from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from . import Base

class Weather(Base):
    __tablename__ = 'weather'
    
    id = Column(UUID(as_uuid=True), server_default=func.gen_random_uuid())
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, primary_key=True)
    location = Column(String(100), nullable=False, primary_key=True)
    ts = Column(DateTime(timezone=True), nullable=False, primary_key=True)
    temp_c = Column(Float, nullable=False)
    humidity = Column(Float)
    wind_speed = Column(Float)
    source = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())