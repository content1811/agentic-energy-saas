from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import get_settings
from database import engine
from observability import setup_telemetry
from routers import health, readings, advice

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lifespan startup
    yield
    # Lifespan shutdown (if needed)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# Setup telemetry BEFORE adding other middleware
setup_telemetry(app, engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(readings.router, prefix="/api/v1/readings", tags=["Readings"])
app.include_router(advice.router, prefix="/api/v1/advice", tags=["Advice"])

@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )