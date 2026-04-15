"""Sandbox d'execution de code Python avec globaux controles."""

import sys
from io import StringIO
import signal
import plotly.graph_objects as go
import plotly.io as pio
import plotly.express as px
import pandas as pd
import numpy as np


# Modules autorises dans le sandbox
MODULES_AUTORISES = {
    "pd": pd,
    "pandas": pd,
    "np": np,
    "numpy": np,
    "px": px,
    "go": go,
    "pio": pio,
    "plotly": __import__("plotly"),
}

# Imports bloques
IMPORTS_BLOQUES = [
    "os", "subprocess", "sys", "shutil", "socket", "http",
    "requests", "urllib", "pathlib", "glob", "signal",
    "ctypes", "importlib", "builtins", "__import__",
]


def verifier_code_securite(code: str) -> bool:
    """Verifie que le code ne contient pas d'imports dangereux."""
    lignes = code.split("\n")
    for ligne in lignes:
        ligne_nettoyee = ligne.strip()
        # Verifier les imports dangereux
        for module_bloque in IMPORTS_BLOQUES:
            if f"import {module_bloque}" in ligne_nettoyee:
                return False
            if f"from {module_bloque}" in ligne_nettoyee:
                return False
        # Verifier __import__
        if "__import__" in ligne_nettoyee:
            return False
        # Verifier open() pour lecture/ecriture de fichiers
        if "open(" in ligne_nettoyee and "pd.read_csv" not in ligne_nettoyee:
            return False
        # Verifier exec/eval imbriques
        if "exec(" in ligne_nettoyee or "eval(" in ligne_nettoyee:
            return False
    return True


def executer_code_sandbox(
    code: str,
    variables_persistantes: dict = None,
    datasets: dict = None,
    timeout: int = 30,
) -> dict:
    """
    Execute du code Python dans un environnement controle.

    Retourne un dictionnaire avec :
    - sortie : la sortie stdout
    - erreur : l'erreur eventuelle
    - variables : les variables mises a jour
    - figures : les figures Plotly generees (en JSON)
    """
    if variables_persistantes is None:
        variables_persistantes = {}
    if datasets is None:
        datasets = {}

    # Verifier la securite du code
    if not verifier_code_securite(code):
        return {
            "sortie": "",
            "erreur": "Code bloque : imports ou operations non autorises detectes. "
                      "Seuls pandas, numpy, plotly, scipy et sklearn sont autorises.",
            "variables": variables_persistantes,
            "figures": [],
        }

    # Preparer les globaux controles
    exec_globals = {
        "__builtins__": {
            "print": print,
            "len": len,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "sorted": sorted,
            "reversed": reversed,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "type": type,
            "isinstance": isinstance,
            "round": round,
            "abs": abs,
            "min": min,
            "max": max,
            "sum": sum,
            "any": any,
            "all": all,
            "hasattr": hasattr,
            "getattr": getattr,
            "setattr": setattr,
            "ValueError": ValueError,
            "TypeError": TypeError,
            "KeyError": KeyError,
            "IndexError": IndexError,
            "Exception": Exception,
            "None": None,
            "True": True,
            "False": False,
        },
    }

    # Ajouter les modules autorises
    exec_globals.update(MODULES_AUTORISES)

    # Ajouter scipy et sklearn si disponibles
    try:
        import scipy.stats as stats
        exec_globals["stats"] = stats
        exec_globals["scipy"] = __import__("scipy")
    except ImportError:
        pass

    try:
        import sklearn
        exec_globals["sklearn"] = sklearn
    except ImportError:
        pass

    # Ajouter les variables persistantes et datasets
    exec_globals.update(variables_persistantes)
    exec_globals.update(datasets)

    # Liste pour capturer les figures Plotly
    exec_globals["plotly_figures"] = []

    # Capturer stdout
    ancien_stdout = sys.stdout
    sys.stdout = StringIO()

    figures_json = []
    erreur = None
    sortie = ""

    try:
        exec(code, exec_globals)
        sortie = sys.stdout.getvalue()
    except Exception as e:
        erreur = f"{type(e).__name__}: {str(e)}"
        sortie = sys.stdout.getvalue()
    finally:
        sys.stdout = ancien_stdout

    # Extraire les figures Plotly en JSON
    if "plotly_figures" in exec_globals:
        for fig in exec_globals["plotly_figures"]:
            try:
                if hasattr(fig, "to_json"):
                    import json
                    figures_json.append(json.loads(fig.to_json()))
            except Exception:
                pass

    # Mettre a jour les variables persistantes
    variables_mises_a_jour = {}
    cles_exclues = set(MODULES_AUTORISES.keys()) | {"__builtins__", "plotly_figures", "scipy", "sklearn", "stats"}
    for cle, valeur in exec_globals.items():
        if cle not in cles_exclues and not cle.startswith("_"):
            # Ne garder que les types serializables ou DataFrames
            if isinstance(valeur, (pd.DataFrame, pd.Series, list, dict, str, int, float, bool, type(None), np.ndarray)):
                variables_mises_a_jour[cle] = valeur

    return {
        "sortie": sortie,
        "erreur": erreur,
        "variables": variables_mises_a_jour,
        "figures": figures_json,
    }
