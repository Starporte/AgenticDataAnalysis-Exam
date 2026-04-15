# Preuve de Deploiement

Ce document contient les preuves du bon fonctionnement du systeme.

## 1. Docker Compose - Tous les services sains

```
NAMES                      STATUS                    PORTS
datastream_frontend        Up 8 minutes (healthy)    0.0.0.0:8501->8501/tcp
datastream_backend         Up 8 minutes (healthy)    0.0.0.0:8000->8000/tcp
datastream_celery_worker   Up 22 minutes
datastream_flower          Up 55 minutes             0.0.0.0:5555->5555/tcp
datastream_postgres        Up 55 minutes (healthy)   0.0.0.0:5433->5432/tcp
datastream_redis           Up 55 minutes (healthy)   0.0.0.0:6379->6379/tcp
```

Sortie complete : [docker-compose-ps.txt](docs/screenshots/docker-compose-ps.txt)

## 2. Page de Connexion Frontend

![Page de connexion](docs/screenshots/page-connexion.png)

URL : http://localhost:8501

## 3. Interface de Chat avec Historique de Session

![Interface de chat](docs/screenshots/chat-historique.png)

## 4. Documentation API (Swagger)

![Documentation API](docs/screenshots/swagger-docs.png)

URL : http://localhost:8000/docs

## 5. Test de Persistance (Redemarrage Backend)

```
=== TEST DE PERSISTANCE ===

--- Connexion ---
Login: {"access_token":"eyJhbGciOiJIUzI1NiIs..."}

--- Sessions apres restart ---
{"sessions":[{"id":1,"nom":"Analyse de test","description":"Session pour tester la persistance",...}]}

--- Messages session 1 apres restart ---
2 messages preserves apres restart
  [user] Quelles sont les colonnes du dataset ?
  [assistant] Erreur lors de l'analyse : Error code: 429 ...
```

Les messages sont intacts apres `docker-compose restart backend`.

Sortie complete : [test-persistance.txt](docs/screenshots/test-persistance.txt)

## 6. Health Check

```json
{"status":"healthy","base_de_donnees":"ok","redis":"ok"}
```

Sortie complete : [health-check.txt](docs/screenshots/health-check.txt)
