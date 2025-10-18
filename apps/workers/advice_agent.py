"""
Advice Agent
Generates actionable energy-saving recommendations using rules + LLM
"""
import signal
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from uuid import UUID
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from dotenv import load_dotenv
import os
import time
import requests

load_dotenv()

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/energy_saas")
ADVICE_INTERVAL = 300  # 5 minutes
USE_OPENROUTER = True  # Switch to OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = "deepseek/deepseek-chat-v3.1:free"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = "llama3.2:latest"
PRICE_PER_KWH = 0.12  # USD
CO2_PER_KWH = 0.5  # kg CO2
PEAK_THRESHOLD = 1.3

# Database setup
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

# OpenTelemetry tracer
tracer = trace.get_tracer(__name__)

running = True


def signal_handler(sig, frame):
    global running
    print("\n🛑 Shutting down advice agent...")
    running = False


def get_current_usage(session: Session, site_id: str) -> Dict:
    """Get recent average usage"""
    query = text("""
        SELECT AVG(kw) as avg_kw, MAX(kw) as max_kw, MIN(kw) as min_kw, COUNT(*) as count
        FROM meter_readings
        WHERE site_id = :site_id AND ts >= NOW() - INTERVAL '1 hour'
    """)
    
    result = session.execute(query, {"site_id": site_id}).fetchone()
    if not result or result[3] == 0:
        return None
    
    return {"avg_kw": float(result[0]), "max_kw": float(result[1]), "min_kw": float(result[2])}


def get_forecast_peak(session: Session, site_id: str) -> Dict:
    """Get predicted peak"""
    query = text("""
        SELECT target_ts, kw_predicted
        FROM forecasts
        WHERE site_id = :site_id AND target_ts BETWEEN NOW() AND NOW() + INTERVAL '6 hours'
        ORDER BY kw_predicted DESC LIMIT 1
    """)
    
    result = session.execute(query, {"site_id": site_id}).fetchone()
    if not result:
        return None
    
    return {"peak_time": result[0], "peak_kw": float(result[1])}


def call_llm(prompt: str, timeout: int = 60) -> str:
    """Call LLM (OpenRouter or Ollama)"""
    try:
        if USE_OPENROUTER:
            # OpenRouter API call with required headers for free models
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/content1811/agentic-energy-saas",  # Required for free models
                    "X-Title": "Energy SaaS Advice Agent"  # Required for free models
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 150,
                    "temperature": 0.7
                },
                timeout=timeout
            )
            
            if response.status_code == 200:
                text = response.json()["choices"][0]["message"]["content"].strip()
                # Clean up common LLM artifacts
                text = text.replace("Here's a tip:", "").replace("Here is a tip:", "")
                text = text.replace("Suggestion:", "").replace("Recommendation:", "")
                text = text.strip()
                return text if text else None
            else:
                print(f"   ⚠️  OpenRouter error: {response.status_code} - {response.text[:100]}")
                return None
        else:
            # Ollama API call
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": LLM_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 150
                    }
                },
                timeout=timeout
            )
            
            if response.status_code == 200:
                text = response.json().get("response", "").strip()
                text = text.replace("Here's a tip:", "").replace("Here is a tip:", "")
                text = text.replace("Suggestion:", "").replace("Recommendation:", "")
                text = text.strip()
                return text if text else None
            return None
            
    except requests.exceptions.Timeout:
        print(f"   ⚠️  LLM timeout")
        return None
    except Exception as e:
        print(f"   ⚠️  LLM call failed: {e}")
        return None


def generate_advice_with_llm(site_id: str, tenant_id: UUID, current: Dict, forecast: Dict) -> List[Dict]:
    """Generate advice using rules + LLM"""
    advice_list = []
    now = datetime.now(timezone.utc)
    
    # Rule 1: Peak prediction
    if forecast and forecast["peak_kw"] > current["avg_kw"] * PEAK_THRESHOLD:
        peak_time = forecast["peak_time"]
        excess_kw = forecast["peak_kw"] - current["avg_kw"]
        savings_kwh = excess_kw * 0.25
        peak_increase_pct = ((forecast['peak_kw']/current['avg_kw']-1)*100)
        
        prompt = f"""You are an energy management consultant for commercial facilities.

CONTEXT:
- Site: {site_id}
- Current average load: {current['avg_kw']:.1f} kW
- Predicted peak: {forecast['peak_kw']:.1f} kW at {peak_time.strftime('%I:%M %p')}
- Increase: {peak_increase_pct:.0f}% above current average
- Potential savings: {savings_kwh:.1f} kWh if reduced by 25%

TASK: Write ONE specific, actionable recommendation (2 sentences maximum) to avoid this peak.

REQUIREMENTS:
- Be direct and specific (mention exact time, equipment, or actions)
- Focus on practical steps (pre-cooling, load shifting, equipment scheduling)
- Do NOT include greetings, explanations, or multiple options
- Do NOT start with "Here's a tip" or "I recommend"
- Start directly with the action

OUTPUT (example format): "Pre-cool the facility by 2°F between 12:00-2:00 PM before the predicted peak. This shifts 15-20% of cooling load to off-peak hours."""

        llm_text = call_llm(prompt)
        
        advice_list.append({
            "tenant_id": tenant_id,
            "site_id": site_id,
            "ts": now,
            "type": "peak_management",
            "title": f"Peak Alert: {peak_time.strftime('%I:%M %p')}",
            "text": llm_text if llm_text else f"Pre-cool facility 1-2 hours before {peak_time.strftime('%I:%M %p')} to reduce peak demand by {excess_kw:.1f} kW.",
            "savings_est_usd": round(savings_kwh * PRICE_PER_KWH, 2),
            "co2_saved_kg": round(savings_kwh * CO2_PER_KWH, 2),
            "confidence": 0.75,
            "status": "pending"
        })
    
    # Rule 2: Baseline efficiency
    if current and current["avg_kw"] > 40:
        savings_kwh = current["avg_kw"] * 0.15 * 24
        baseline_cost_day = current["avg_kw"] * 24 * PRICE_PER_KWH
        
        prompt = f"""You are an energy management consultant for commercial facilities.

CONTEXT:
- Site: {site_id}
- Current baseline: {current['avg_kw']:.1f} kW average
- Daily energy cost: ${baseline_cost_day:.2f}
- Target reduction: 15% (saves ${savings_kwh * PRICE_PER_KWH:.2f}/day)

TASK: Write ONE specific action to reduce baseline consumption (2 sentences maximum).

REQUIREMENTS:
- Target specific systems (HVAC, lighting, equipment)
- Give concrete actions with numbers/times
- Do NOT include pleasantries or multiple suggestions
- Do NOT start with "Consider" or "You should"
- Start directly with the action verb

OUTPUT (example format): "Adjust HVAC setpoints to 72°F during occupied hours and 78°F when unoccupied. Implement occupancy sensors in conference rooms and storage areas to auto-shutoff lighting."""

        llm_text = call_llm(prompt)
        
        advice_list.append({
            "tenant_id": tenant_id,
            "site_id": site_id,
            "ts": now,
            "type": "efficiency",
            "title": "Baseline Optimization",
            "text": llm_text if llm_text else f"Optimize HVAC schedules and review lighting timers. Target 15% reduction in baseline load of {current['avg_kw']:.1f} kW.",
            "savings_est_usd": round(savings_kwh * PRICE_PER_KWH, 2),
            "co2_saved_kg": round(savings_kwh * CO2_PER_KWH, 2),
            "confidence": 0.65,
            "status": "pending"
        })
    
    # Rule 3: Off-hours usage check
    if current and current["min_kw"] > current["avg_kw"] * 0.7:
        savings_kwh = (current["min_kw"] - current["avg_kw"] * 0.3) * 24
        
        prompt = f"""You are an energy management consultant for commercial facilities.

CONTEXT:
- Site: {site_id}
- Minimum load: {current['min_kw']:.1f} kW
- Average load: {current['avg_kw']:.1f} kW
- Issue: Minimum usage is {(current['min_kw']/current['avg_kw']*100):.0f}% of average (should be ~30-40%)
- This indicates high off-hours consumption

TASK: Write ONE action to reduce off-hours/overnight energy waste (2 sentences maximum).

REQUIREMENTS:
- Focus on equipment that shouldn't run 24/7
- Be specific about scheduling or automation
- Do NOT be generic or vague
- Start with action verb

OUTPUT (example format): "Schedule non-essential equipment to shut down after 6 PM and restart at 6 AM on weekdays. Audit plug loads to identify always-on devices that can be placed on timers or smart outlets."""

        llm_text = call_llm(prompt)
        
        if llm_text:  # Only add if LLM provides good output
            advice_list.append({
                "tenant_id": tenant_id,
                "site_id": site_id,
                "ts": now,
                "type": "off_hours",
                "title": "Off-Hours Usage Reduction",
                "text": llm_text,
                "savings_est_usd": round(savings_kwh * PRICE_PER_KWH, 2),
                "co2_saved_kg": round(savings_kwh * CO2_PER_KWH, 2),
                "confidence": 0.60,
                "status": "pending"
            })
    
    return advice_list[:3]


def save_advice(session: Session, advice_list: List[Dict]):
    """Save advice to database"""
    if not advice_list:
        return 0
    
    # Delete old pending advice
    delete_query = text("""
        DELETE FROM advice
        WHERE status = 'pending' AND ts < NOW() - INTERVAL '1 day'
    """)
    session.execute(delete_query)
    
    insert_query = text("""
        INSERT INTO advice (tenant_id, site_id, ts, type, title, text, 
                           savings_est_usd, co2_saved_kg, confidence, status)
        VALUES (:tenant_id, :site_id, :ts, :type, :title, :text,
                :savings_est_usd, :co2_saved_kg, :confidence, :status)
    """)
    
    for advice in advice_list:
        session.execute(insert_query, advice)
    
    session.commit()
    return len(advice_list)


def get_sites(session: Session) -> List[Dict]:
    """Get active sites"""
    query = text("""
        SELECT DISTINCT tenant_id, site_id
        FROM meter_readings
        WHERE ts >= NOW() - INTERVAL '1 hour'
    """)
    
    result = session.execute(query)
    return [{"tenant_id": row[0], "site_id": row[1]} for row in result]


def run_advice_cycle(session: Session):
    """Generate advice for all sites"""
    with tracer.start_as_current_span("advice_cycle") as span:
        try:
            sites = get_sites(session)
            
            if not sites:
                print("⏸️  No active sites")
                return
            
            total_advice = 0
            
            for site in sites:
                try:
                    site_id = site["site_id"]
                    tenant_id = site["tenant_id"]
                    
                    print(f"💡 Generating advice for {site_id}...")
                    
                    current = get_current_usage(session, site_id)
                    forecast = get_forecast_peak(session, site_id)
                    
                    if not current:
                        print(f"   ⚠️  No recent data")
                        continue
                    
                    advice_list = generate_advice_with_llm(site_id, tenant_id, current, forecast)
                    
                    if advice_list:
                        saved = save_advice(session, advice_list)
                        print(f"   ✅ Generated {saved} recommendations")
                        
                        for advice in advice_list:
                            print(f"      • {advice['title']}: ${advice['savings_est_usd']:.2f}/day")
                        
                        total_advice += saved
                    
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    continue
            
            print(f"\n💡 Advice cycle complete: {total_advice} recommendations")
            span.set_status(Status(StatusCode.OK))
            
        except Exception as e:
            print(f"❌ Error: {e}")
            span.set_status(Status(StatusCode.ERROR, str(e)))


def main():
    global running
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    session = SessionLocal()
    
    try:
        print("🚀 Starting Advice Agent")
        print(f"💡 Interval: {ADVICE_INTERVAL}s")
        if USE_OPENROUTER:
            print(f"🤖 LLM: OpenRouter ({OPENROUTER_MODEL})")
        else:
            print(f"🤖 LLM: Ollama ({LLM_MODEL})")
        print()
        
        run_advice_cycle(session)
        
        while running:
            print(f"\n⏳ Next cycle in {ADVICE_INTERVAL}s...\n")
            
            for _ in range(ADVICE_INTERVAL):
                if not running:
                    break
                time.sleep(1)
            
            if running:
                run_advice_cycle(session)
    
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
        print("👋 Advice agent stopped")


if __name__ == "__main__":
    main()