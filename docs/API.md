# Documentation API - DataStream AI

Base URL : `http://localhost:8000`

Documentation interactive : `http://localhost:8000/docs`

## Authentification

Toutes les routes `/api/*` (sauf `/api/auth/register` et `/api/auth/login`) necessitent un token JWT dans le header :

```
Authorization: Bearer <votre_token>
```

---

## Endpoints d'Authentification

### POST /api/auth/register

Inscrit un nouvel utilisateur.

**Corps de la requete :**
```json
{
    "email": "utilisateur@example.com",
    "mot_de_passe": "monMotDePasse123",
    "nom": "Jean Dupont"
}
```

**Reponse 201 :**
```json
{
    "access_token": "eyJhbGciOiJIUzI1...",
    "token_type": "bearer"
}
```

**Erreur 400 :** Email deja utilise.

---

### POST /api/auth/login

Connecte un utilisateur existant.

**Corps de la requete :**
```json
{
    "email": "utilisateur@example.com",
    "mot_de_passe": "monMotDePasse123"
}
```

**Reponse 200 :**
```json
{
    "access_token": "eyJhbGciOiJIUzI1...",
    "token_type": "bearer"
}
```

**Erreur 401 :** Email ou mot de passe incorrect.

---

### GET /api/auth/me

Retourne le profil de l'utilisateur connecte.

**Reponse 200 :**
```json
{
    "id": 1,
    "email": "utilisateur@example.com",
    "nom": "Jean Dupont",
    "est_actif": true,
    "cree_le": "2025-01-15T10:30:00Z"
}
```

---

## Endpoints de Sessions

### POST /api/sessions

Cree une nouvelle session d'analyse.

**Corps de la requete :**
```json
{
    "nom": "Analyse des ventes Q1",
    "description": "Etude des tendances de vente du premier trimestre"
}
```

**Reponse 201 :**
```json
{
    "id": 1,
    "nom": "Analyse des ventes Q1",
    "description": "Etude des tendances de vente du premier trimestre",
    "nom_dataset": null,
    "cree_le": "2025-01-15T10:30:00Z",
    "mis_a_jour_le": "2025-01-15T10:30:00Z"
}
```

---

### GET /api/sessions

Liste toutes les sessions de l'utilisateur connecte.

**Reponse 200 :**
```json
{
    "sessions": [
        {
            "id": 1,
            "nom": "Analyse des ventes Q1",
            "description": "...",
            "nom_dataset": "ventes.csv",
            "cree_le": "2025-01-15T10:30:00Z",
            "mis_a_jour_le": "2025-01-15T11:00:00Z"
        }
    ]
}
```

---

### GET /api/sessions/{session_id}

Recupere une session specifique.

**Reponse 200 :** Objet session (meme format que la creation).

**Erreur 404 :** Session non trouvee ou n'appartient pas a l'utilisateur.

---

### DELETE /api/sessions/{session_id}

Supprime une session et tous ses messages/visualisations (cascade).

**Reponse 204 :** Pas de contenu.

---

## Endpoints de Chat

### GET /api/sessions/{session_id}/messages

Recupere l'historique des messages d'une session.

**Reponse 200 :**
```json
[
    {
        "id": 1,
        "role": "user",
        "contenu": "Quelles sont les colonnes du dataset ?",
        "metadata_msg": null,
        "cree_le": "2025-01-15T10:31:00Z",
        "visualisations": null
    },
    {
        "id": 2,
        "role": "assistant",
        "contenu": "Le dataset contient les colonnes suivantes : age, revenu, education...",
        "metadata_msg": {
            "intermediate_outputs": [
                {"thought": "Je vais explorer les colonnes", "code": "print(df.columns)"}
            ]
        },
        "cree_le": "2025-01-15T10:31:15Z",
        "visualisations": [
            {"id": 1, "titre": "Distribution", "figure_json": {...}}
        ]
    }
]
```

---

### POST /api/sessions/{session_id}/chat

Envoie un message a l'agent et retourne sa reponse.

**Corps de la requete :**
```json
{
    "contenu": "Cree un histogramme de la colonne age",
    "dataset_ids": [1, 2]
}
```

**Reponse 200 :**
```json
{
    "reponse": {
        "id": 5,
        "role": "assistant",
        "contenu": "Voici l'histogramme de la distribution de l'age...",
        "metadata_msg": {...},
        "cree_le": "2025-01-15T10:32:00Z",
        "visualisations": [
            {"id": 3, "titre": "Histogramme Age", "figure_json": {...}}
        ]
    },
    "visualisations": [
        {"id": 3, "titre": "Histogramme Age", "figure_json": {...}}
    ]
}
```

---

## Endpoints de Datasets

### POST /api/datasets/upload

Upload un fichier CSV.

**Requete :** `multipart/form-data`
- `fichier` : Le fichier CSV
- `description` : Description optionnelle

**Reponse 201 :**
```json
{
    "id": 1,
    "nom_fichier": "ventes.csv",
    "description": "Donnees de ventes 2024",
    "taille_octets": 15360,
    "nombre_lignes": 500,
    "nombre_colonnes": 8,
    "noms_colonnes": ["date", "produit", "quantite", "prix", ...],
    "cree_le": "2025-01-15T10:30:00Z"
}
```

---

### GET /api/datasets

Liste les datasets de l'utilisateur.

**Reponse 200 :**
```json
{
    "datasets": [
        {
            "id": 1,
            "nom_fichier": "ventes.csv",
            "description": "Donnees de ventes 2024",
            "taille_octets": 15360,
            "nombre_lignes": 500,
            "nombre_colonnes": 8,
            "noms_colonnes": ["date", "produit", ...],
            "cree_le": "2025-01-15T10:30:00Z"
        }
    ]
}
```

---

### DELETE /api/datasets/{dataset_id}

Supprime un dataset (fichier + enregistrement base).

**Reponse 204 :** Pas de contenu.

---

## Endpoints de Visualisations

### GET /api/sessions/{session_id}/visualizations

Recupere toutes les visualisations d'une session.

**Reponse 200 :**
```json
[
    {
        "id": 1,
        "titre": "Histogramme Age",
        "figure_json": {
            "data": [{"type": "histogram", "x": [20, 25, 30, ...]}],
            "layout": {"title": {"text": "Distribution de l'age"}}
        },
        "cree_le": "2025-01-15T10:32:00Z"
    }
]
```

---

## Endpoints de Sante

### GET /health

Verifie l'etat du systeme.

**Reponse 200 :**
```json
{
    "status": "healthy",
    "base_de_donnees": "ok",
    "redis": "ok"
}
```

### GET /metrics

Retourne les metriques de l'application.

**Reponse 200 :**
```json
{
    "app_info": {"version": "1.0.0", "nom": "agentic-data-analysis"},
    "status": "running"
}
```

---

## Codes d'Erreur

| Code | Signification |
|------|---------------|
| 200 | Succes |
| 201 | Ressource creee |
| 204 | Suppression reussie (pas de contenu) |
| 400 | Requete invalide (email duplique, etc.) |
| 401 | Non authentifie / Token invalide |
| 404 | Ressource non trouvee |
| 500 | Erreur interne du serveur |
