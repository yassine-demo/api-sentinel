# API Sentinel — Surveillance de disponibilité des API

**API Sentinel** est une application web légère développée en Python et Flask permettant de surveiller automatiquement la disponibilité d'API HTTP. L'application effectue des contrôles périodiques sur des endpoints configurés, mesure leurs temps de réponse, détecte les erreurs et conserve l'historique des résultats dans une base de données SQLite.

---

## Problème résolu

Dans les architectures modernes, de nombreuses applications reposent sur plusieurs API. Lorsqu'une API devient lente, retourne une erreur HTTP ou cesse totalement de répondre, les utilisateurs sont directement impactés.

**API Sentinel** permet de détecter rapidement ces problèmes grâce à une surveillance continue et centralisée des endpoints afin d'identifier les incidents avant qu'ils ne deviennent critiques pour les utilisateurs.

---

## Fonctionnalités principales

- **Gestion des endpoints (CRUD)** : ajout, consultation et suppression des API à surveiller.
- **Surveillance automatique** : exécution périodique de requêtes HTTP sur chaque endpoint.
- **Mesure des performances** : enregistrement des codes HTTP et des temps de réponse.
- **Détection des incidents** : identification des erreurs et des dépassements de seuil de latence.
- **Historique des contrôles** : conservation des résultats dans une base SQLite via SQLAlchemy.
- **Tableau de bord web** : visualisation rapide de l'état des endpoints surveillés.
- **API REST** : accès programmatique aux endpoints et aux résultats de surveillance.
- **Tests automatisés** : validation du comportement de l'application avec Pytest.

---

## Stack technique

- **Langage :** Python 3.12
- **Framework Web :** Flask
- **Base de données :** SQLite
- **ORM :** Flask-SQLAlchemy
- **Requêtes HTTP :** Requests
- **Planification des contrôles :** APScheduler
- **Interface utilisateur :** HTML5, CSS, JavaScript
- **Tests automatisés :** Pytest

---

## Structure du projet

```text
api_sentinel/
├── templates/
│   └── index.html          # Tableau de bord web
├── app.py                  # Application Flask principale
├── test_app.py             # Tests automatisés avec pytest
├── sentinel.db             # Base SQLite générée automatiquement
├── requirements.txt        # Dépendances du projet
└── README.md               # Documentation
```

---

## 🚀 Installation et exécution

### 1. Cloner le projet

```bash
git clone <URL_DE_TON_DEPOT>
cd api_sentinel
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv
```

### 3. Activer l'environnement virtuel

#### Windows PowerShell

```powershell
.\venv\Scripts\Activate.ps1
```

#### Linux / macOS

```bash
source venv/bin/activate
```

### 4. Installer les dépendances

```bash
pip install Flask Flask-SQLAlchemy requests apscheduler pytest
```

ou

```bash
pip install -r requirements.txt
```

### 5. Lancer l'application

```bash
python app.py
```

L'application sera accessible à l'adresse :

```text
http://127.0.0.1:5000
```

---

## Exécuter les tests

Pour lancer la suite de tests automatisés :

```bash
pytest
```

---

## API REST

| Méthode   | Route                 | Description                                     |
|-----------|-----------------------|-------------------------------------------------|
| GET       | `/api/endpoints`      | Retourne tous les endpoints surveillés          |
| POST      | `/api/endpoints`      | Ajoute un nouvel endpoint                       |
| DELETE    | `/api/endpoints/<id>` | Supprime un endpoint                            |
| GET       | `/api/results`        | Retourne les derniers résultats de surveillance |

---

## Exemple d'ajout d'un endpoint

### Requête

```http
POST /api/endpoints
```

```json
{
  "name": "JSONPlaceholder",
  "url": "https://jsonplaceholder.typicode.com/posts/1",
  "latency_threshold": 500
}
```

### Réponse

```json
{
  "id": 1,
  "name": "JSONPlaceholder",
  "url": "https://jsonplaceholder.typicode.com/posts/1",
  "latency_threshold": 500
}
```

---

## Exemple de surveillance

Lors de chaque contrôle, l'application enregistre :

- l'endpoint contrôlé ;
- le code de réponse HTTP ;
- le temps de réponse ;
- l'état de disponibilité ;
- la date et l'heure du contrôle.

Exemple :

| Endpoint | Status | Temps de réponse |
|-----------|---------|------------------|
| API Users | 200 | 120 ms |
| API Orders | 200 | 180 ms |
| API Payments | 500 | Erreur |

---

## Compétences démontrées

Ce projet met en pratique :

- Développement backend avec Flask
- Conception d'API REST
- Manipulation de bases de données relationnelles
- Gestion des erreurs et des exceptions
- Surveillance d'applications et métriques
- Tests automatisés avec Pytest
- Architecture logicielle orientée services

---

## Exemple de description CV

**API Sentinel — Surveillance de disponibilité des API**

Développement d'une application Flask permettant de surveiller automatiquement plusieurs endpoints HTTP, de mesurer leurs temps de réponse et de détecter les erreurs de disponibilité.

Conception d'une API REST, mise en place d'un stockage persistant avec SQLite et développement d'une suite de tests automatisés avec Pytest pour valider les principaux scénarios métier.

---

## Évolutions possibles

- Notifications par email en cas de panne
- Alertes Discord ou Slack
- Authentification des utilisateurs
- Graphiques d'évolution des performances
- Export CSV des résultats
- Historique détaillé des incidents
- Calcul automatique du taux de disponibilité (uptime)

---

Projet réalisé dans le but d'approfondir les compétences en développement backend, surveillance d'applications, bases de données, API REST et tests automatisés.