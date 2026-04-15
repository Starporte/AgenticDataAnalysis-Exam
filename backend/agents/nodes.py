"""Noeuds du graphe LangGraph pour l'agent d'analyse de donnees."""

import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from typing import Literal
from backend.agents.state import AgentState
from backend.agents.tools import (
    execute_data_cleaning,
    execute_visualization,
    execute_statistical_analysis,
)
from backend.config import get_settings

settings = get_settings()

# Configuration du LLM
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    api_key=settings.openai_api_key,
)

# Outils disponibles
tools = [execute_data_cleaning, execute_visualization, execute_statistical_analysis]
outils_par_nom = {t.name: t for t in tools}

model = llm.bind_tools(tools)

# Prompt systeme
PROMPT_SYSTEME = """## Role
Tu es un data scientist professionnel aidant un utilisateur non-technique a comprendre, analyser et visualiser ses donnees.

## Capacites
1. **Nettoyage de donnees** avec l'outil `execute_data_cleaning` (valeurs manquantes, doublons, conversions).
2. **Visualisations** avec l'outil `execute_visualization` (graphiques Plotly).
3. **Analyses statistiques** avec l'outil `execute_statistical_analysis` (statistiques, correlations, tests).

## Regles du code
- TOUTES LES DONNEES SONT DEJA CHARGEES, utilise les noms de variables fournis.
- LES VARIABLES PERSISTENT ENTRE LES EXECUTIONS, reutilise les variables definies precedemment.
- UTILISE `print()` pour voir les resultats. `pd.head()` seul ne montre rien.
- BIBLIOTHEQUES DISPONIBLES : pandas (pd), numpy (np), plotly.express (px), plotly.graph_objects (go), scipy.stats (stats), sklearn.
- Pour les graphiques, stocke les figures dans la liste `plotly_figures`.
- Ne jamais utiliser `fig.show()`, les figures sont sauvegardees automatiquement.

## Comportement
- Reponds en francais.
- Explique chaque etape de maniere claire et pedagogique.
- Propose des analyses pertinentes et des visualisations adaptees.
"""

chat_template = ChatPromptTemplate.from_messages([
    ("system", PROMPT_SYSTEME),
    ("placeholder", "{messages}"),
])
model_avec_prompt = chat_template | model


def creer_resume_donnees(state: AgentState) -> str:
    """Cree un resume des datasets disponibles pour le contexte de l'agent."""
    resume = ""
    for d in state.get("input_data", []):
        resume += f"\n\nVariable: {d['variable_name']}\n"
        resume += f"Description: {d.get('data_description', 'Aucune description')}"
        if d.get("columns"):
            resume += f"\nColonnes: {', '.join(d['columns'])}"

    # Ajouter les variables deja definies
    for nom_var in state.get("current_variables", {}):
        if not any(d["variable_name"] == nom_var for d in state.get("input_data", [])):
            resume += f"\n\nVariable: {nom_var}"

    return resume


def route_vers_outils(state: AgentState) -> Literal["tools", "__end__"]:
    """Decide si le dernier message necessite un appel d'outil."""
    messages = state.get("messages", [])
    if not messages:
        raise ValueError("Aucun message dans l'etat")

    dernier_message = messages[-1]
    if hasattr(dernier_message, "tool_calls") and len(dernier_message.tool_calls) > 0:
        return "tools"
    return "__end__"


def appeler_modele(state: AgentState) -> dict:
    """Noeud qui appelle le LLM avec le contexte des donnees."""
    resume = creer_resume_donnees(state)
    message_contexte = HumanMessage(
        content=f"Les donnees suivantes sont disponibles :\n{resume}"
    )
    # Inserer le contexte au debut des messages
    messages_avec_contexte = [message_contexte] + list(state["messages"])
    state_avec_contexte = {**state, "messages": messages_avec_contexte}

    reponse_llm = model_avec_prompt.invoke(state_avec_contexte)

    return {
        "messages": [reponse_llm],
        "intermediate_outputs": [message_contexte.content],
    }


def appeler_outils(state: AgentState) -> dict:
    """Noeud qui execute les appels d'outils du LLM."""
    dernier_message = state["messages"][-1]
    messages_outils = []
    mises_a_jour = {}

    if isinstance(dernier_message, AIMessage) and hasattr(dernier_message, "tool_calls"):
        for appel in dernier_message.tool_calls:
            outil = outils_par_nom[appel["name"]]
            entree = {**appel["args"], "graph_state": state}
            try:
                resultat = outil.invoke(entree)
                message_sortie, maj_etat = resultat
            except Exception as e:
                message_sortie = f"Erreur d'execution: {str(e)}"
                maj_etat = {}

            messages_outils.append(ToolMessage(
                content=str(message_sortie),
                name=appel["name"],
                tool_call_id=appel["id"],
            ))

            for cle, valeur in maj_etat.items():
                if cle == "intermediate_outputs":
                    mises_a_jour.setdefault(cle, []).extend(valeur)
                elif cle == "figures":
                    mises_a_jour.setdefault(cle, []).extend(valeur)
                else:
                    mises_a_jour[cle] = valeur

    mises_a_jour["messages"] = messages_outils
    return mises_a_jour
