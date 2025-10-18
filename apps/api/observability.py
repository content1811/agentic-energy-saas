from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from fastapi import FastAPI
from config import get_settings

settings = get_settings()

def setup_telemetry(app: FastAPI, engine):
    if settings.environment == "development":
        provider = TracerProvider()
        processor = BatchSpanProcessor(
            OTLPSpanExporter(endpoint=f"{settings.otel_exporter_endpoint}/v1/traces")
        )
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        
        FastAPIInstrumentor.instrument_app(app)
        SQLAlchemyInstrumentor().instrument(engine=engine)

def get_tracer(name: str):
    return trace.get_tracer(name)