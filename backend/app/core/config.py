from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    HKMA_BASE_URL: str = "https://api.hkma.gov.hk/public"
    MARKET_WATCH_USE_FIXTURES: bool = False
    HTTP_TIMEOUT_SECONDS: int = 10
    
    # Cache TTL settings
    rates_ttl_seconds: int = 21600
    liquidity_ttl_seconds: int = 21600
    
    class Config:
        env_file = ".env"

settings = Settings()
