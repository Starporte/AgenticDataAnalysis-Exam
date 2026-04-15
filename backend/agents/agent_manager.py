"""Gestionnaire de l'agent d'analyse de donnees avec persistance DB."""

from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage, AIMessage
from backend.agents.state import AgentState
from backend.agents.nodes import appeler_modele, appeler_outils, route_vers_outils


class AgentManager:
    """Gere le workflow LangGraph et la persistance des sessions."""

    def __init__(self):
        self.graph = self._creer_graphe()

    def _creer_graphe(self):
        """Cree et compile le graphe LangGraph."""
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", appeler_modele)
        workflow.add_node("tools", appeler_outils)
        workflow.add_conditional_edges("agent", route_vers_outils)
        workflow.add_edge("tools", "agent")
        workflow.set_entry_point("agent")
        return workflow.compile()

    def executer(
        self,
        historique_messages: list,
        datasets: list,
        session_id: int,
    ) -> dict:
        """
        Execute l'agent avec le contexte de la session.

        Args:
            historique_messages: Messages de la session (objets Message DB)
            datasets: Datasets disponibles (objets Dataset DB)
            session_id: ID de la session

        Returns:
            dict avec reponse, metadata et figures
        """
        # Convertir l'historique DB en messages LangChain
        messages_langchain = []
        for msg in historique_messages:
            if msg.role == "user":
                messages_langchain.append(HumanMessage(content=msg.contenu))
            elif msg.role == "assistant":
                messages_langchain.append(AIMessage(content=msg.contenu))

        # Preparer les infos des datasets
        input_data = []
        for dataset in datasets:
            input_data.append({
                "variable_name": dataset.nom_fichier.replace(".csv", ""),
                "data_path": dataset.chemin_fichier,
                "data_description": dataset.description or "",
                "columns": dataset.noms_colonnes or [],
            })

        # Etat initial du graphe
        etat_initial = {
            "messages": messages_langchain,
            "input_data": input_data,
            "intermediate_outputs": [],
            "current_variables": {},
            "figures": [],
        }

        # Executer le graphe
        try:
            resultat = self.graph.invoke(etat_initial, {"recursion_limit": 25})
        except Exception as e:
            return {
                "reponse": f"Erreur lors de l'analyse : {str(e)}",
                "metadata": {"erreur": str(e)},
                "figures": [],
            }

        # Extraire la reponse de l'agent
        reponse_agent = ""
        if resultat.get("messages"):
            for msg in reversed(resultat["messages"]):
                if isinstance(msg, AIMessage) and msg.content:
                    reponse_agent = msg.content
                    break

        if not reponse_agent:
            reponse_agent = "Je n'ai pas pu generer de reponse. Veuillez reformuler votre question."

        return {
            "reponse": reponse_agent,
            "metadata": {
                "intermediate_outputs": resultat.get("intermediate_outputs", []),
            },
            "figures": resultat.get("figures", []),
        }
