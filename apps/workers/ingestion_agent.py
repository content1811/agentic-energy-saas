import json
import signal
from datetime import datetime
from typing import Dict, List
from uuid import UUID
import paho.mqtt.client as mqtt
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from dotenv import load_dotenv
import os
import time
import threading

load_dotenv()

# Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/energy_saas")
BATCH_SIZE = 50
BATCH_TIMEOUT = 5  # seconds

# Database setup
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
metadata = MetaData()
meter_readings_table = Table('meter_readings', metadata, autoload_with=engine)

# OpenTelemetry tracer
tracer = trace.get_tracer(__name__)

# Global state
running = True
message_buffer: List[Dict] = []
last_flush_time = time.time()
flush_lock = threading.Lock()


def signal_handler(sig, frame):
    global running
    print("\n🛑 Shutting down ingestion agent...")
    running = False


def parse_message(payload: str) -> Dict:
    """Parse and validate MQTT message"""
    data = json.loads(payload)
    
    # Validate required fields
    required = ["tenant_id", "site_id", "ts", "kw", "source"]
    for field in required:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    # Parse timestamp
    ts = datetime.fromisoformat(data["ts"].replace("Z", "+00:00"))
    
    # Convert tenant_id string to UUID
    tenant_id = UUID(data["tenant_id"]) if isinstance(data["tenant_id"], str) else data["tenant_id"]
    
    return {
        "tenant_id": tenant_id,
        "site_id": data["site_id"],
        "ts": ts,
        "kw": float(data["kw"]),
        "kwh": None,
        "cost_est": None,
        "source": data["source"],
        "quality_flag": "ok"
    }


def flush_buffer(session):
    """Write buffered readings to database"""
    global message_buffer, last_flush_time
    
    with flush_lock:
        if not message_buffer:
            return
        
        with tracer.start_as_current_span("flush_readings") as span:
            try:
                span.set_attribute("batch_size", len(message_buffer))
                
                # Upsert with conflict handling (deduplication)
                stmt = insert(meter_readings_table).values(message_buffer)
                
                # On conflict, update the reading (handles duplicates)
                stmt = stmt.on_conflict_do_update(
                    constraint="meter_readings_pkey",
                    set_={
                        "kw": stmt.excluded.kw,
                        "quality_flag": stmt.excluded.quality_flag,
                        "created_at": stmt.excluded.created_at
                    }
                )
                
                session.execute(stmt)
                session.commit()
                
                print(f"✅ Flushed {len(message_buffer)} readings to database")
                span.set_status(Status(StatusCode.OK))
                
                # Clear buffer
                message_buffer = []
                last_flush_time = time.time()
                
            except Exception as e:
                session.rollback()
                print(f"❌ Error flushing to database: {e}")
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        
        # Subscribe to all tenant meter topics
        topic = "tenant/+/meter/+"
        client.subscribe(topic, qos=1)
        print(f"📡 Subscribed to: {topic}")
    else:
        print(f"❌ Connection failed with code {rc}")


def on_message(client, userdata, msg):
    """Handle incoming MQTT messages"""
    global message_buffer
    
    with tracer.start_as_current_span("process_message") as span:
        try:
            # Parse message
            reading = parse_message(msg.payload.decode())
            
            span.set_attributes({
                "tenant_id": str(reading["tenant_id"]),
                "site_id": reading["site_id"],
                "kw": reading["kw"]
            })
            
            # Add to buffer with lock
            with flush_lock:
                message_buffer.append(reading)
                buffer_size = len(message_buffer)
            
            print(f"📥 Received: {reading['site_id']} | {reading['kw']} kW | Buffer: {buffer_size}")
            
            # Flush if buffer is full
            session = userdata["session"]
            if buffer_size >= BATCH_SIZE:
                flush_buffer(session)
            
            span.set_status(Status(StatusCode.OK))
            
        except json.JSONDecodeError as e:
            print(f"⚠️  Invalid JSON: {e}")
            span.set_status(Status(StatusCode.ERROR, "Invalid JSON"))
        except ValueError as e:
            print(f"⚠️  Validation error: {e}")
            span.set_status(Status(StatusCode.ERROR, str(e)))
        except Exception as e:
            print(f"❌ Error processing message: {e}")
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)


def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"⚠️  Unexpected disconnect. Reconnecting...")


def main():
    global running
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create database session
    session = SessionLocal()
    
    # Initialize MQTT client
    client = mqtt.Client()
    client.user_data_set({"session": session})
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    try:
        print("🚀 Starting Ingestion Agent")
        print(f"📊 Batch size: {BATCH_SIZE}")
        print(f"⏱️  Batch timeout: {BATCH_TIMEOUT}s")
        print(f"💾 Database: {DATABASE_URL.split('@')[1]}\n")
        
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        
        # Keep running and periodically flush on timeout
        while running:
            time.sleep(1)
            
            # Check for timeout-based flush
            current_time = time.time()
            if message_buffer and (current_time - last_flush_time) >= BATCH_TIMEOUT:
                flush_buffer(session)
        
        # Final flush before shutdown
        if message_buffer:
            print("🔄 Final flush...")
            flush_buffer(session)
    
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.loop_stop()
        client.disconnect()
        session.close()
        print("👋 Ingestion agent stopped")


if __name__ == "__main__":
    main()