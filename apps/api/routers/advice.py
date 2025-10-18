from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import Optional
from uuid import UUID
from database import get_db
from models.advice import Advice
from pydantic import BaseModel

router = APIRouter()

class AdviceResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    site_id: str
    ts: datetime
    type: str
    title: str
    text: str
    savings_est_usd: Optional[float]
    co2_saved_kg: Optional[float]
    confidence: Optional[float]
    status: str
    
    class Config:
        from_attributes = True

@router.get("/", response_model=list[AdviceResponse])
async def get_advice(
    tenant_id: UUID,
    site_id: str,
    status: Optional[str] = None,
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(Advice).filter(
        Advice.tenant_id == tenant_id,
        Advice.site_id == site_id
    )
    
    if status:
        query = query.filter(Advice.status == status)
    
    advice_list = query.order_by(desc(Advice.ts)).limit(limit).all()
    
    return advice_list