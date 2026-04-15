"""Tests de persistance : sessions, messages, visualisations en base de donnees."""

import pytest
from backend.db.models import User, AnalysisSession, Message, Dataset, Visualization
from backend.api.auth import hasher_mot_de_passe


class TestPersistanceSession:
    """Tests de la persistance des sessions en base de donnees."""

    def test_creer_session_en_base(self, db_session, utilisateur_test):
        """Une session creee doit etre persistee en base."""
        session = AnalysisSession(
            user_id=utilisateur_test.id,
            nom="Session Test",
            description="Description de test",
        )
        db_session.add(session)
        db_session.commit()

        session_lue = db_session.query(AnalysisSession).filter_by(id=session.id).first()
        assert session_lue is not None
        assert session_lue.nom == "Session Test"
        assert session_lue.user_id == utilisateur_test.id

    def test_persistance_messages(self, db_session, utilisateur_test):
        """Les messages doivent etre persistes et lies a leur session."""
        session = AnalysisSession(user_id=utilisateur_test.id, nom="Chat Test")
        db_session.add(session)
        db_session.commit()

        msg1 = Message(session_id=session.id, role="user", contenu="Bonjour")
        msg2 = Message(session_id=session.id, role="assistant", contenu="Comment puis-je vous aider ?")
        db_session.add_all([msg1, msg2])
        db_session.commit()

        messages = db_session.query(Message).filter_by(session_id=session.id).order_by(Message.cree_le).all()
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].contenu == "Bonjour"
        assert messages[1].role == "assistant"

    def test_persistance_visualisations(self, db_session, utilisateur_test):
        """Les visualisations JSON doivent etre persistees en base."""
        session = AnalysisSession(user_id=utilisateur_test.id, nom="Viz Test")
        db_session.add(session)
        db_session.commit()

        msg = Message(session_id=session.id, role="assistant", contenu="Voici le graphique")
        db_session.add(msg)
        db_session.commit()

        figure_json = {
            "data": [{"type": "bar", "x": [1, 2, 3], "y": [4, 5, 6]}],
            "layout": {"title": {"text": "Test"}}
        }
        vis = Visualization(
            session_id=session.id,
            message_id=msg.id,
            titre="Test Bar Chart",
            figure_json=figure_json,
        )
        db_session.add(vis)
        db_session.commit()

        vis_lue = db_session.query(Visualization).filter_by(id=vis.id).first()
        assert vis_lue is not None
        assert vis_lue.figure_json["data"][0]["type"] == "bar"
        assert vis_lue.titre == "Test Bar Chart"

    def test_suppression_cascade_session(self, db_session, utilisateur_test):
        """Supprimer une session doit supprimer ses messages et visualisations."""
        session = AnalysisSession(user_id=utilisateur_test.id, nom="Cascade Test")
        db_session.add(session)
        db_session.commit()

        msg = Message(session_id=session.id, role="user", contenu="Test")
        db_session.add(msg)
        db_session.commit()

        vis = Visualization(
            session_id=session.id,
            message_id=msg.id,
            titre="Graph",
            figure_json={"data": []},
        )
        db_session.add(vis)
        db_session.commit()

        session_id = session.id
        db_session.delete(session)
        db_session.commit()

        assert db_session.query(Message).filter_by(session_id=session_id).count() == 0
        assert db_session.query(Visualization).filter_by(session_id=session_id).count() == 0

    def test_persistance_dataset(self, db_session, utilisateur_test):
        """Les datasets doivent etre persistes avec leurs metadonnees."""
        dataset = Dataset(
            user_id=utilisateur_test.id,
            nom_fichier="test.csv",
            chemin_fichier="/uploads/1/test.csv",
            description="Jeu de donnees de test",
            nombre_lignes=100,
            nombre_colonnes=5,
            noms_colonnes=["col1", "col2", "col3", "col4", "col5"],
        )
        db_session.add(dataset)
        db_session.commit()

        ds_lu = db_session.query(Dataset).filter_by(id=dataset.id).first()
        assert ds_lu is not None
        assert ds_lu.nom_fichier == "test.csv"
        assert ds_lu.nombre_lignes == 100
        assert ds_lu.noms_colonnes == ["col1", "col2", "col3", "col4", "col5"]


class TestIsolationDonneesBD:
    """Tests d'isolation des donnees au niveau base de donnees."""

    def test_sessions_isolees_par_utilisateur(self, db_session):
        """Les sessions doivent etre isolees par user_id."""
        user1 = User(email="u1@test.com", mot_de_passe_hash=hasher_mot_de_passe("mdp1"), nom="User1")
        user2 = User(email="u2@test.com", mot_de_passe_hash=hasher_mot_de_passe("mdp2"), nom="User2")
        db_session.add_all([user1, user2])
        db_session.commit()

        s1 = AnalysisSession(user_id=user1.id, nom="Session User1")
        s2 = AnalysisSession(user_id=user2.id, nom="Session User2")
        db_session.add_all([s1, s2])
        db_session.commit()

        sessions_u1 = db_session.query(AnalysisSession).filter_by(user_id=user1.id).all()
        sessions_u2 = db_session.query(AnalysisSession).filter_by(user_id=user2.id).all()

        assert len(sessions_u1) == 1
        assert sessions_u1[0].nom == "Session User1"
        assert len(sessions_u2) == 1
        assert sessions_u2[0].nom == "Session User2"

    def test_datasets_isoles_par_utilisateur(self, db_session):
        """Les datasets doivent etre isoles par user_id."""
        user1 = User(email="d1@test.com", mot_de_passe_hash=hasher_mot_de_passe("mdp1"))
        user2 = User(email="d2@test.com", mot_de_passe_hash=hasher_mot_de_passe("mdp2"))
        db_session.add_all([user1, user2])
        db_session.commit()

        ds1 = Dataset(user_id=user1.id, nom_fichier="data1.csv", chemin_fichier="/u/1/data1.csv")
        ds2 = Dataset(user_id=user2.id, nom_fichier="data2.csv", chemin_fichier="/u/2/data2.csv")
        db_session.add_all([ds1, ds2])
        db_session.commit()

        datasets_u1 = db_session.query(Dataset).filter_by(user_id=user1.id).all()
        assert len(datasets_u1) == 1
        assert datasets_u1[0].nom_fichier == "data1.csv"


class TestSimulationRedemarrage:
    """Tests de persistance simulant un redemarrage serveur."""

    def test_messages_survivent_redemarrage(self, db_session, utilisateur_test):
        """Les messages doivent survivre a un 'redemarrage' (nouvelle session DB)."""
        session = AnalysisSession(user_id=utilisateur_test.id, nom="Persistance Test")
        db_session.add(session)
        db_session.commit()
        session_id = session.id

        msg = Message(session_id=session_id, role="user", contenu="Donnees importantes")
        db_session.add(msg)
        db_session.commit()

        # Simuler un redemarrage : expulser le cache et relire
        db_session.expire_all()

        msg_relu = db_session.query(Message).filter_by(session_id=session_id).first()
        assert msg_relu is not None
        assert msg_relu.contenu == "Donnees importantes"

    def test_visualisations_survivent_redemarrage(self, db_session, utilisateur_test):
        """Les visualisations doivent survivre a un 'redemarrage'."""
        session = AnalysisSession(user_id=utilisateur_test.id, nom="Viz Persist")
        db_session.add(session)
        db_session.commit()

        vis = Visualization(
            session_id=session.id,
            titre="Mon Graphique",
            figure_json={"data": [{"type": "scatter", "x": [1], "y": [2]}]},
        )
        db_session.add(vis)
        db_session.commit()
        vis_id = vis.id

        db_session.expire_all()

        vis_relue = db_session.query(Visualization).filter_by(id=vis_id).first()
        assert vis_relue is not None
        assert vis_relue.titre == "Mon Graphique"
        assert vis_relue.figure_json["data"][0]["type"] == "scatter"
