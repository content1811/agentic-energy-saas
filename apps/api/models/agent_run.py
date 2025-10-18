from sqlalchemy import Column, String, Text, Integer, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from . import Base

class AgentRun(Base):
    __tablename__ = 'agent_runs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    run_id = Column(String(100), nullable=False, unique=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False, index=True)
    input_ref = Column(Text)
    output_ref = Column(Text)
    state = Column(String(20), nullable=False)
    error_message = Column(Text)
    latency_ms = Column(Integer)
    tokens_used = Column(Integer)
    cost_usd = Column(Numeric(10, 4))
    run_metadata  = Column(JSONB)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True))