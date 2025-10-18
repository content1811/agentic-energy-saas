"""Initial schema with core tables

Revision ID: 001
Create Date: 2025-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('role', sa.String(50), nullable=False, server_default='viewer'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Meter readings (timeseries)
    op.create_table(
        'meter_readings',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('site_id', sa.String(100), nullable=False, index=True),
        sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
        sa.Column('kw', sa.Float, nullable=False),
        sa.Column('kwh', sa.Float, nullable=True),
        sa.Column('cost_est', sa.Numeric(10, 2), nullable=True),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('quality_flag', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('tenant_id', 'site_id', 'ts'),
    )
    
    # Convert to hypertable
    op.execute("SELECT create_hypertable('meter_readings', 'ts', if_not_exists => TRUE)")
    op.create_index('idx_meter_readings_tenant_site', 'meter_readings', ['tenant_id', 'site_id', 'ts'])
    
    # Price feed (timeseries)
    op.create_table(
        'price_feed',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
        sa.Column('price_per_kwh', sa.Numeric(8, 4), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('tenant_id', 'ts'),
    )
    
    op.execute("SELECT create_hypertable('price_feed', 'ts', if_not_exists => TRUE)")
    
    # Weather data (timeseries)
    op.create_table(
        'weather',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('location', sa.String(100), nullable=False),
        sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
        sa.Column('temp_c', sa.Float, nullable=False),
        sa.Column('humidity', sa.Float, nullable=True),
        sa.Column('wind_speed', sa.Float, nullable=True),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('tenant_id', 'location', 'ts'),
    )
    
    op.execute("SELECT create_hypertable('weather', 'ts', if_not_exists => TRUE)")
    
    # Advice/recommendations
    op.create_table(
        'advice',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('site_id', sa.String(100), nullable=False, index=True),
        sa.Column('ts', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('text', sa.Text, nullable=False),
        sa.Column('savings_est_usd', sa.Numeric(10, 2), nullable=True),
        sa.Column('co2_saved_kg', sa.Numeric(10, 2), nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    op.create_index('idx_advice_tenant_site_ts', 'advice', ['tenant_id', 'site_id', 'ts'])
    
    # Agent runs (observability)
    op.create_table(
        'agent_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('run_id', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('agent_name', sa.String(100), nullable=False, index=True),
        sa.Column('input_ref', sa.Text, nullable=True),
        sa.Column('output_ref', sa.Text, nullable=True),
        sa.Column('state', sa.String(20), nullable=False),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('latency_ms', sa.Integer, nullable=True),
        sa.Column('tokens_used', sa.Integer, nullable=True),
        sa.Column('cost_usd', sa.Numeric(10, 4), nullable=True),
        sa.Column('run_metadata', postgresql.JSONB, nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    op.create_index('idx_agent_runs_tenant_agent', 'agent_runs', ['tenant_id', 'agent_name'])
    op.create_index('idx_agent_runs_state', 'agent_runs', ['state'])
    
    # Forecasts (timeseries)
    op.create_table(
        'forecasts',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('site_id', sa.String(100), nullable=False, index=True),
        sa.Column('forecast_ts', sa.DateTime(timezone=True), nullable=False),
        sa.Column('target_ts', sa.DateTime(timezone=True), nullable=False),
        sa.Column('kw_predicted', sa.Float, nullable=False),
        sa.Column('confidence_lower', sa.Float, nullable=True),
        sa.Column('confidence_upper', sa.Float, nullable=True),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('tenant_id', 'site_id', 'forecast_ts', 'target_ts'),
    )
    
    op.execute("SELECT create_hypertable('forecasts', 'target_ts', if_not_exists => TRUE)")

def downgrade() -> None:
    op.drop_table('forecasts')
    op.drop_table('agent_runs')
    op.drop_table('advice')
    op.drop_table('weather')
    op.drop_table('price_feed')
    op.drop_table('meter_readings')
    op.drop_table('users')