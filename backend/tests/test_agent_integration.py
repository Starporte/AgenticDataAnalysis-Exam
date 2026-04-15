"""Tests d'integration de l'agent : persistance de session et workflow complet."""

import pytest
from backend.db.models import AnalysisSession, Message, Visualization


class TestPersistanceSessionAPI:
    """Tests de la persistance de session via l'API."""

    def test_creer_session_et_recuperer(self, client, headers_auth):
        """Creer une session puis la recuperer doit retourner les memes donnees."""
        reponse = client.post("/api/sessions", json={
            "nom": "Analyse Ventes",
            "description": "Analyse des ventes Q1",
        }, headers=headers_auth)
        assert reponse.status_code == 201
        session_id = reponse.json()["id"]

        reponse = client.get(f"/api/sessions/{session_id}", headers=headers_auth)
        assert reponse.status_code == 200
        data = reponse.json()
        assert data["nom"] == "Analyse Ventes"
        assert data["description"] == "Analyse des ventes Q1"

    def test_historique_messages_persiste(self, client, headers_auth, db_session, utilisateur_test):
        """Les messages doivent etre persistes et recuperables."""
        reponse = client.post("/api/sessions", json={"nom": "Chat Test"}, headers=headers_auth)
        session_id = reponse.json()["id"]

        msg1 = Message(session_id=session_id, role="user", contenu="Quelles sont les colonnes ?")
        msg2 = Message(session_id=session_id, role="assistant", contenu="Voici les colonnes : col1, col2, col3")
        db_session.add_all([msg1, msg2])
        db_session.commit()

        reponse = client.get(f"/api/sessions/{session_id}/messages", headers=headers_auth)
        assert reponse.status_code == 200
        messages = reponse.json()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["contenu"] == "Quelles sont les colonnes ?"
        assert messages[1]["role"] == "assistant"

    def test_visualisations_persistees(self, client, headers_auth, db_session, utilisateur_test):
        """Les visualisations doivent etre stockees et recuperables."""
        reponse = client.post("/api/sessions", json={"nom": "Viz Test"}, headers=headers_auth)
        session_id = reponse.json()["id"]

        msg = Message(session_id=session_id, role="assistant", contenu="Voici le graphique")
        db_session.add(msg)
        db_session.commit()

        vis = Visualization(
            session_id=session_id,
            message_id=msg.id,
            titre="Histogramme Age",
            figure_json={"data": [{"type": "histogram", "x": [20, 30, 40]}], "layout": {"title": {"text": "Age"}}},
        )
        db_session.add(vis)
        db_session.commit()

        reponse = client.get(f"/api/sessions/{session_id}/visualizations", headers=headers_auth)
        assert reponse.status_code == 200
        visualisations = reponse.json()
        assert len(visualisations) == 1
        assert visualisations[0]["titre"] == "Histogramme Age"
        assert visualisations[0]["figure_json"]["data"][0]["type"] == "histogram"

    def test_simulation_redemarrage_via_api(self, client, headers_auth, db_session, utilisateur_test):
        """Simuler un redemarrage : les donnees doivent persister en base.

        Ce test simule le scenario crucial de l'examen :
        1. Creer une session avec des messages
        2. Simuler un redemarrage (nouvelle requete)
        3. Les donnees doivent toujours etre la
        """
        reponse = client.post("/api/sessions", json={"nom": "Session Persistante"}, headers=headers_auth)
        session_id = reponse.json()["id"]

        msg = Message(session_id=session_id, role="user", contenu="Analyse ces donnees")
        db_session.add(msg)
        db_session.commit()

        msg_agent = Message(
            session_id=session_id,
            role="assistant",
            contenu="J'ai analyse les donnees. Voici les resultats.",
            metadata_msg={"intermediate_outputs": [{"thought": "Je vais analyser", "code": "print('ok')"}]},
        )
        db_session.add(msg_agent)
        db_session.commit()

        # Simuler redemarrage : relire depuis la base
        reponse = client.get(f"/api/sessions/{session_id}/messages", headers=headers_auth)
        assert reponse.status_code == 200
        messages = reponse.json()

        assert len(messages) == 2
        assert messages[0]["contenu"] == "Analyse ces donnees"
        assert messages[1]["contenu"] == "J'ai analyse les donnees. Voici les resultats."
        assert messages[1]["metadata_msg"]["intermediate_outputs"][0]["thought"] == "Je vais analyser"


class TestWorkflowComplet:
    """Tests du workflow complet d'analyse."""

    def test_workflow_session_complete(self, client, headers_auth, db_session, utilisateur_test):
        """Test du workflow : creer session -> messages -> lister -> supprimer."""
        r = client.post("/api/sessions", json={"nom": "Workflow Test"}, headers=headers_auth)
        session_id = r.json()["id"]

        for i in range(3):
            db_session.add(Message(session_id=session_id, role="user", contenu=f"Question {i}"))
            db_session.add(Message(session_id=session_id, role="assistant", contenu=f"Reponse {i}"))
        db_session.commit()

        r = client.get(f"/api/sessions/{session_id}/messages", headers=headers_auth)
        assert len(r.json()) == 6

        r = client.delete(f"/api/sessions/{session_id}", headers=headers_auth)
        assert r.status_code == 204

        r = client.get(f"/api/sessions/{session_id}", headers=headers_auth)
        assert r.status_code == 404

    def test_multiple_sessions_independantes(self, client, headers_auth, db_session, utilisateur_test):
        """Plusieurs sessions doivent etre independantes."""
        r1 = client.post("/api/sessions", json={"nom": "Session A"}, headers=headers_auth)
        r2 = client.post("/api/sessions", json={"nom": "Session B"}, headers=headers_auth)
        id_a = r1.json()["id"]
        id_b = r2.json()["id"]

        db_session.add(Message(session_id=id_a, role="user", contenu="Message A"))
        db_session.add(Message(session_id=id_b, role="user", contenu="Message B"))
        db_session.commit()

        msgs_a = client.get(f"/api/sessions/{id_a}/messages", headers=headers_auth).json()
        msgs_b = client.get(f"/api/sessions/{id_b}/messages", headers=headers_auth).json()

        assert len(msgs_a) == 1
        assert msgs_a[0]["contenu"] == "Message A"
        assert len(msgs_b) == 1
        assert msgs_b[0]["contenu"] == "Message B"
