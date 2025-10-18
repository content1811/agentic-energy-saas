from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from . import Base

class Forecast(Base):
    __tablename__ = 'forecasts'
    
    id = Column(UUID(as_uuid=True), server_default=func.gen_random_uuid())
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, primary_key=True)
    site_id = Column(String(100), nullable=False, index=True, primary_key=True)
    forecast_ts = Column(DateTime(timezone=True), nullable=False, primary_key=True)
    target_ts = Column(DateTime(timezone=True), nullable=False, primary_key=True)
    kw_predicted = Column(Float, nullable=False)
    confidence_lower = Column(Float)
    confidence_upper = Column(Float)
    model_version = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())