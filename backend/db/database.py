"""Configuration de la base de donnees SQLAlchemy."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config import get_settings

Base = declarative_base()

_engine = None
_SessionLocal = None


def get_engine():
    """Retourne l'engine SQLAlchemy (creation lazy)."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
        )
    return _engine


def get_session_local():
    """Retourne la session factory (creation lazy)."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


# Alias pour compatibilite
@property
def engine():
    return get_engine()


def get_db():
    """Generateur de session DB pour injection de dependance FastAPI."""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
