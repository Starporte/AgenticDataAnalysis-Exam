"""Tests de securite : sandbox d'execution de code et protection API."""

import pytest
from backend.security.code_sandbox import executer_code_sandbox, verifier_code_securite


class TestVerificationCode:
    """Tests de la verification statique du code."""

    def test_code_python_normal_accepte(self):
        """Du code pandas/plotly normal doit etre accepte."""
        code = "df = pd.DataFrame({'a': [1, 2, 3]})\nprint(df.describe())"
        assert verifier_code_securite(code) is True

    def test_import_os_bloque(self):
        """L'import de os doit etre bloque."""
        assert verifier_code_securite("import os") is False

    def test_import_subprocess_bloque(self):
        """L'import de subprocess doit etre bloque."""
        assert verifier_code_securite("import subprocess") is False

    def test_from_os_import_bloque(self):
        """from os import ... doit etre bloque."""
        assert verifier_code_securite("from os import system") is False

    def test_dunder_import_bloque(self):
        """__import__ doit etre bloque."""
        assert verifier_code_securite("__import__('os')") is False

    def test_open_bloque(self):
        """open() direct doit etre bloque."""
        assert verifier_code_securite("f = open('/etc/passwd')") is False

    def test_exec_imbrique_bloque(self):
        """exec() imbrique doit etre bloque."""
        assert verifier_code_securite("exec('print(1)')") is False

    def test_eval_bloque(self):
        """eval() doit etre bloque."""
        assert verifier_code_securite("eval('1+1')") is False

    def test_import_requests_bloque(self):
        """L'import de requests doit etre bloque."""
        assert verifier_code_securite("import requests") is False

    def test_import_socket_bloque(self):
        """L'import de socket doit etre bloque."""
        assert verifier_code_securite("import socket") is False


class TestExecutionSandbox:
    """Tests de l'execution sandbox."""

    def test_execution_simple(self):
        """Du code simple doit s'executer correctement."""
        resultat = executer_code_sandbox("print('hello')")
        assert resultat["erreur"] is None
        assert "hello" in resultat["sortie"]

    def test_execution_pandas(self):
        """Les operations pandas doivent fonctionner."""
        code = "df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})\nprint(df.shape)"
        resultat = executer_code_sandbox(code)
        assert resultat["erreur"] is None
        assert "(3, 2)" in resultat["sortie"]

    def test_execution_numpy(self):
        """Les operations numpy doivent fonctionner."""
        code = "print(np.mean([1, 2, 3, 4, 5]))"
        resultat = executer_code_sandbox(code)
        assert resultat["erreur"] is None
        assert "3.0" in resultat["sortie"]

    def test_execution_plotly(self):
        """Les figures Plotly doivent etre capturees."""
        code = "fig = px.bar(x=[1, 2, 3], y=[4, 5, 6])\nplotly_figures.append(fig)"
        resultat = executer_code_sandbox(code)
        assert resultat["erreur"] is None
        assert len(resultat["figures"]) == 1

    def test_code_malveillant_os_bloque(self):
        """Le code tentant d'acceder au systeme doit etre bloque."""
        code = "__import__('os').system('echo HACKED')"
        resultat = executer_code_sandbox(code)
        assert resultat["erreur"] is not None
        assert "bloque" in resultat["erreur"].lower() or "autorise" in resultat["erreur"].lower()

    def test_code_malveillant_subprocess_bloque(self):
        """subprocess doit etre bloque."""
        code = "import subprocess\nsubprocess.run(['ls'])"
        resultat = executer_code_sandbox(code)
        assert resultat["erreur"] is not None

    def test_code_malveillant_lecture_fichier_bloque(self):
        """La lecture de fichiers systeme doit etre bloquee."""
        code = "f = open('/etc/passwd', 'r')\nprint(f.read())"
        resultat = executer_code_sandbox(code)
        assert resultat["erreur"] is not None

    def test_variables_persistantes(self):
        """Les variables doivent persister entre executions."""
        resultat1 = executer_code_sandbox("x = 42")
        assert resultat1["erreur"] is None

        resultat2 = executer_code_sandbox(
            "print(x)",
            variables_persistantes=resultat1["variables"]
        )
        assert resultat2["erreur"] is None
        assert "42" in resultat2["sortie"]

    def test_datasets_injectes(self):
        """Les datasets doivent etre accessibles dans le sandbox."""
        import pandas as pd_test
        df = pd_test.DataFrame({"col1": [1, 2, 3]})
        resultat = executer_code_sandbox(
            "print(mon_dataset.shape)",
            datasets={"mon_dataset": df}
        )
        assert resultat["erreur"] is None
        assert "(3, 1)" in resultat["sortie"]

    def test_erreur_runtime_capturee(self):
        """Les erreurs d'execution doivent etre capturees proprement."""
        resultat = executer_code_sandbox("x = 1 / 0")
        assert resultat["erreur"] is not None
        assert "ZeroDivision" in resultat["erreur"]


class TestSecuriteAPI:
    """Tests de securite au niveau API."""

    def test_injection_sql_bloquee(self, client, headers_auth):
        """Les tentatives d'injection SQL doivent etre gerees par l'ORM."""
        reponse = client.post("/api/sessions", json={
            "nom": "Robert'); DROP TABLE users;--",
        }, headers=headers_auth)
        # L'ORM protege contre l'injection SQL, la requete doit reussir
        assert reponse.status_code == 201
        # La table users doit toujours exister
        reponse = client.get("/api/auth/me", headers=headers_auth)
        assert reponse.status_code == 200

    def test_token_expire_refuse(self, client):
        """Un token invalide/expire doit etre refuse."""
        headers = {"Authorization": "Bearer token_completement_invalide"}
        reponse = client.get("/api/sessions", headers=headers)
        assert reponse.status_code == 401

    def test_pas_de_secrets_dans_erreurs(self, client):
        """Les erreurs ne doivent pas exposer de stack traces."""
        reponse = client.get("/api/sessions/not_a_number", headers={
            "Authorization": "Bearer fake"
        })
        # Verifier qu'aucune stack trace n'est exposee
        texte = reponse.text.lower()
        assert "traceback" not in texte
        assert "file \"/" not in texte
