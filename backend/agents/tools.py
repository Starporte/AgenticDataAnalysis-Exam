"""Outils specialises de l'agent d'analyse de donnees."""

from langchain_core.tools import tool
from typing import Annotated, Tuple
from langgraph.prebuilt import InjectedState
import pandas as pd
from backend.security.code_sandbox import executer_code_sandbox


def _executer_outil(graph_state: dict, thought: str, python_code: str, type_outil: str) -> Tuple[str, dict]:
    """Logique commune d'execution pour les trois outils specialises."""
    # Charger les datasets dans les variables
    current_variables = graph_state.get("current_variables", {})
    datasets = {}

    for dataset_info in graph_state.get("input_data", []):
        nom_variable = dataset_info["variable_name"]
        if nom_variable not in current_variables:
            try:
                datasets[nom_variable] = pd.read_csv(dataset_info["data_path"])
            except Exception as e:
                return f"Erreur chargement dataset {nom_variable}: {e}", {
                    "intermediate_outputs": [{"thought": thought, "code": python_code, "output": str(e)}]
                }

    # Executer dans le sandbox
    resultat = executer_code_sandbox(
        code=python_code,
        variables_persistantes=current_variables,
        datasets=datasets,
        timeout=30,
    )

    # Construire la sortie
    sortie = resultat["sortie"]
    if resultat["erreur"]:
        sortie += f"\nErreur: {resultat['erreur']}"

    # Mise a jour de l'etat
    etat_maj = {
        "intermediate_outputs": [{
            "thought": thought,
            "code": python_code,
            "output": sortie,
            "type": type_outil,
        }],
        "current_variables": resultat["variables"],
    }

    if resultat["figures"]:
        etat_maj["figures"] = resultat["figures"]

    return sortie, etat_maj


@tool(parse_docstring=True)
def execute_data_cleaning(
    graph_state: Annotated[dict, InjectedState],
    thought: str,
    python_code: str,
) -> Tuple[str, dict]:
    """Nettoie et transforme les donnees : gestion des valeurs manquantes, doublons, conversions de type.

    Args:
        thought: Raisonnement interne sur l'action a effectuer, formate en MARKDOWN.
        python_code: Code Python pour le nettoyage des donnees (pandas, numpy).
    """
    return _executer_outil(graph_state, thought, python_code, "nettoyage")


@tool(parse_docstring=True)
def execute_visualization(
    graph_state: Annotated[dict, InjectedState],
    thought: str,
    python_code: str,
) -> Tuple[str, dict]:
    """Cree des visualisations Plotly : histogrammes, nuages de points, graphiques lineaires, diagrammes en barres.

    Args:
        thought: Raisonnement interne sur la visualisation a creer, formate en MARKDOWN.
        python_code: Code Python pour creer des graphiques Plotly. Stocker les figures dans plotly_figures.
    """
    return _executer_outil(graph_state, thought, python_code, "visualisation")


@tool(parse_docstring=True)
def execute_statistical_analysis(
    graph_state: Annotated[dict, InjectedState],
    thought: str,
    python_code: str,
) -> Tuple[str, dict]:
    """Effectue des analyses statistiques : statistiques descriptives, correlations, tests scipy, sklearn.

    Args:
        thought: Raisonnement interne sur l'analyse statistique a realiser, formate en MARKDOWN.
        python_code: Code Python pour l'analyse statistique (pandas, numpy, scipy, sklearn).
    """
    return _executer_outil(graph_state, thought, python_code, "statistique")
