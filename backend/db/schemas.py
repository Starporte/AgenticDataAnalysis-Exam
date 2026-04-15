"""Schemas Pydantic pour la validation des requetes et reponses API."""

from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import datetime


# --- Authentification ---

class InscriptionRequete(BaseModel):
    email: EmailStr
    mot_de_passe: str
    nom: Optional[str] = None


class ConnexionRequete(BaseModel):
    email: EmailStr
    mot_de_passe: str


class TokenReponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UtilisateurReponse(BaseModel):
    id: int
    email: str
    nom: Optional[str] = None
    est_actif: bool
    cree_le: datetime

    class Config:
        from_attributes = True


# --- Sessions ---

class SessionCreerRequete(BaseModel):
    nom: str = "Nouvelle analyse"
    description: Optional[str] = None


class SessionReponse(BaseModel):
    id: int
    nom: str
    description: Optional[str] = None
    nom_dataset: Optional[str] = None
    cree_le: datetime
    mis_a_jour_le: Optional[datetime] = None

    class Config:
        from_attributes = True


class SessionListeReponse(BaseModel):
    sessions: List[SessionReponse]


# --- Messages ---

class MessageRequete(BaseModel):
    contenu: str
    dataset_ids: Optional[List[int]] = None


class MessageReponse(BaseModel):
    id: int
    role: str
    contenu: str
    metadata_msg: Optional[Any] = None
    cree_le: datetime
    visualisations: Optional[List[Any]] = None

    class Config:
        from_attributes = True


class ChatReponse(BaseModel):
    reponse: MessageReponse
    visualisations: Optional[List[Any]] = None


# --- Datasets ---

class DatasetReponse(BaseModel):
    id: int
    nom_fichier: str
    description: Optional[str] = None
    taille_octets: Optional[int] = None
    nombre_lignes: Optional[int] = None
    nombre_colonnes: Optional[int] = None
    noms_colonnes: Optional[List[str]] = None
    cree_le: datetime

    class Config:
        from_attributes = True


class DatasetListeReponse(BaseModel):
    datasets: List[DatasetReponse]


# --- Visualisations ---

class VisualisationReponse(BaseModel):
    id: int
    titre: Optional[str] = None
    figure_json: Any
    cree_le: datetime

    class Config:
        from_attributes = True


# --- Health ---

class HealthReponse(BaseModel):
    status: str
    base_de_donnees: str
    redis: str
