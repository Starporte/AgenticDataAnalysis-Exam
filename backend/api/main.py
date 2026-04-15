"""Application FastAPI principale avec middleware, logging et health checks."""

import uuid
import time
import structlog
import redis
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.config import get_settings
from backend.db.database import engine, Base, SessionLocal
from backend.api.auth import router as auth_router
from backend.api.routes import router as api_router

settings = get_settings()

# Configuration du logging structure
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()

# Creation de l'application FastAPI
app = FastAPI(
    title="Agentic Data Analysis API",
    description="Plateforme d'analyse de donnees agentique - DataStream AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origines_autorisees.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware d'ID de requete pour le tracage distribue
@app.middleware("http")
async def middleware_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    debut = time.time()

    response = await call_next(request)

    duree = time.time() - debut
    response.headers["X-Request-ID"] = request_id

    logger.info(
        "requete_traitee",
        request_id=request_id,
        methode=request.method,
        chemin=request.url.path,
        status_code=response.status_code,
        duree_ms=round(duree * 1000, 2),
    )
    return response


# Gestionnaire d'exceptions global
@app.exception_handler(Exception)
async def gestionnaire_exception_global(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "inconnu")
    logger.error(
        "erreur_non_geree",
        request_id=request_id,
        erreur=str(exc),
        type_erreur=type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erreur interne du serveur",
            "request_id": request_id,
        },
    )


# Enregistrement des routeurs
app.include_router(auth_router)
app.include_router(api_router)


# Evenement de demarrage : creation des tables
@app.on_event("startup")
async def demarrage():
    logger.info("demarrage_application", version="1.0.0")
    Base.metadata.create_all(bind=engine)


# --- Endpoints de sante et metriques ---

@app.get("/health", tags=["Sante"])
async def health_check():
    """Verifie la sante de l'application et de ses dependances."""
    etat_db = "ok"
    etat_redis = "ok"

    # Test PostgreSQL
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception:
        etat_db = "erreur"

    # Test Redis
    try:
        client_redis = redis.from_url(settings.redis_url)
        client_redis.ping()
        client_redis.close()
    except Exception:
        etat_redis = "erreur"

    status_global = "healthy" if etat_db == "ok" and etat_redis == "ok" else "degraded"

    return {
        "status": status_global,
        "base_de_donnees": etat_db,
        "redis": etat_redis,
    }


@app.get("/metrics", tags=["Metriques"])
async def metriques():
    """Endpoint de metriques au format Prometheus."""
    return {
        "app_info": {"version": "1.0.0", "nom": "agentic-data-analysis"},
        "status": "running",
    }
