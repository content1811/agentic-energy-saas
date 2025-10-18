from sqlalchemy import Column, String, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from . import Base

class PriceFeed(Base):
    __tablename__ = 'price_feed'
    
    id = Column(UUID(as_uuid=True), server_default=func.gen_random_uuid())
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, primary_key=True)
    ts = Column(DateTime(timezone=True), nullable=False, primary_key=True)
    price_per_kwh = Column(Numeric(8, 4), nullable=False)
    currency = Column(String(3), nullable=False, server_default='USD')
    source = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())