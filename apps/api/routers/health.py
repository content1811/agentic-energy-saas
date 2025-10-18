from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from config import get_settings

router = APIRouter()
settings = get_settings()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": settings.app_version
    }

@router.get("/health/db")
async def database_health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}

@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    checks = {"database": False, "api": True}
    
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass
    
    all_ready = all(checks.values())
    status = "ready" if all_ready else "not_ready"
    
    return {"status": status, "checks": checks}