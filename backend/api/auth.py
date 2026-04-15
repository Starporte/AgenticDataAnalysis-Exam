"""Routes d'authentification : inscription et connexion."""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt

from backend.db.database import get_db
from backend.db.models import User
from backend.db.schemas import (
    InscriptionRequete, ConnexionRequete, TokenReponse, UtilisateurReponse
)
from backend.api.dependencies import get_current_user
from backend.config import get_settings

router = APIRouter(prefix="/api/auth", tags=["Authentification"])

# Contexte de hachage bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
settings = get_settings()


def hasher_mot_de_passe(mot_de_passe: str) -> str:
    """Hache un mot de passe avec bcrypt."""
    return pwd_context.hash(mot_de_passe)


def verifier_mot_de_passe(mot_de_passe: str, mot_de_passe_hash: str) -> bool:
    """Verifie un mot de passe contre son hash bcrypt."""
    return pwd_context.verify(mot_de_passe, mot_de_passe_hash)


def creer_token_acces(user_id: int) -> str:
    """Cree un token JWT avec expiration."""
    expiration = datetime.utcnow() + timedelta(minutes=settings.duree_expiration_token)
    donnees = {"sub": str(user_id), "exp": expiration}
    return jwt.encode(donnees, settings.secret_key, algorithm=settings.algorithme_jwt)


@router.post("/register", response_model=TokenReponse, status_code=status.HTTP_201_CREATED)
def inscription(requete: InscriptionRequete, db: Session = Depends(get_db)):
    """Inscrit un nouvel utilisateur et retourne un token JWT."""
    # Verifier si l'email existe deja
    utilisateur_existant = db.query(User).filter(User.email == requete.email).first()
    if utilisateur_existant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un compte avec cet email existe deja",
        )

    # Creer l'utilisateur
    nouvel_utilisateur = User(
        email=requete.email,
        mot_de_passe_hash=hasher_mot_de_passe(requete.mot_de_passe),
        nom=requete.nom,
    )
    db.add(nouvel_utilisateur)
    db.commit()
    db.refresh(nouvel_utilisateur)

    # Generer le token
    token = creer_token_acces(nouvel_utilisateur.id)
    return TokenReponse(access_token=token)


@router.post("/login", response_model=TokenReponse)
def connexion(requete: ConnexionRequete, db: Session = Depends(get_db)):
    """Authentifie un utilisateur et retourne un token JWT."""
    utilisateur = db.query(User).filter(User.email == requete.email).first()
    if not utilisateur or not verifier_mot_de_passe(requete.mot_de_passe, utilisateur.mot_de_passe_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )

    token = creer_token_acces(utilisateur.id)
    return TokenReponse(access_token=token)


@router.get("/me", response_model=UtilisateurReponse)
def profil_utilisateur(utilisateur: User = Depends(get_current_user)):
    """Retourne les informations de l'utilisateur connecte."""
    return utilisateur
