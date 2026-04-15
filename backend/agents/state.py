"""Definition de l'etat de l'agent LangGraph."""

import operator
from typing import Sequence, TypedDict, Annotated, List, Dict, Any
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """Etat partage entre les noeuds du graphe LangGraph."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    input_data: List[Dict[str, Any]]  # infos sur les datasets disponibles
    intermediate_outputs: Annotated[List[dict], operator.add]
    current_variables: dict  # variables persistantes entre executions
    figures: Annotated[List[dict], operator.add]  # figures Plotly en JSON
