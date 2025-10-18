from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    app_name: str = "Agentic Energy SaaS API"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/energy_saas"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # MQTT
    mqtt_broker: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: str = ""
    mqtt_password: str = ""
    
    # NATS
    nats_url: str = "nats://localhost:4222"
    
    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    
    # LLM
    ollama_base_url: str = "http://localhost:11434"
    paid_llm: bool = False
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    
    # Observability
    otel_exporter_endpoint: str = "http://localhost:4318"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://localhost:3000"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    cors_origins: list[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()