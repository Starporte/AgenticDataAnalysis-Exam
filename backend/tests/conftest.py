"""Fixtures de test partagees."""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Utiliser SQLite en memoire pour les tests
TEST_DATABASE_URL = "sqlite:///./test.db"

# Patcher la config AVANT d'importer les modules backend
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["SECRET_KEY"] = "cle-test-securisee-pour-les-tests"
os.environ["OPENAI_API_KEY"] = "sk-test-fake-key"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

from backend.db.database import Base, get_db
from backend.api.main import app
from backend.db.models import User
from backend.api.auth import hasher_mot_de_passe, creer_token_acces

# Engine et session pour les tests
engine_test = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
SessionTest = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="function")
def db_session():
    """Cree une session DB de test avec tables fraiches."""
    Base.metadata.create_all(bind=engine_test)
    session = SessionTest()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(scope="function")
def client(db_session):
    """Client de test FastAPI avec injection de la session DB."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def utilisateur_test(db_session) -> User:
    """Cree un utilisateur de test en base."""
    utilisateur = User(
        email="test@example.com",
        mot_de_passe_hash=hasher_mot_de_passe("motdepasse123"),
        nom="Utilisateur Test",
    )
    db_session.add(utilisateur)
    db_session.commit()
    db_session.refresh(utilisateur)
    return utilisateur


@pytest.fixture
def token_test(utilisateur_test) -> str:
    """Genere un token JWT pour l'utilisateur de test."""
    return creer_token_acces(utilisateur_test.id)


@pytest.fixture
def headers_auth(token_test) -> dict:
    """Headers avec authentification pour les requetes de test."""
    return {"Authorization": f"Bearer {token_test}"}
