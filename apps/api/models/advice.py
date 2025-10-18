from sqlalchemy import Column, String, Text, Numeric, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from . import Base

class Advice(Base):
    __tablename__ = 'advice'
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    site_id = Column(String(100), nullable=False, index=True)
    ts = Column(DateTime(timezone=True), nullable=False, index=True)
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    savings_est_usd = Column(Numeric(10, 2))
    co2_saved_kg = Column(Numeric(10, 2))
    confidence = Column(Float)
    status = Column(String(20), nullable=False, server_default='pending')
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())