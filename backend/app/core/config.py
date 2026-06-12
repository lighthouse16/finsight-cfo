from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    HKMA_BASE_URL: str = "https://api.hkma.gov.hk/public"
    MARKET_WATCH_USE_FIXTURES: bool = False
    HTTP_TIMEOUT_SECONDS: int = 10
    
    # Ingestion & Production Mode Configs
    APP_MODE: str = "development"
    APP_VERSION: str = "1.0.0-rc1"
    ALLOW_DEMO_FALLBACK: bool = True

    # Auth / Tenant Context Foundation
    AUTH_MODE: str = "local"
    AUTH_SECRET: str = ""          # Deprecated fallback
    JWT_SECRET_KEY: str = ""       # Canonical JWT signing key
    JWT_ALGORITHM: str = "HS256"
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
    CHINADATA_API_KEY: str = ""
    IHS_MARKIT_API_KEY: str = ""
    FEDWATCH_API_KEY: str = ""
    BOCHK_CATALOG_CONFIGURED: bool = False
    COMMODITY_PROVIDER: str = "fixture"
    MARKET_WATCH_AUTO_REFRESH_SECONDS: int = 300

    CORS_ALLOW_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5174,http://127.0.0.1:5174,"
        "http://localhost:5175,http://127.0.0.1:5175"
    )

    PERSISTENCE_BACKEND: str = "local"
    STORAGE_BACKEND: str = "local"
    DATABASE_URL: str = "sqlite:///./storage_db/finsight_dev.db"
    DATABASE_ECHO: bool = False

    # Object Storage Configs
    OBJECT_STORAGE_BACKEND: str = "local_file"
    S3_ENDPOINT_URL: str = ""
    S3_BUCKET: str = ""             # Canonical S3 bucket name
    S3_BUCKET_NAME: str = ""        # Deprecated fallback
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_REGION: str = "us-east-1"    # Canonical S3 Region
    S3_REGION_NAME: str = "us-east-1" # Deprecated S3 Region fallback
    S3_FORCE_PATH_STYLE: bool = True
    S3_SECURE: bool = True

    # AI / LLM Provider Configuration
    LLM_PROVIDER: str = ""  # "openai", "azure_openai", "google_ai", or empty for deterministic fallback
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = ""
    GOOGLE_API_KEY: str = ""
    GOOGLE_AI_MODEL: str = "gemini-1.5-flash"
    GOOGLE_AI_BASE_URL: str = ""

    # Queue Configuration
    QUEUE_BACKEND: str = "in_process"  # "in_process", "redis" or "local" (as fallback)
    QUEUE_REDIS_URL: str = "redis://localhost:6379/0" # Canonical Redis URL
    REDIS_URL: str = "redis://localhost:6379/0"       # Deprecated fallback
    QUEUE_IN_PROCESS_MAXSIZE: int = 0

    # Rate Limiting Configuration
    RATE_LIMIT_IP_RATE: float = 10.0
    RATE_LIMIT_IP_BURST: float = 20.0
    RATE_LIMIT_WS_RATE: float = 50.0
    RATE_LIMIT_WS_BURST: float = 100.0

    # Report Worker Harness Configuration
    REPORT_WORKER_ENABLED: bool = False
    REPORT_WORKER_MAX_JOBS_PER_TICK: int = 1
    SCHEDULER_MODE: str = "manual"

    def __init__(self, **values):
        super().__init__(**values)
        
        # Standardize JWT secret
        auth_secret_val = self.JWT_SECRET_KEY or self.AUTH_SECRET
        if auth_secret_val:
            self.JWT_SECRET_KEY = auth_secret_val
            self.AUTH_SECRET = auth_secret_val
            
        # Standardize Redis URL
        redis_url_val = self.QUEUE_REDIS_URL or self.REDIS_URL
        if redis_url_val:
            self.QUEUE_REDIS_URL = redis_url_val
            self.REDIS_URL = redis_url_val
            
        # Standardize S3 Bucket
        s3_bucket_val = self.S3_BUCKET or self.S3_BUCKET_NAME
        if s3_bucket_val:
            self.S3_BUCKET = s3_bucket_val
            self.S3_BUCKET_NAME = s3_bucket_val

        # Standardize S3 Region
        s3_region_val = self.S3_REGION or self.S3_REGION_NAME
        if s3_region_val:
            self.S3_REGION = s3_region_val
            self.S3_REGION_NAME = s3_region_val

    @property
    def normalized_object_storage_backend(self) -> str:
        return (self.OBJECT_STORAGE_BACKEND or "local_file").strip().lower()

    @property
    def normalized_persistence_backend(self) -> str:
        return (self.PERSISTENCE_BACKEND or "local").strip().lower()

    @property
    def is_database_persistence_enabled(self) -> bool:
        return self.normalized_persistence_backend == "database"

    @property
    def normalized_ai_mode(self) -> str:
        """Detect AI provider mode from env configuration."""
        provider = self.LLM_PROVIDER.strip().lower()
        if provider == "google_ai" and self.GOOGLE_API_KEY.strip():
            return "google_ai"
        if provider == "openai" and self.OPENAI_API_KEY.strip():
            return "openai"
        if provider == "azure_openai" and self.AZURE_OPENAI_API_KEY.strip():
            return "azure_openai"
        if self.GOOGLE_API_KEY.strip():
            return "google_ai"
        if self.OPENAI_API_KEY.strip():
            return "openai"
        if self.AZURE_OPENAI_API_KEY.strip():
            return "azure_openai"
        return "deterministic_fallback"

    @property
    def is_llm_configured(self) -> bool:
        """Returns True if at least one LLM provider is fully configured."""
        return self.normalized_ai_mode in ("openai", "azure_openai", "google_ai")

    @property
    def normalized_queue_backend(self) -> str:
        return (self.QUEUE_BACKEND or "in_process").strip().lower()

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

@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (cleared in tests via cache_clear())."""
    return Settings()
