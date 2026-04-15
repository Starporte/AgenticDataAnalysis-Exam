"""Configuration centralisee de l'application via variables d'environnement."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Parametres de l'application charges depuis .env ou variables d'environnement."""

    # Base de donnees
    database_url: str = "postgresql://postgres:postgres@localhost:5432/datastream"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Authentification JWT
    secret_key: str = "changez-moi-en-production-avec-une-vraie-cle-secrete"
    algorithme_jwt: str = "HS256"
    duree_expiration_token: int = 60  # minutes

    # OpenAI
    openai_api_key: str = ""

    # CORS
    origines_autorisees: str = "http://localhost:8501"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # Limites d'execution de code
    timeout_execution_code: int = 30  # secondes
    taille_max_upload: int = 200  # MB

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """Retourne les parametres caches (singleton)."""
    return Settings()
