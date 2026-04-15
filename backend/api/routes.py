"""Routes API principales : sessions, datasets, chat."""

import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
import json

from backend.db.database import get_db
from backend.db.models import (
    User, AnalysisSession, Message, Dataset, Visualization
)
from backend.db.schemas import (
    SessionCreerRequete, SessionReponse, SessionListeReponse,
    MessageRequete, MessageReponse, ChatReponse,
    DatasetReponse, DatasetListeReponse, VisualisationReponse,
)
from backend.api.dependencies import get_current_user
from backend.agents.agent_manager import AgentManager

router = APIRouter(prefix="/api", tags=["API"])

# Repertoire d'upload par utilisateur
UPLOAD_DIR = "uploads"


# --- Sessions ---

@router.post("/sessions", response_model=SessionReponse, status_code=status.HTTP_201_CREATED)
def creer_session(
    requete: SessionCreerRequete,
    db: Session = Depends(get_db),
    utilisateur: User = Depends(get_current_user),
):
    """Cree une nouvelle session d'analyse."""
    session = AnalysisSession(
        user_id=utilisateur.id,
        nom=requete.nom,
        description=requete.description,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions", response_model=SessionListeReponse)
def lister_sessions(
    db: Session = Depends(get_db),
    utilisateur: User = Depends(get_current_user),
):
    """Liste toutes les sessions de l'utilisateur connecte."""
    sessions = (
        db.query(AnalysisSession)
        .filter(AnalysisSession.user_id == utilisateur.id)
        .order_by(AnalysisSession.mis_a_jour_le.desc())
        .all()
    )
    return SessionListeReponse(sessions=sessions)


@router.get("/sessions/{session_id}", response_model=SessionReponse)
def obtenir_session(
    session_id: int,
    db: Session = Depends(get_db),
    utilisateur: User = Depends(get_current_user),
):
    """Recupere une session specifique."""
    session = (
        db.query(AnalysisSession)
        .filter(AnalysisSession.id == session_id, AnalysisSession.user_id == utilisateur.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvee")
    return session


@router.patch("/sessions/{session_id}", response_model=SessionReponse)
def mettre_a_jour_session(
    session_id: int,
    requete: SessionCreerRequete,
    db: Session = Depends(get_db),
    utilisateur: User = Depends(get_current_user),
):
    """Met a jour le nom ou la description d'une session."""
    session = (
        db.query(AnalysisSession)
        .filter(AnalysisSession.id == session_id, AnalysisSession.user_id == utilisateur.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvee")
    if requete.nom:
        session.nom = requete.nom
    if requete.description is not None:
        session.description = requete.description
    db.commit()
    db.refresh(session)
    return session


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_session(
    session_id: int,
    db: Session = Depends(get_db),
    utilisateur: User = Depends(get_current_user),
):
    """Supprime une session d'analyse."""
    session = (
        db.query(AnalysisSession)
        .filter(AnalysisSession.id == session_id, AnalysisSession.user_id == utilisateur.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvee")
    db.delete(session)
    db.commit()


# --- Messages / Chat ---

@router.get("/sessions/{session_id}/messages", response_model=List[MessageReponse])
def lister_messages(
    session_id: int,
    db: Session = Depends(get_db),
    utilisateur: User = Depends(get_current_user),
):
    """Recupere l'historique des messages d'une session."""
    session = (
        db.query(AnalysisSession)
        .filter(AnalysisSession.id == session_id, AnalysisSession.user_id == utilisateur.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvee")

    messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.cree_le)
        .all()
    )

    resultats = []
    for msg in messages:
        vis_list = [
            {"id": v.id, "titre": v.titre, "figure_json": v.figure_json}
            for v in msg.visualisations
        ]
        resultats.append(MessageReponse(
            id=msg.id,
            role=msg.role,
            contenu=msg.contenu,
            metadata_msg=msg.metadata_msg,
            cree_le=msg.cree_le,
            visualisations=vis_list if vis_list else None,
        ))
    return resultats


@router.post("/sessions/{session_id}/chat", response_model=ChatReponse)
def envoyer_message(
    session_id: int,
    requete: MessageRequete,
    db: Session = Depends(get_db),
    utilisateur: User = Depends(get_current_user),
):
    """Envoie un message a l'agent et retourne sa reponse."""
    # Verifier que la session appartient a l'utilisateur
    session = (
        db.query(AnalysisSession)
        .filter(AnalysisSession.id == session_id, AnalysisSession.user_id == utilisateur.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvee")

    # Sauvegarder le message utilisateur
    msg_utilisateur = Message(
        session_id=session_id,
        role="user",
        contenu=requete.contenu,
    )
    db.add(msg_utilisateur)
    db.commit()
    db.refresh(msg_utilisateur)

    # Recuperer les datasets de l'utilisateur
    datasets = []
    if requete.dataset_ids:
        datasets = (
            db.query(Dataset)
            .filter(Dataset.id.in_(requete.dataset_ids), Dataset.user_id == utilisateur.id)
            .all()
        )

    # Charger l'historique de conversation
    historique = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.cree_le)
        .all()
    )

    # Invoquer l'agent
    agent_manager = AgentManager()
    resultat = agent_manager.executer(
        historique_messages=historique,
        datasets=datasets,
        session_id=session_id,
    )

    # Sauvegarder la reponse de l'agent
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
    visualisations_reponse = []
    for fig_json in resultat.get("figures", []):
        vis = Visualization(
            session_id=session_id,
            message_id=msg_agent.id,
            titre=fig_json.get("layout", {}).get("title", {}).get("text", "Visualisation"),
            figure_json=fig_json,
        )
        db.add(vis)
        db.commit()
        db.refresh(vis)
        visualisations_reponse.append({
            "id": vis.id,
            "titre": vis.titre,
            "figure_json": vis.figure_json,
        })

    # Mettre a jour la session
    session.mis_a_jour_le = msg_agent.cree_le
    db.commit()

    return ChatReponse(
        reponse=MessageReponse(
            id=msg_agent.id,
            role=msg_agent.role,
            contenu=msg_agent.contenu,
            metadata_msg=msg_agent.metadata_msg,
            cree_le=msg_agent.cree_le,
            visualisations=visualisations_reponse if visualisations_reponse else None,
        ),
        visualisations=visualisations_reponse if visualisations_reponse else None,
    )


# --- Datasets ---

@router.post("/datasets/upload", response_model=DatasetReponse, status_code=status.HTTP_201_CREATED)
async def uploader_dataset(
    fichier: UploadFile = File(...),
    description: str = "",
    db: Session = Depends(get_db),
    utilisateur: User = Depends(get_current_user),
):
    """Upload un fichier CSV et l'enregistre en base."""
    if not fichier.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers CSV sont acceptes")

    # Creer le repertoire utilisateur
    dossier_utilisateur = os.path.join(UPLOAD_DIR, str(utilisateur.id))
    os.makedirs(dossier_utilisateur, exist_ok=True)

    # Sauvegarder le fichier
    chemin_fichier = os.path.join(dossier_utilisateur, fichier.filename)
    with open(chemin_fichier, "wb") as f:
        contenu = await fichier.read()
        f.write(contenu)

    # Analyser le CSV
    try:
        df = pd.read_csv(chemin_fichier)
        nombre_lignes = len(df)
        nombre_colonnes = len(df.columns)
        noms_colonnes = list(df.columns)
    except Exception:
        nombre_lignes = None
        nombre_colonnes = None
        noms_colonnes = None

    # Creer l'enregistrement en base
    dataset = Dataset(
        user_id=utilisateur.id,
        nom_fichier=fichier.filename,
        chemin_fichier=chemin_fichier,
        description=description,
        taille_octets=len(contenu),
        nombre_lignes=nombre_lignes,
        nombre_colonnes=nombre_colonnes,
        noms_colonnes=noms_colonnes,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.get("/datasets", response_model=DatasetListeReponse)
def lister_datasets(
    db: Session = Depends(get_db),
    utilisateur: User = Depends(get_current_user),
):
    """Liste les datasets de l'utilisateur connecte."""
    datasets = (
        db.query(Dataset)
        .filter(Dataset.user_id == utilisateur.id)
        .order_by(Dataset.cree_le.desc())
        .all()
    )
    return DatasetListeReponse(datasets=datasets)


@router.delete("/datasets/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    utilisateur: User = Depends(get_current_user),
):
    """Supprime un dataset."""
    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id, Dataset.user_id == utilisateur.id)
        .first()
    )
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset non trouve")

    # Supprimer le fichier physique
    if os.path.exists(dataset.chemin_fichier):
        os.remove(dataset.chemin_fichier)

    db.delete(dataset)
    db.commit()


# --- Visualisations ---

@router.get("/sessions/{session_id}/visualizations", response_model=List[VisualisationReponse])
def lister_visualisations(
    session_id: int,
    db: Session = Depends(get_db),
    utilisateur: User = Depends(get_current_user),
):
    """Recupere toutes les visualisations d'une session."""
    session = (
        db.query(AnalysisSession)
        .filter(AnalysisSession.id == session_id, AnalysisSession.user_id == utilisateur.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvee")

    return (
        db.query(Visualization)
        .filter(Visualization.session_id == session_id)
        .order_by(Visualization.cree_le)
        .all()
    )
