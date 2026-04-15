"""Client API pour communiquer avec le backend FastAPI."""

import os
import requests
import streamlit as st
from typing import Optional, List

# URL de base du backend (configurable via variable d'environnement)
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class APIClient:
    """Client HTTP pour le backend FastAPI avec gestion du token JWT."""

    def __init__(self):
        self.base_url = API_BASE_URL

    @property
    def token(self) -> Optional[str]:
        return st.session_state.get("jwt_token")

    @token.setter
    def token(self, valeur: str):
        st.session_state["jwt_token"] = valeur

    @property
    def headers(self) -> dict:
        """Headers avec le token d'authentification."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _gerer_reponse(self, reponse: requests.Response) -> dict:
        """Gere les erreurs de reponse HTTP."""
        if reponse.status_code == 401:
            st.session_state.pop("jwt_token", None)
            st.session_state.pop("utilisateur", None)
            st.error("Session expiree. Veuillez vous reconnecter.")
            st.rerun()
        if reponse.status_code >= 400:
            detail = reponse.json().get("detail", "Erreur inconnue")
            raise Exception(f"Erreur API ({reponse.status_code}): {detail}")
        return reponse.json()

    # --- Authentification ---

    def inscription(self, email: str, mot_de_passe: str, nom: str = "") -> dict:
        """Inscrit un nouvel utilisateur."""
        reponse = requests.post(
            f"{self.base_url}/api/auth/register",
            json={"email": email, "mot_de_passe": mot_de_passe, "nom": nom},
        )
        resultat = self._gerer_reponse(reponse)
        self.token = resultat["access_token"]
        return resultat

    def connexion(self, email: str, mot_de_passe: str) -> dict:
        """Connecte un utilisateur."""
        reponse = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"email": email, "mot_de_passe": mot_de_passe},
        )
        resultat = self._gerer_reponse(reponse)
        self.token = resultat["access_token"]
        return resultat

    def profil(self) -> dict:
        """Recupere le profil de l'utilisateur connecte."""
        reponse = requests.get(
            f"{self.base_url}/api/auth/me",
            headers=self.headers,
        )
        return self._gerer_reponse(reponse)

    # --- Sessions ---

    def creer_session(self, nom: str = "Nouvelle analyse", description: str = "") -> dict:
        """Cree une nouvelle session d'analyse."""
        reponse = requests.post(
            f"{self.base_url}/api/sessions",
            json={"nom": nom, "description": description},
            headers=self.headers,
        )
        return self._gerer_reponse(reponse)

    def lister_sessions(self) -> List[dict]:
        """Liste toutes les sessions de l'utilisateur."""
        reponse = requests.get(
            f"{self.base_url}/api/sessions",
            headers=self.headers,
        )
        resultat = self._gerer_reponse(reponse)
        return resultat.get("sessions", [])

    def obtenir_session(self, session_id: int) -> dict:
        """Recupere une session specifique."""
        reponse = requests.get(
            f"{self.base_url}/api/sessions/{session_id}",
            headers=self.headers,
        )
        return self._gerer_reponse(reponse)

    def supprimer_session(self, session_id: int):
        """Supprime une session."""
        reponse = requests.delete(
            f"{self.base_url}/api/sessions/{session_id}",
            headers=self.headers,
        )
        if reponse.status_code != 204:
            self._gerer_reponse(reponse)

    # --- Messages / Chat ---

    def lister_messages(self, session_id: int) -> List[dict]:
        """Recupere l'historique des messages d'une session."""
        reponse = requests.get(
            f"{self.base_url}/api/sessions/{session_id}/messages",
            headers=self.headers,
        )
        return self._gerer_reponse(reponse)

    def envoyer_message(self, session_id: int, contenu: str, dataset_ids: List[int] = None) -> dict:
        """Envoie un message a l'agent."""
        reponse = requests.post(
            f"{self.base_url}/api/sessions/{session_id}/chat",
            json={"contenu": contenu, "dataset_ids": dataset_ids or []},
            headers=self.headers,
            timeout=120,
        )
        return self._gerer_reponse(reponse)

    # --- Datasets ---

    def uploader_dataset(self, fichier, description: str = "") -> dict:
        """Upload un fichier CSV."""
        fichiers = {"fichier": (fichier.name, fichier.getvalue(), "text/csv")}
        donnees = {"description": description}
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        reponse = requests.post(
            f"{self.base_url}/api/datasets/upload",
            files=fichiers,
            data=donnees,
            headers=headers,
        )
        return self._gerer_reponse(reponse)

    def lister_datasets(self) -> List[dict]:
        """Liste les datasets de l'utilisateur."""
        reponse = requests.get(
            f"{self.base_url}/api/datasets",
            headers=self.headers,
        )
        resultat = self._gerer_reponse(reponse)
        return resultat.get("datasets", [])

    # --- Visualisations ---

    def lister_visualisations(self, session_id: int) -> List[dict]:
        """Recupere les visualisations d'une session."""
        reponse = requests.get(
            f"{self.base_url}/api/sessions/{session_id}/visualizations",
            headers=self.headers,
        )
        return self._gerer_reponse(reponse)


def get_api_client() -> APIClient:
    """Retourne une instance du client API."""
    return APIClient()
