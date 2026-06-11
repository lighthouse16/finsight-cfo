from typing import Generator
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings, Settings

# Global engine placeholder to be initialized lazily or explicitly
_engine: Engine | None = None
SessionLocal: sessionmaker | None = None

def create_engine_from_settings(app_settings: Settings) -> Engine:
    """
    Creates a new SQLAlchemy Engine instance from application settings.
    """
    url = app_settings.DATABASE_URL
    echo = app_settings.DATABASE_ECHO
    
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        
    return create_engine(
        url,
        echo=echo,
        connect_args=connect_args
    )

def get_engine() -> Engine:
    """
    Lazily initializes and returns the global Engine.
    """
    global _engine, SessionLocal
    if _engine is None:
        _engine = create_engine_from_settings(settings)
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_engine
        )
    return _engine

def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a scoped database session.
    """
    global SessionLocal
    if SessionLocal is None:
        get_engine()
        
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
