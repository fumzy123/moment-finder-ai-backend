from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # AWS / MinIO Storage Configuration
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str
    S3_ENDPOINT_URL: str | None = None
    S3_USE_SSL: bool = True
    DATABASE_URL: str
    
    # Celery & Message Broker
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    
    # AI Engines
    ACTIVE_AI_ENGINE: str = "GEMINI"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_NAME: str = "gemini-2.5-flash-lite"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
