from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    HKMA_BASE_URL: str = "https://api.hkma.gov.hk/public"
    MARKET_WATCH_USE_FIXTURES: bool = False
    HTTP_TIMEOUT_SECONDS: int = 10
    
    # Ingestion & Production Mode Configs
    APP_MODE: str = "development"
    ALLOW_DEMO_FALLBACK: bool = True

    # Auth / Tenant Context Foundation
    AUTH_MODE: str = "local"
    AUTH_DEFAULT_ORGANIZATION_ID: str = "demo-org"
    AUTH_DEFAULT_USER_ID: str = "demo-user"
    AUTH_DEFAULT_ROLE: str = "admin"
    AUTH_ALLOW_HEADER_OVERRIDES: bool = True

    # Cache TTL settings
    rates_ttl_seconds: int = 21600
    liquidity_ttl_seconds: int = 21600
    
    # Live Data Foundation Configs
    FX_PROVIDER: str = "frankfurter"
    FX_PROVIDER_BASE_URL: str = "https://api.frankfurter.dev/v2"
    ALPHA_VANTAGE_API_KEY: str = ""
    COMMODITY_PROVIDER: str = "fixture"
    MARKET_WATCH_AUTO_REFRESH_SECONDS: int = 300

    CORS_ALLOW_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5174,http://127.0.0.1:5174,"
        "http://localhost:5175,http://127.0.0.1:5175"
    )

    PERSISTENCE_BACKEND: str = "local"
    DATABASE_URL: str = "sqlite:///./storage_db/finsight_dev.db"
    DATABASE_ECHO: bool = False

    # S3 Object Storage Configuration
    S3_ENDPOINT_URL: Optional[str] = None
    S3_ACCESS_KEY_ID: Optional[str] = None
    S3_SECRET_ACCESS_KEY: Optional[str] = None
    S3_BUCKET_NAME: Optional[str] = None
    S3_REGION_NAME: str = "us-east-1"
    S3_SECURE: bool = True


    # Report Worker Harness Configuration
    REPORT_WORKER_ENABLED: bool = False
    REPORT_WORKER_MAX_JOBS_PER_TICK: int = 1

    @property
    def normalized_persistence_backend(self) -> str:
        return (self.PERSISTENCE_BACKEND or "local").strip().lower()

    @property
    def is_database_persistence_enabled(self) -> bool:
        return self.normalized_persistence_backend == "database"

    @property
    def normalized_auth_mode(self) -> str:
        return (self.AUTH_MODE or "local").strip().lower()

    @property
    def parsed_cors_origins(self) -> list[str]:
        if not self.CORS_ALLOW_ORIGINS:
            return []
        return [origin.strip() for origin in self.CORS_ALLOW_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"

settings = Settings()
