# Guide d'Installation et de Deploiement

## Prerequis

- Docker et Docker Compose (v2.0+)
- Python 3.11+
- Git

## Installation - Developpement Local

### 1. Cloner le Depot

```bash
git clone <url-du-depot>
cd AgenticDataAnalysis-Exam
```

### 2. Configuration de l'Environnement

```bash
cp .env.example .env
```

Editez `.env` avec vos cles API :

```env
OPENAI_API_KEY=sk-votre-cle-openai
SECRET_KEY=une-cle-aleatoire-de-production
```

### 3. Demarrer les Services avec Docker Compose

```bash
docker-compose up -d
```

Cette commande demarre automatiquement :
- **PostgreSQL** (port 5432) : Base de donnees principale
- **Redis** (port 6379) : Broker de messages Celery
- **Backend FastAPI** (port 8000) : API REST
- **Frontend Streamlit** (port 8501) : Interface utilisateur
- **Celery Worker** : Execution asynchrone des taches
- **Flower** (port 5555) : Monitoring Celery

### 4. Verifier le Deploiement

```bash
# Verifier que tous les services sont sains
docker-compose ps

# Tester le health check
curl http://localhost:8000/health
```

### 5. Executer les Migrations (automatique au demarrage)

Les tables sont creees automatiquement au demarrage du backend. Pour les migrations manuelles :

```bash
docker-compose exec backend alembic upgrade head
```

### 6. Acceder a l'Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:8501 |
| Backend API | http://localhost:8000 |
| Documentation API (Swagger) | http://localhost:8000/docs |
| Documentation API (ReDoc) | http://localhost:8000/redoc |
| Flower (Monitoring Celery) | http://localhost:5555 |

## Installation sans Docker (Developpement)

### 1. Creer un environnement virtuel

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 2. Installer les dependances

```bash
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### 3. Demarrer PostgreSQL et Redis

```bash
# Avec Docker (services uniquement)
docker run -d --name postgres -e POSTGRES_DB=datastream -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:15-alpine
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

### 4. Demarrer le Backend

```bash
uvicorn backend.api.main:app --reload --port 8000
```

### 5. Demarrer le Frontend

```bash
streamlit run frontend/app.py --server.port=8501
```

### 6. Demarrer Celery (optionnel)

```bash
celery -A backend.tasks.celery_app worker --loglevel=info
```

## Executer les Tests

```bash
# Avec Docker
docker-compose exec backend pytest -v

# En local
pytest backend/tests/ -v --cov=backend --cov-report=term
```

## Commandes Utiles

```bash
# Redemarrer le backend (test de persistance)
docker-compose restart backend

# Voir les logs
docker-compose logs -f backend

# Scaler le backend
docker-compose up --scale backend=3 -d

# Arreter tous les services
docker-compose down

# Arreter et supprimer les donnees
docker-compose down -v
```

## Variables d'Environnement

| Variable | Description | Defaut |
|----------|-------------|--------|
| `OPENAI_API_KEY` | Cle API OpenAI | (requis) |
| `DATABASE_URL` | URL PostgreSQL | `postgresql://postgres:postgres@localhost:5432/datastream` |
| `REDIS_URL` | URL Redis | `redis://localhost:6379/0` |
| `SECRET_KEY` | Cle secrete JWT | (requis en production) |
| `ORIGINES_AUTORISEES` | Origines CORS | `http://localhost:8501` |
