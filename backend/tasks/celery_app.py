"""Configuration Celery et taches asynchrones pour l'execution de l'agent."""

from celery import Celery
from backend.config import get_settings

settings = get_settings()

# Creation de l'application Celery
celery_app = Celery(
    "datastream_workers",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Configuration Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Paris",
    enable_utc=True,
    task_soft_time_limit=60,   # Avertissement apres 60s
    task_time_limit=90,        # Arret force apres 90s
    task_acks_late=True,       # Acquitter apres execution (resilience)
    worker_prefetch_multiplier=1,  # Un seul message a la fois par worker
)


@celery_app.task(bind=True, name="executer_agent_analyse")
def tache_executer_agent(self, session_id: int, user_id: int, contenu_message: str, dataset_ids: list):
    """
    Tache Celery pour executer l'agent d'analyse en arriere-plan.

    Permet de ne pas bloquer l'API FastAPI pendant les analyses longues.
    """
    from backend.db.database import SessionLocal
    from backend.db.models import Message, Dataset, AnalysisSession, Visualization
    from backend.agents.agent_manager import AgentManager

    db = SessionLocal()
    try:
        # Verifier que la session appartient a l'utilisateur
        session = (
            db.query(AnalysisSession)
            .filter(AnalysisSession.id == session_id, AnalysisSession.user_id == user_id)
            .first()
        )
        if not session:
            return {"erreur": "Session non trouvee"}

        # Charger les datasets
        datasets = []
        if dataset_ids:
            datasets = (
                db.query(Dataset)
                .filter(Dataset.id.in_(dataset_ids), Dataset.user_id == user_id)
                .all()
            )

        # Charger l'historique
        historique = (
            db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.cree_le)
            .all()
        )

        # Executer l'agent
        agent = AgentManager()
        resultat = agent.executer(
            historique_messages=historique,
            datasets=datasets,
            session_id=session_id,
        )

        # Sauvegarder la reponse
        msg_agent = Message(
            session_id=session_id,
            role="assistant",
            contenu=resultat["reponse"],
            metadata_msg=resultat.get("metadata"),
        )
        db.add(msg_agent)
        db.commit()
        db.refresh(msg_agent)

        # Sauvegarder les visualisations
        for fig_json in resultat.get("figures", []):
            vis = Visualization(
                session_id=session_id,
                message_id=msg_agent.id,
                titre=fig_json.get("layout", {}).get("title", {}).get("text", "Visualisation"),
                figure_json=fig_json,
            )
            db.add(vis)
        db.commit()

        return {
            "message_id": msg_agent.id,
            "reponse": resultat["reponse"],
            "nombre_figures": len(resultat.get("figures", [])),
        }

    except Exception as e:
        return {"erreur": str(e)}
    finally:
        db.close()
