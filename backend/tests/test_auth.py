"""Tests d'authentification : inscription, connexion, JWT."""

import pytest
from backend.api.auth import hasher_mot_de_passe, verifier_mot_de_passe, creer_token_acces
from jose import jwt
from backend.config import get_settings

settings = get_settings()


class TestHachageMdp:
    """Tests du hachage de mot de passe."""

    def test_hachage_produit_hash_different(self):
        """Le hash doit etre different du mot de passe original."""
        mdp = "motdepasse123"
        hache = hasher_mot_de_passe(mdp)
        assert hache != mdp

    def test_verification_correcte(self):
        """La verification doit reussir avec le bon mot de passe."""
        mdp = "motdepasse123"
        hache = hasher_mot_de_passe(mdp)
        assert verifier_mot_de_passe(mdp, hache) is True

    def test_verification_incorrecte(self):
        """La verification doit echouer avec un mauvais mot de passe."""
        hache = hasher_mot_de_passe("motdepasse123")
        assert verifier_mot_de_passe("mauvais_mdp", hache) is False

    def test_hash_unique(self):
        """Deux hachages du meme mdp doivent etre differents (salt)."""
        mdp = "motdepasse123"
        hash1 = hasher_mot_de_passe(mdp)
        hash2 = hasher_mot_de_passe(mdp)
        assert hash1 != hash2


class TestTokenJWT:
    """Tests de generation et validation JWT."""

    def test_creation_token(self):
        """Un token JWT valide doit etre genere."""
        token = creer_token_acces(user_id=1)
        assert token is not None
        assert isinstance(token, str)

    def test_payload_token(self):
        """Le payload doit contenir le user_id et l'expiration."""
        token = creer_token_acces(user_id=42)
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithme_jwt])
        assert payload["sub"] == 42
        assert "exp" in payload

    def test_token_invalide(self):
        """Un token avec une mauvaise cle doit lever une erreur."""
        token = creer_token_acces(user_id=1)
        with pytest.raises(Exception):
            jwt.decode(token, "mauvaise_cle", algorithms=[settings.algorithme_jwt])


class TestEndpointsAuth:
    """Tests des endpoints d'authentification."""

    def test_inscription_reussie(self, client):
        """L'inscription doit retourner un token."""
        reponse = client.post("/api/auth/register", json={
            "email": "nouveau@example.com",
            "mot_de_passe": "monmdp123",
            "nom": "Nouveau",
        })
        assert reponse.status_code == 201
        data = reponse.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_inscription_email_duplique(self, client, utilisateur_test):
        """L'inscription avec un email existant doit echouer."""
        reponse = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "mot_de_passe": "monmdp123",
        })
        assert reponse.status_code == 400

    def test_connexion_reussie(self, client, utilisateur_test):
        """La connexion avec de bons identifiants doit reussir."""
        reponse = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "mot_de_passe": "motdepasse123",
        })
        assert reponse.status_code == 200
        assert "access_token" in reponse.json()

    def test_connexion_mauvais_mdp(self, client, utilisateur_test):
        """La connexion avec un mauvais mot de passe doit echouer."""
        reponse = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "mot_de_passe": "mauvais_mdp",
        })
        assert reponse.status_code == 401

    def test_connexion_email_inexistant(self, client):
        """La connexion avec un email inexistant doit echouer."""
        reponse = client.post("/api/auth/login", json={
            "email": "inexistant@example.com",
            "mot_de_passe": "monmdp123",
        })
        assert reponse.status_code == 401

    def test_profil_authentifie(self, client, headers_auth):
        """L'endpoint /me doit retourner le profil de l'utilisateur."""
        reponse = client.get("/api/auth/me", headers=headers_auth)
        assert reponse.status_code == 200
        data = reponse.json()
        assert data["email"] == "test@example.com"

    def test_profil_sans_token(self, client):
        """L'endpoint /me sans token doit retourner 401."""
        reponse = client.get("/api/auth/me")
        assert reponse.status_code == 401

    def test_profil_token_invalide(self, client):
        """L'endpoint /me avec un token invalide doit retourner 401."""
        reponse = client.get("/api/auth/me", headers={
            "Authorization": "Bearer token_bidon_invalide"
        })
        assert reponse.status_code == 401
