# Agentic Energy SaaS

Enterprise energy monitoring and optimization platform with AI-powered recommendations.

## Features

- 🔌 Real-time energy consumption monitoring
- 📊 Predictive forecasting (15-min intervals)
- 💡 Actionable AI-driven savings recommendations
- 🌱 Carbon footprint tracking
- 📧 Automated reporting and alerts
- 🔐 Multi-tenant ready with RBAC

## Tech Stack

**Frontend:** Next.js 14, TypeScript, Tailwind CSS, shadcn/ui  
**Backend:** FastAPI, Python 3.11+, SQLAlchemy  
**Database:** PostgreSQL + TimescaleDB  
**Agents:** LangGraph, LangChain  
**Messaging:** NATS, MQTT (Mosquitto)  
**Vector Store:** Qdrant  
**Observability:** OpenTelemetry, Langfuse, Grafana

## Quick Start

### Prerequisites

- Node.js 18+ and pnpm
- Python 3.11+
- Docker & Docker Compose
- Poetry (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd agentic-energy-saas