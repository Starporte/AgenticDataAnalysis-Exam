# Preuve de Deploiement

Ce document contient les captures d'ecran prouvant le bon fonctionnement du systeme.

## 1. Docker Compose - Tous les services sains

```bash
$ docker-compose ps
```

> [CAPTURE D'ECRAN : sortie de docker-compose ps montrant tous les services "Up (healthy)"]

## 2. Page de Connexion Frontend

> [CAPTURE D'ECRAN : page de connexion Streamlit avec formulaires email/mot de passe]

URL : http://localhost:8501

## 3. Interface de Chat avec Historique de Session

> [CAPTURE D'ECRAN : interface de chat montrant l'historique d'une session chargee]

Demontre que :
- L'utilisateur est connecte (nom affiche dans la sidebar)
- Les sessions passees sont visibles dans la barre laterale
- L'historique de conversation est restaure

## 4. Documentation API (Swagger)

> [CAPTURE D'ECRAN : page /docs montrant la documentation Swagger auto-generee]

URL : http://localhost:8000/docs

## 5. Test de Persistance (Redemarrage Backend)

```bash
# Etape 1 : Creer une session et envoyer un message
# Etape 2 : Redemarrer le backend
$ docker-compose restart backend
# Etape 3 : Recharger la session - l'historique est preserve
```

> [CAPTURE D'ECRAN : session chargee apres redemarrage du backend]

## 6. Health Check

```bash
$ curl http://localhost:8000/health
```

> [CAPTURE D'ECRAN : reponse JSON {"status": "healthy", "base_de_donnees": "ok", "redis": "ok"}]
