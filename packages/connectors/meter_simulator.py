"""
MQTT Meter Data Simulator
Generates realistic energy consumption data for 2 sites
"""
import json
import time
import signal
import sys
from datetime import datetime, timezone
from math import sin, pi
from random import random, gauss
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os

load_dotenv()

# Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
TENANT_ID = os.getenv("TENANT_ID", "123e4567-e89b-12d3-a456-426614174000")
PUBLISH_INTERVAL = 15  # seconds
SITES = ["site-01", "site-02"]

# Power consumption parameters (kW)
BASE_LOAD = 30.0  # Minimum baseline
PEAK_AMPLITUDE = 25.0  # Max variation from baseline
WEEKEND_FACTOR = 0.6  # 60% of weekday consumption
SPIKE_PROBABILITY = 0.05  # 5% chance of equipment spike
SPIKE_MAGNITUDE = 15.0  # kW spike size

running = True


def signal_handler(sig, frame):
    global running
    print("\n🛑 Shutting down simulator...")
    running = False


def is_weekend(dt):
    return dt.weekday() >= 5  # Saturday=5, Sunday=6


def calculate_kw(dt):
    """Generate realistic power consumption based on time of day"""
    hour = dt.hour + dt.minute / 60.0
    
    # Base sinusoidal pattern: peak at 2pm (14:00), low at 2am
    time_factor = sin(pi * (hour - 2) / 12)
    time_variation = PEAK_AMPLITUDE * max(0, time_factor)
    
    # Weekend reduction
    day_factor = WEEKEND_FACTOR if is_weekend(dt) else 1.0
    
    # Base consumption
    kw = BASE_LOAD + (time_variation * day_factor)
    
    # Add gaussian noise (±2 kW)
    kw += gauss(0, 2)
    
    # Random equipment spikes
    if random() < SPIKE_PROBABILITY:
        kw += SPIKE_MAGNITUDE * random()
    
    return max(15.0, kw)  # Never below 15 kW


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
    else:
        print(f"❌ Connection failed with code {rc}")


def on_publish(client, userdata, mid):
    pass  # Silent success


def main():
    global running
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_publish = on_publish
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        
        print(f"🚀 Starting meter simulator for {len(SITES)} sites")
        print(f"📡 Publishing every {PUBLISH_INTERVAL}s")
        print(f"🏢 Tenant ID: {TENANT_ID}")
        print(f"📍 Sites: {', '.join(SITES)}\n")
        
        while running:
            now = datetime.now(timezone.utc)
            
            for site_id in SITES:
                # Calculate power with slight variation per site
                kw = calculate_kw(now)
                
                # Site-02 has ~10% higher baseline
                if site_id == "site-02":
                    kw *= 1.1
                
                # Create message
                message = {
                    "tenant_id": TENANT_ID,
                    "site_id": site_id,
                    "ts": now.isoformat(),
                    "kw": round(kw, 2),
                    "source": "simulator"
                }
                
                # Publish to MQTT
                topic = f"tenant/{TENANT_ID}/meter/{site_id}"
                result = client.publish(topic, json.dumps(message), qos=1)
                
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    day_type = "🏖️ Weekend" if is_weekend(now) else "💼 Weekday"
                    print(f"✉️  {now.strftime('%H:%M:%S')} | {site_id} | {kw:5.1f} kW | {day_type}")
                else:
                    print(f"⚠️  Failed to publish for {site_id}")
            
            print()  # Blank line between batches
            time.sleep(PUBLISH_INTERVAL)
    
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        print("👋 Simulator stopped")


if __name__ == "__main__":
    main()