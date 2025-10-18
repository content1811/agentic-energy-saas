# Agentic Energy SaaS - Setup Guide

> AI-powered energy monitoring and optimization platform with real-time insights, forecasting, and actionable recommendations.

## 🎥 Video Demo

[![Agentic Energy SaaS Demo](https://img.youtube.com/vi/5Ugsu2MSINI/maxresdefault.jpg)](https://youtu.be/5Ugsu2MSINI)

**Watch the full walkthrough** ↑ *Click to see the platform in action!*

---

## 🎯 What You'll Build

A complete SaaS featuring:
- **Real-time monitoring** via MQTT simulator (2 sites)
- **Data ingestion** with batching and deduplication
- **Quality checks** with anomaly detection
- **AI forecasting** using Prophet (24-hour predictions)
- **Smart recommendations** via LLM (OpenRouter/DeepSeek)
- **Live dashboard** with charts and metrics
- **Email digests** with daily summaries

---

## 📋 Prerequisites

- **Node.js** 18+ and **pnpm**
- **Python** 3.11+
- **Docker** & Docker Compose
- **Poetry** (Python package manager)
- **Git**

---

## 🚀 Quick Start (5 Steps)

### Step 1: Clone & Install

```bash
# Clone repository
git clone <your-repo-url>
cd agentic-energy-saas

# Install Python dependencies
poetry install

# Install Node dependencies
cd apps/web
pnpm install
cd ../..
```

---

### Step 2: Configure Environment

**Create `.env` in project root:**

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/energy_saas

# Redis
REDIS_URL=redis://localhost:6379

# MQTT
MQTT_BROKER=localhost
MQTT_PORT=1883

# NATS
NATS_URL=nats://localhost:4222

# Qdrant
QDRANT_URL=http://localhost:6333

# LLM (OpenRouter with DeepSeek - Free)
OPENROUTER_API_KEY=your_key_here

# Email (Mailpit for testing)
SMTP_HOST=localhost
SMTP_PORT=1025
FROM_EMAIL=noreply@energy-saas.local

# Tenant (Demo)
TENANT_ID=123e4567-e89b-12d3-a456-426614174000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Get your OpenRouter API key:**
1. Go to https://openrouter.ai
2. Sign up (free)
3. Create API key
4. Add to `.env` as `OPENROUTER_API_KEY`

---

### Step 3: Start Infrastructure

```bash
# Start all Docker services
docker-compose -f infra/docker/docker-compose.dev.yml up -d

# Wait 10 seconds for services to initialize
sleep 10

# Run database migrations
cd apps/api
poetry run alembic upgrade head
cd ../..

# Verify services are healthy
docker ps
```

**Expected services running:**
- PostgreSQL + TimescaleDB (port 5432)
- Redis (port 6379)
- MQTT/Mosquitto (port 1883)
- NATS (port 4222)
- Qdrant (port 6333)
- Mailpit (ports 1025, 8025)

---

### Step 4: Start Backend Agents

**Open 6 separate terminals:**

**Terminal 1 - MQTT Simulator:**
```bash
cd packages/connectors
poetry run python meter_simulator.py
```
*Publishes fake meter data every 15 seconds for 2 sites*

**Terminal 2 - Ingestion Agent:**
```bash
cd apps/workers
poetry run python ingestion_agent.py
```
*Consumes MQTT data and writes to database*

**Terminal 3 - Quality Agent:**
```bash
cd apps/workers
poetry run python quality_agent.py
```
*Detects anomalies and flags suspicious readings*

**Terminal 4 - Forecast Agent:**
```bash
cd apps/workers
poetry run python forecast_agent.py
```
*Generates 24-hour energy predictions using Prophet*

**Terminal 5 - Advice Agent:**
```bash
cd apps/workers
poetry run python advice_agent.py
```
*Creates AI-powered savings recommendations*

**Terminal 6 - Email Agent (Optional):**
```bash
cd apps/workers
poetry run python email_agent.py
```
*Sends daily email digests*

---

### Step 5: Start Frontend

**Terminal 7 - API Server:**
```bash
cd apps/api
poetry run python main.py
```
*FastAPI backend on port 8000*

**Terminal 8 - Next.js Web:**
```bash
cd apps/web
pnpm dev
```
*Frontend on port 3000*

---

## 🌐 Access

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | http://localhost:3000 | Main web interface |
| **API Docs** | http://localhost:8000/docs | Swagger/OpenAPI |
| **Mailpit UI** | http://localhost:8025 | Email testing |
| **NATS Monitor** | http://localhost:8222 | Message queue stats |
| **Qdrant Dashboard** | http://localhost:6333/dashboard | Vector store UI |

---

## 📊 What You'll See

### Dashboard (localhost:3000)
- **Live Stats Cards:**
  - Current usage (kW) with trend indicator
  - Estimated daily cost
  - Total savings potential
  - CO₂ impact

- **Usage Chart:**
  - Real-time line graph
  - Last 100 readings (rolling window)
  - Updates every 15 seconds

- **AI Recommendations:**
  - Peak management tips
  - Baseline optimization
  - Off-hours reduction
  - Savings & CO₂ quantified

### Email Digests (localhost:8025)
- Beautiful HTML emails
- 24-hour summary statistics
- Top 3 recommendations
- Peak forecast alerts

---

## 🔍 Verify Everything Works

### 1. Check Data Flow

```bash
# Check meter readings in database
docker exec -it energy-postgres psql -U postgres -d energy_saas -c \
  "SELECT site_id, ts, kw FROM meter_readings ORDER BY ts DESC LIMIT 5;"

# Check forecasts
docker exec -it energy-postgres psql -U postgres -d energy_saas -c \
  "SELECT site_id, target_ts, kw_predicted FROM forecasts ORDER BY target_ts LIMIT 5;"

# Check advice
docker exec -it energy-postgres psql -U postgres -d energy_saas -c \
  "SELECT site_id, title, savings_est_usd FROM advice ORDER BY ts DESC LIMIT 3;"
```

### 2. Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Get latest reading
curl "http://localhost:8000/api/v1/readings/latest?tenant_id=123e4567-e89b-12d3-a456-426614174000&site_id=site-01"

# Get advice
curl "http://localhost:8000/api/v1/advice/?tenant_id=123e4567-e89b-12d3-a456-426614174000&site_id=site-01&limit=3"
```

### 3. Monitor Agent Logs

Each terminal should show activity:
- **Simulator:** Publishing messages every 15s
- **Ingestion:** Flushing batches to database
- **Quality:** Checking for anomalies
- **Forecast:** Generating predictions every 5 min
- **Advice:** Creating recommendations every 5 min
- **Email:** Sending digests (default: daily)

---

## 🛠️ Troubleshooting

### Services won't start
```bash
# Check what's using ports
lsof -i :5432  # PostgreSQL
lsof -i :1883  # MQTT
lsof -i :8000  # API
lsof -i :3000  # Web

# Restart Docker services
docker-compose -f infra/docker/docker-compose.dev.yml down
docker-compose -f infra/docker/docker-compose.dev.yml up -d
```

### Database issues
```bash
# Reset database
docker-compose -f infra/docker/docker-compose.dev.yml down -v
docker-compose -f infra/docker/docker-compose.dev.yml up -d
sleep 10
cd apps/api && poetry run alembic upgrade head
```

### LLM timeouts
```bash
# Check OpenRouter API key is set
echo $OPENROUTER_API_KEY

# Or switch to fallback mode (rule-based only)
# In advice_agent.py: USE_OPENROUTER = False
```

### No data in dashboard
```bash
# Verify all agents are running
ps aux | grep python

# Check API is accessible
curl http://localhost:8000/health

# Check database has data
docker exec -it energy-postgres psql -U postgres -d energy_saas -c \
  "SELECT COUNT(*) FROM meter_readings;"
```

---

## 📁 Project Structure

```
agentic-energy-saas/
├── apps/
│   ├── api/                 # FastAPI backend
│   │   ├── main.py          # API server
│   │   ├── models/          # SQLAlchemy models
│   │   ├── routers/         # API endpoints
│   │   └── migrations/      # Alembic migrations
│   ├── web/                 # Next.js frontend
│   │   └── src/
│   │       ├── app/         # Pages
│   │       ├── components/  # React components
│   │       └── lib/         # Utilities
│   └── workers/             # Background agents
│       ├── ingestion_agent.py
│       ├── quality_agent.py
│       ├── forecast_agent.py
│       ├── advice_agent.py
│       └── email_agent.py
├── packages/
│   └── connectors/
│       └── meter_simulator.py  # MQTT data generator
├── infra/
│   └── docker/
│       ├── docker-compose.dev.yml
│       └── init-timescale.sql
└── .env
```

---

## 🎛️ Configuration Options

### Simulator Settings
**File:** `packages/connectors/meter_simulator.py`
```python
PUBLISH_INTERVAL = 15  # seconds between readings
SITES = ["site-01", "site-02"]  # add more sites
BASE_LOAD = 30.0  # minimum kW
PEAK_AMPLITUDE = 25.0  # max variation
```

### Forecast Settings
**File:** `apps/workers/forecast_agent.py`
```python
FORECAST_INTERVAL = 300  # run every 5 minutes
TRAINING_DAYS = 7  # use last 7 days
FORECAST_HOURS = 24  # predict next 24 hours
```

### Advice Settings
**File:** `apps/workers/advice_agent.py`
```python
ADVICE_INTERVAL = 300  # run every 5 minutes
USE_OPENROUTER = True  # toggle LLM on/off
PEAK_THRESHOLD = 1.3  # 30% above average = peak
```

### Email Settings
**File:** `apps/workers/email_agent.py`
```python
EMAIL_INTERVAL = 86400  # daily (use 60 for testing)
TO_EMAIL = "admin@demo.com"  # change recipient
```

---

## 🚀 Next Steps (Phase 2+)

After running:

1. **Multi-tenant Support**
   - Add tenant isolation
   - User authentication (NextAuth)
   - Role-based access control

2. **Advanced Features**
   - Weather integration (Open-Meteo)
   - Price feed (TOU rates)
   - Battery/solar recommendations
   - Device control (BACnet/Modbus)

3. **Production Deployment**
   - Kubernetes/Docker Swarm
   - CI/CD pipeline (GitHub Actions)
   - Monitoring (Grafana/Prometheus)
   - Backup & disaster recovery

4. **Business Features**
   - Billing & usage metering
   - White-labeling
   - API marketplace
   - Custom integrations

---

## 📚 Tech Stack

**Frontend:**
- Next.js 14, React 18, TypeScript
- Tailwind CSS, shadcn/ui
- TanStack Query, Recharts

**Backend:**
- FastAPI, Python 3.11, SQLAlchemy 2.0
- PostgreSQL + TimescaleDB
- MQTT (Mosquitto), NATS, Redis

**AI/ML:**
- Prophet (forecasting)
- OpenRouter/DeepSeek (LLM)
- Qdrant (vector store)

**Observability:**
- OpenTelemetry, Langfuse
- Docker, Docker Compose

---

## 📝 Common Commands

```bash
# Start everything
make docker-up
make migrate-up

# Stop everything
make docker-down

# View logs
docker-compose -f infra/docker/docker-compose.dev.yml logs -f

# Reset database
make db-reset

# Run tests
make test

# Format code
make format

# Lint code
make lint
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🆘 Support

- **Documentation:** Check `/docs` folder
- **Issues:** Open GitHub issue
- **Email:** support@energy-saas.local

---

## ✅Checklist

Use this to verify your setup:

- [ ] Docker services running (6 containers)
- [ ] Database migrated (7 tables created)
- [ ] Simulator publishing data
- [ ] Ingestion agent writing to DB
- [ ] Quality agent detecting anomalies
- [ ] Forecast agent generating predictions
- [ ] Advice agent creating recommendations
- [ ] Email agent sending digests
- [ ] API server responding (port 8000)
- [ ] Web dashboard loading (port 3000)
- [ ] Live data showing on dashboard
- [ ] Chart displaying usage patterns
- [ ] AI recommendations visible
- [ ] Email received in Mailpit

**All checked?** 🎉 Your is fully operational!

---

**Built with ❤️ for sustainable energy management**