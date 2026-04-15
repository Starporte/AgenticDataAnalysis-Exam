"""Tests des endpoints API : sessions, datasets, health."""

import pytest


class TestHealth:
    """Tests de l'endpoint de sante."""

    def test_health_check(self, client):
        """L'endpoint /health doit repondre."""
        reponse = client.get("/health")
        assert reponse.status_code == 200
        data = reponse.json()
        assert "status" in data

    def test_metrics(self, client):
        """L'endpoint /metrics doit repondre."""
        reponse = client.get("/metrics")
        assert reponse.status_code == 200


class TestSessions:
    """Tests des endpoints de sessions."""

    def test_creer_session(self, client, headers_auth):
        """La creation de session doit reussir."""
        reponse = client.post("/api/sessions", json={
            "nom": "Test Analyse",
            "description": "Session de test",
        }, headers=headers_auth)
        assert reponse.status_code == 201
        data = reponse.json()
        assert data["nom"] == "Test Analyse"
        assert "id" in data

    def test_creer_session_sans_auth(self, client):
        """La creation sans auth doit echouer."""
        reponse = client.post("/api/sessions", json={"nom": "Test"})
        assert reponse.status_code == 401

    def test_lister_sessions(self, client, headers_auth):
        """La liste des sessions doit fonctionner."""
        client.post("/api/sessions", json={"nom": "Session 1"}, headers=headers_auth)
        client.post("/api/sessions", json={"nom": "Session 2"}, headers=headers_auth)

        reponse = client.get("/api/sessions", headers=headers_auth)
        assert reponse.status_code == 200
        data = reponse.json()
        assert len(data["sessions"]) == 2

    def test_obtenir_session(self, client, headers_auth):
        """La recuperation d'une session doit fonctionner."""
        creation = client.post("/api/sessions", json={"nom": "Ma Session"}, headers=headers_auth)
        session_id = creation.json()["id"]

        reponse = client.get(f"/api/sessions/{session_id}", headers=headers_auth)
        assert reponse.status_code == 200
        assert reponse.json()["nom"] == "Ma Session"

    def test_obtenir_session_inexistante(self, client, headers_auth):
        """La recuperation d'une session inexistante doit retourner 404."""
        reponse = client.get("/api/sessions/99999", headers=headers_auth)
        assert reponse.status_code == 404

    def test_supprimer_session(self, client, headers_auth):
        """La suppression de session doit fonctionner."""
        creation = client.post("/api/sessions", json={"nom": "A supprimer"}, headers=headers_auth)
        session_id = creation.json()["id"]

        reponse = client.delete(f"/api/sessions/{session_id}", headers=headers_auth)
        assert reponse.status_code == 204

        reponse = client.get(f"/api/sessions/{session_id}", headers=headers_auth)
        assert reponse.status_code == 404


class TestIsolationDonnees:
    """Tests d'isolation des donnees entre utilisateurs."""

    def test_utilisateur_ne_voit_pas_sessions_autre(self, client, headers_auth, db_session):
        """Un utilisateur ne doit pas voir les sessions d'un autre."""
        client.post("/api/sessions", json={"nom": "Session User 1"}, headers=headers_auth)

        reponse = client.post("/api/auth/register", json={
            "email": "user2@example.com",
            "mot_de_passe": "monmdp456",
        })
        token2 = reponse.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        reponse = client.get("/api/sessions", headers=headers2)
        assert reponse.status_code == 200
        assert len(reponse.json()["sessions"]) == 0

    def test_utilisateur_ne_peut_pas_acceder_session_autre(self, client, headers_auth, db_session):
        """Un utilisateur ne doit pas acceder a la session d'un autre."""
        creation = client.post("/api/sessions", json={"nom": "Session Privee"}, headers=headers_auth)
        session_id = creation.json()["id"]

        reponse = client.post("/api/auth/register", json={
            "email": "intrus@example.com",
            "mot_de_passe": "monmdp789",
        })
        token_intrus = reponse.json()["access_token"]
        headers_intrus = {"Authorization": f"Bearer {token_intrus}"}

        reponse = client.get(f"/api/sessions/{session_id}", headers=headers_intrus)
        assert reponse.status_code == 404

    def test_acces_non_autorise_retourne_401(self, client):
        """Les endpoints proteges sans token retournent 401."""
        reponse = client.get("/api/sessions")
        assert reponse.status_code == 401

        reponse = client.get("/api/datasets")
        assert reponse.status_code == 401
