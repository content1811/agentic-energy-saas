from sqlalchemy import Column, String, Float, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from . import Base

class MeterReading(Base):
    __tablename__ = 'meter_readings'
    
    id = Column(UUID(as_uuid=True), server_default=func.gen_random_uuid())
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, primary_key=True)
    site_id = Column(String(100), nullable=False, index=True, primary_key=True)
    ts = Column(DateTime(timezone=True), nullable=False, primary_key=True)
    kw = Column(Float, nullable=False)
    kwh = Column(Float)
    cost_est = Column(Numeric(10, 2))
    source = Column(String(50), nullable=False)
    quality_flag = Column(String(20))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())