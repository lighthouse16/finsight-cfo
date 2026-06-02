from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    HKMA_BASE_URL: str = "https://api.hkma.gov.hk/public"
    MARKET_WATCH_USE_FIXTURES: bool = False
    HTTP_TIMEOUT_SECONDS: int = 10
    
    # Cache TTL settings
    rates_ttl_seconds: int = 21600
    liquidity_ttl_seconds: int = 21600
    
    # Live Data Foundation Configs
    FX_PROVIDER: str = "frankfurter"
    FX_PROVIDER_BASE_URL: str = "https://api.frankfurter.dev/v2"
    ALPHA_VANTAGE_API_KEY: str = ""
    COMMODITY_PROVIDER: str = "fixture"
    MARKET_WATCH_AUTO_REFRESH_SECONDS: int = 300
    
    class Config:
        env_file = ".env"

settings = Settings()
