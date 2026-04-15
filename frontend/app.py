"""Point d'entree du frontend Streamlit avec authentification."""

import os
import sys

os.environ["STREAMLIT_SERVER_MAX_UPLOAD_SIZE"] = "2000"

# Ajouter le repertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="DataStream AI - Analyse de Donnees",
    page_icon="📊",
)

from frontend.utils.api_client import get_api_client

api = get_api_client()


def page_connexion():
    """Page de connexion / inscription."""
    st.title("📊 DataStream AI")
    st.subheader("Plateforme d'Analyse de Donnees Agentique")

    onglet_connexion, onglet_inscription = st.tabs(["Connexion", "Inscription"])

    with onglet_connexion:
        with st.form("formulaire_connexion"):
            email = st.text_input("Email", key="login_email")
            mot_de_passe = st.text_input("Mot de passe", type="password", key="login_mdp")
            soumis = st.form_submit_button("Se connecter", use_container_width=True)

            if soumis and email and mot_de_passe:
                try:
                    api.connexion(email, mot_de_passe)
                    utilisateur = api.profil()
                    st.session_state["utilisateur"] = utilisateur
                    st.success("Connexion reussie !")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    with onglet_inscription:
        with st.form("formulaire_inscription"):
            nom = st.text_input("Nom", key="register_nom")
            email = st.text_input("Email", key="register_email")
            mot_de_passe = st.text_input("Mot de passe", type="password", key="register_mdp")
            confirmation = st.text_input("Confirmer le mot de passe", type="password", key="register_confirm")
            soumis = st.form_submit_button("S'inscrire", use_container_width=True)

            if soumis:
                if not email or not mot_de_passe:
                    st.error("Email et mot de passe requis")
                elif mot_de_passe != confirmation:
                    st.error("Les mots de passe ne correspondent pas")
                elif len(mot_de_passe) < 6:
                    st.error("Le mot de passe doit contenir au moins 6 caracteres")
                else:
                    try:
                        api.inscription(email, mot_de_passe, nom)
                        utilisateur = api.profil()
                        st.session_state["utilisateur"] = utilisateur
                        st.success("Inscription reussie !")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))


def barre_laterale():
    """Barre laterale avec gestion des sessions et deconnexion."""
    utilisateur = st.session_state.get("utilisateur", {})

    with st.sidebar:
        st.write(f"**{utilisateur.get('nom', utilisateur.get('email', 'Utilisateur'))}**")

        if st.button("Deconnexion", use_container_width=True):
            for cle in list(st.session_state.keys()):
                del st.session_state[cle]
            st.rerun()

        st.divider()
        st.subheader("Sessions d'analyse")

        # Bouton nouvelle session
        if st.button("+ Nouvelle session", use_container_width=True):
            try:
                nouvelle = api.creer_session()
                st.session_state["session_active_id"] = nouvelle["id"]
                st.session_state.pop("messages_cache", None)
                st.rerun()
            except Exception as e:
                st.error(str(e))

        # Liste des sessions
        try:
            sessions = api.lister_sessions()
            for session in sessions:
                nom_affiche = session["nom"]
                if session.get("nom_dataset"):
                    nom_affiche += f" ({session['nom_dataset']})"

                est_active = st.session_state.get("session_active_id") == session["id"]
                type_bouton = "primary" if est_active else "secondary"

                if st.button(
                    f"{'▶ ' if est_active else ''}{nom_affiche}",
                    key=f"session_{session['id']}",
                    use_container_width=True,
                    type=type_bouton,
                ):
                    st.session_state["session_active_id"] = session["id"]
                    st.session_state.pop("messages_cache", None)
                    st.rerun()

        except Exception as e:
            st.error(f"Erreur chargement sessions: {e}")


def page_analyse():
    """Page principale d'analyse de donnees."""
    import plotly.io as pio

    barre_laterale()

    session_id = st.session_state.get("session_active_id")

    if not session_id:
        st.title("📊 DataStream AI")
        st.info("Creez ou selectionnez une session d'analyse dans la barre laterale.")
        return

    # Onglets principaux
    tab_donnees, tab_chat, tab_debug = st.tabs(["Gestion des donnees", "Chat", "Debug"])

    with tab_donnees:
        st.subheader("Upload de datasets")
        fichier = st.file_uploader("Choisir un fichier CSV", type="csv")
        description = st.text_input("Description du dataset (optionnel)")

        if fichier and st.button("Uploader"):
            try:
                resultat = api.uploader_dataset(fichier, description)
                st.success(f"Dataset '{resultat['nom_fichier']}' uploade avec succes !")
                st.rerun()
            except Exception as e:
                st.error(str(e))

        # Liste des datasets
        st.subheader("Mes datasets")
        try:
            datasets = api.lister_datasets()
            if datasets:
                for ds in datasets:
                    with st.expander(f"📄 {ds['nom_fichier']} ({ds.get('nombre_lignes', '?')} lignes)"):
                        if ds.get("description"):
                            st.write(f"**Description:** {ds['description']}")
                        if ds.get("noms_colonnes"):
                            st.write(f"**Colonnes:** {', '.join(ds['noms_colonnes'])}")
                        st.write(f"**Taille:** {ds.get('taille_octets', 0) / 1024:.1f} Ko")
            else:
                st.info("Aucun dataset uploade. Uploadez un fichier CSV ci-dessus.")
        except Exception as e:
            st.error(str(e))

    with tab_chat:
        # Charger les messages de la session
        try:
            messages = api.lister_messages(session_id)
        except Exception:
            messages = []

        # Afficher l'historique
        conteneur_chat = st.container(height=500)
        with conteneur_chat:
            for msg in messages:
                if msg["role"] == "user":
                    st.chat_message("user").markdown(msg["contenu"])
                elif msg["role"] == "assistant":
                    with st.chat_message("assistant"):
                        st.markdown(msg["contenu"])
                        # Afficher les visualisations associees
                        if msg.get("visualisations"):
                            for vis in msg["visualisations"]:
                                try:
                                    fig = pio.from_json(str(vis["figure_json"]).replace("'", '"'))
                                    st.plotly_chart(fig, use_container_width=True)
                                except Exception:
                                    try:
                                        import plotly.graph_objects as go_fig
                                        fig = go_fig.Figure(vis["figure_json"])
                                        st.plotly_chart(fig, use_container_width=True)
                                    except Exception:
                                        pass

        # Champ de saisie
        question = st.chat_input("Posez une question sur vos donnees...")
        if question:
            # Recuperer les IDs des datasets
            try:
                datasets = api.lister_datasets()
                dataset_ids = [ds["id"] for ds in datasets]
            except Exception:
                dataset_ids = []

            with st.spinner("L'agent analyse vos donnees..."):
                try:
                    resultat = api.envoyer_message(session_id, question, dataset_ids)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur: {e}")

    with tab_debug:
        st.subheader("Informations de debug")
        if messages:
            for i, msg in enumerate(messages):
                if msg.get("metadata_msg") and msg["metadata_msg"].get("intermediate_outputs"):
                    for j, sortie in enumerate(msg["metadata_msg"]["intermediate_outputs"]):
                        with st.expander(f"Etape {i+1}.{j+1}"):
                            if isinstance(sortie, dict):
                                if "thought" in sortie:
                                    st.markdown("### Raisonnement")
                                    st.markdown(sortie["thought"])
                                if "code" in sortie:
                                    st.markdown("### Code")
                                    st.code(sortie["code"], language="python")
                                if "output" in sortie:
                                    st.markdown("### Sortie")
                                    st.text(sortie["output"])
                            else:
                                st.text(str(sortie))
        else:
            st.info("Aucune donnee de debug. Commencez une conversation pour voir les sorties intermediaires.")


# --- Logique principale ---
def main():
    if st.session_state.get("jwt_token"):
        # Verifier que le token est valide
        try:
            if "utilisateur" not in st.session_state:
                utilisateur = api.profil()
                st.session_state["utilisateur"] = utilisateur
            page_analyse()
        except Exception:
            st.session_state.pop("jwt_token", None)
            st.session_state.pop("utilisateur", None)
            page_connexion()
    else:
        page_connexion()


if __name__ == "__main__":
    main()
else:
    main()
