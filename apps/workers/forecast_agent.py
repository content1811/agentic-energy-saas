"""
Forecast Agent
Generates next-day energy consumption predictions using Prophet
"""
import signal
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from uuid import UUID
import pandas as pd
from prophet import Prophet
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from dotenv import load_dotenv
import os
import time

load_dotenv()

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/energy_saas")
FORECAST_INTERVAL = 300  # 5 minutes (for testing; use 3600 for hourly in prod)
TRAINING_DAYS = 7  # Use last 7 days for training
FORECAST_HOURS = 24  # Predict next 24 hours
FORECAST_PERIODS = 96  # 24 hours * 4 (15-min intervals)
MODEL_VERSION = "prophet-v1"

# Database setup
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

# OpenTelemetry tracer
tracer = trace.get_tracer(__name__)

running = True


def signal_handler(sig, frame):
    global running
    print("\n🛑 Shutting down forecast agent...")
    running = False


def get_training_data(session: Session, site_id: str, days: int) -> pd.DataFrame:
    """Fetch historical data for training"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    query = text("""
        SELECT ts, kw
        FROM meter_readings
        WHERE site_id = :site_id
        AND ts >= :cutoff
        AND (quality_flag = 'ok' OR quality_flag IS NULL)
        ORDER BY ts
    """)
    
    result = session.execute(query, {"site_id": site_id, "cutoff": cutoff})
    
    # Remove timezone for Prophet compatibility
    data = [{"ds": row[0].replace(tzinfo=None), "y": row[1]} for row in result]
    
    if not data:
        return pd.DataFrame()
    
    return pd.DataFrame(data)


def train_and_forecast(df: pd.DataFrame, periods: int) -> pd.DataFrame:
    """Train Prophet model and generate forecast"""
    if len(df) < 10:
        raise ValueError(f"Insufficient data: {len(df)} points (need at least 10)")
    
    # Initialize Prophet with simple settings
    model = Prophet(
        daily_seasonality=True,
        weekly_seasonality=True,
        yearly_seasonality=False,
        interval_width=0.80  # 80% confidence interval
    )
    
    # Suppress Prophet logging
    import logging
    logging.getLogger('prophet').setLevel(logging.ERROR)
    
    # Fit model
    model.fit(df)
    
    # Create future dataframe (15-min intervals)
    future = model.make_future_dataframe(periods=periods, freq='15min')
    
    # Generate forecast
    forecast = model.predict(future)
    
    return forecast


def save_forecasts(session: Session, tenant_id: UUID, site_id: str, forecast_df: pd.DataFrame):
    """Save forecast results to database"""
    now = datetime.now(timezone.utc)
    now_naive = pd.Timestamp(now.replace(tzinfo=None))
    
    # Get only future predictions (not historical fit)
    future_mask = forecast_df['ds'] > now_naive
    future_forecast = forecast_df[future_mask].head(FORECAST_PERIODS)
    
    if len(future_forecast) == 0:
        return 0
    
    # Prepare batch insert
    records = []
    for _, row in future_forecast.iterrows():
        # Convert pandas Timestamp to datetime and add timezone
        target_ts = row['ds'].to_pydatetime().replace(tzinfo=timezone.utc)
        
        records.append({
            "tenant_id": tenant_id,
            "site_id": site_id,
            "forecast_ts": now,
            "target_ts": target_ts,
            "kw_predicted": max(0, row['yhat']),
            "confidence_lower": max(0, row['yhat_lower']),
            "confidence_upper": max(0, row['yhat_upper']),
            "model_version": MODEL_VERSION
        })
    
    # Delete existing forecasts for this site
    delete_query = text("""
        DELETE FROM forecasts
        WHERE tenant_id = :tenant_id
        AND site_id = :site_id
        AND forecast_ts < :now
    """)
    session.execute(delete_query, {"tenant_id": tenant_id, "site_id": site_id, "now": now})
    
    # Insert new forecasts
    insert_query = text("""
        INSERT INTO forecasts (tenant_id, site_id, forecast_ts, target_ts, 
                              kw_predicted, confidence_lower, confidence_upper, model_version)
        VALUES (:tenant_id, :site_id, :forecast_ts, :target_ts,
                :kw_predicted, :confidence_lower, :confidence_upper, :model_version)
    """)
    
    for record in records:
        session.execute(insert_query, record)
    
    session.commit()
    return len(records)


def get_sites(session: Session) -> List[Dict]:
    """Get distinct sites with recent data"""
    query = text("""
        SELECT DISTINCT tenant_id, site_id
        FROM meter_readings
        WHERE ts >= NOW() - INTERVAL '1 day'
    """)
    
    result = session.execute(query)
    return [{"tenant_id": row[0], "site_id": row[1]} for row in result]


def run_forecast_cycle(session: Session):
    """Run forecast for all active sites"""
    with tracer.start_as_current_span("forecast_cycle") as span:
        try:
            sites = get_sites(session)
            
            if not sites:
                print("⏸️  No active sites found")
                return
            
            span.set_attribute("sites_count", len(sites))
            total_forecasts = 0
            
            for site in sites:
                try:
                    site_id = site["site_id"]
                    tenant_id = site["tenant_id"]
                    
                    print(f"🔮 Forecasting for {site_id}...")
                    
                    # Get training data
                    df = get_training_data(session, site_id, TRAINING_DAYS)
                    
                    if df.empty:
                        print(f"   ⚠️  No training data for {site_id}")
                        continue
                    
                    print(f"   📊 Training on {len(df)} data points")
                    
                    # Train and forecast
                    forecast_df = train_and_forecast(df, FORECAST_PERIODS)
                    
                    # Save to database
                    saved = save_forecasts(session, tenant_id, site_id, forecast_df)
                    
                    print(f"   ✅ Generated {saved} forecast points\n")
                    total_forecasts += saved
                    
                except Exception as e:
                    print(f"   ❌ Error forecasting {site.get('site_id', 'unknown')}: {e}\n")
                    continue
            
            print(f"📈 Forecast cycle complete: {total_forecasts} predictions for {len(sites)} sites")
            span.set_attribute("total_forecasts", total_forecasts)
            span.set_status(Status(StatusCode.OK))
            
        except Exception as e:
            print(f"❌ Error during forecast cycle: {e}")
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)


def main():
    global running
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    session = SessionLocal()
    
    try:
        print("🚀 Starting Forecast Agent")
        print(f"🔮 Forecast interval: {FORECAST_INTERVAL}s")
        print(f"📅 Training window: {TRAINING_DAYS} days")
        print(f"⏰ Forecast horizon: {FORECAST_HOURS} hours ({FORECAST_PERIODS} intervals)")
        print(f"🤖 Model: {MODEL_VERSION}\n")
        
        # Run initial forecast
        run_forecast_cycle(session)
        
        # Schedule periodic forecasts
        while running:
            print(f"\n⏳ Next forecast in {FORECAST_INTERVAL}s...\n")
            
            for _ in range(FORECAST_INTERVAL):
                if not running:
                    break
                time.sleep(1)
            
            if running:
                run_forecast_cycle(session)
    
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
        print("👋 Forecast agent stopped")


if __name__ == "__main__":
    main()