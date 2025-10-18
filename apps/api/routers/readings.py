from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import Optional
from uuid import UUID
from database import get_db
from models.meter_reading import MeterReading
from pydantic import BaseModel

router = APIRouter()

class MeterReadingResponse(BaseModel):
    tenant_id: UUID
    site_id: str
    ts: datetime
    kw: float
    kwh: Optional[float]
    cost_est: Optional[float]
    source: str
    
    class Config:
        from_attributes = True

@router.get("/", response_model=list[MeterReadingResponse])
async def get_readings(
    tenant_id: UUID,
    site_id: str,
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    readings = db.query(MeterReading).filter(
        MeterReading.tenant_id == tenant_id,
        MeterReading.site_id == site_id
    ).order_by(desc(MeterReading.ts)).limit(limit).all()
    
    return readings

@router.get("/latest", response_model=MeterReadingResponse)
async def get_latest_reading(
    tenant_id: UUID,
    site_id: str,
    db: Session = Depends(get_db)
):
    reading = db.query(MeterReading).filter(
        MeterReading.tenant_id == tenant_id,
        MeterReading.site_id == site_id
    ).order_by(desc(MeterReading.ts)).first()
    
    if not reading:
        raise HTTPException(status_code=404, detail="No readings found")
    
    return reading