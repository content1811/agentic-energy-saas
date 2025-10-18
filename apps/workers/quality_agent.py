"""
Data Quality Agent
Validates meter readings and flags anomalies
"""
import signal
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from uuid import UUID
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from dotenv import load_dotenv
import os
import time
import statistics

load_dotenv()

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/energy_saas")
CHECK_INTERVAL = 30  # seconds
LOOKBACK_MINUTES = 5  # Check last N minutes of data
SPIKE_THRESHOLD = 2.5  # Standard deviations for spike detection
DROP_THRESHOLD = -2.0  # Standard deviations for drop detection

# Database setup
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

# OpenTelemetry tracer
tracer = trace.get_tracer(__name__)

running = True


def signal_handler(sig, frame):
    global running
    print("\n🛑 Shutting down quality agent...")
    running = False


def get_recent_readings(session: Session, minutes: int = LOOKBACK_MINUTES) -> List[Dict]:
    """Fetch recent readings for analysis"""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    
    query = text("""
        SELECT tenant_id, site_id, ts, kw, quality_flag
        FROM meter_readings
        WHERE ts >= :cutoff
        AND (quality_flag IS NULL OR quality_flag = 'ok')
        ORDER BY site_id, ts
    """)
    
    result = session.execute(query, {"cutoff": cutoff})
    return [
        {
            "tenant_id": row[0],
            "site_id": row[1],
            "ts": row[2],
            "kw": row[3],
            "quality_flag": row[4]
        }
        for row in result
    ]


def calculate_baseline(readings: List[Dict], site_id: str) -> Dict:
    """Calculate baseline statistics for a site"""
    site_readings = [r["kw"] for r in readings if r["site_id"] == site_id]
    
    if len(site_readings) < 3:
        return {"mean": None, "stdev": None, "count": len(site_readings)}
    
    mean = statistics.mean(site_readings)
    stdev = statistics.stdev(site_readings) if len(site_readings) > 1 else 0
    
    return {
        "mean": mean,
        "stdev": stdev,
        "count": len(site_readings),
        "min": min(site_readings),
        "max": max(site_readings)
    }


def detect_anomalies(readings: List[Dict]) -> List[Dict]:
    """Detect anomalies in readings"""
    anomalies = []
    
    # Group by site
    sites = set(r["site_id"] for r in readings)
    
    for site_id in sites:
        site_data = [r for r in readings if r["site_id"] == site_id]
        
        if len(site_data) < 3:
            continue
        
        baseline = calculate_baseline(readings, site_id)
        
        if baseline["stdev"] is None or baseline["stdev"] == 0:
            continue
        
        # Check each reading
        for reading in site_data:
            z_score = (reading["kw"] - baseline["mean"]) / baseline["stdev"]
            
            anomaly_type = None
            
            if z_score > SPIKE_THRESHOLD:
                anomaly_type = "spike"
            elif z_score < DROP_THRESHOLD:
                anomaly_type = "drop"
            
            if anomaly_type:
                anomalies.append({
                    "tenant_id": reading["tenant_id"],
                    "site_id": reading["site_id"],
                    "ts": reading["ts"],
                    "kw": reading["kw"],
                    "type": anomaly_type,
                    "z_score": round(z_score, 2),
                    "baseline_mean": round(baseline["mean"], 2)
                })
    
    return anomalies


def update_quality_flags(session: Session, anomalies: List[Dict]):
    """Update quality flags for anomalous readings"""
    if not anomalies:
        return 0
    
    updated = 0
    query = text("""
        UPDATE meter_readings
        SET quality_flag = :flag
        WHERE tenant_id = :tenant_id
        AND site_id = :site_id
        AND ts = :ts
    """)
    
    for anomaly in anomalies:
        session.execute(query, {
            "flag": anomaly['type'],
            "tenant_id": anomaly['tenant_id'],
            "site_id": anomaly['site_id'],
            "ts": anomaly['ts']
        })
        updated += 1
    
    session.commit()
    return updated


def run_quality_check(session: Session):
    """Run a quality check cycle"""
    with tracer.start_as_current_span("quality_check") as span:
        try:
            # Fetch recent readings
            readings = get_recent_readings(session, LOOKBACK_MINUTES)
            
            if not readings:
                print(f"⏸️  No new readings to check")
                span.set_attribute("readings_count", 0)
                return
            
            span.set_attribute("readings_count", len(readings))
            
            # Detect anomalies
            anomalies = detect_anomalies(readings)
            
            if anomalies:
                # Update flags
                updated = update_quality_flags(session, anomalies)
                
                print(f"⚠️  Found {len(anomalies)} anomalies, updated {updated} flags:")
                for a in anomalies:
                    print(f"   {a['site_id']} | {a['ts'].strftime('%H:%M:%S')} | "
                          f"{a['kw']} kW | {a['type'].upper()} | z={a['z_score']}")
                
                span.set_attribute("anomalies_found", len(anomalies))
            else:
                print(f"✅ Checked {len(readings)} readings - all normal")
                span.set_attribute("anomalies_found", 0)
            
            span.set_status(Status(StatusCode.OK))
            
        except Exception as e:
            print(f"❌ Error during quality check: {e}")
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)


def main():
    global running
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    session = SessionLocal()
    
    try:
        print("🚀 Starting Data Quality Agent")
        print(f"🔍 Check interval: {CHECK_INTERVAL}s")
        print(f"📊 Lookback window: {LOOKBACK_MINUTES} minutes")
        print(f"⚡ Spike threshold: {SPIKE_THRESHOLD} σ")
        print(f"📉 Drop threshold: {DROP_THRESHOLD} σ\n")
        
        while running:
            run_quality_check(session)
            print()
            
            # Wait for next check
            for _ in range(CHECK_INTERVAL):
                if not running:
                    break
                time.sleep(1)
    
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
        print("👋 Quality agent stopped")


if __name__ == "__main__":
    main()