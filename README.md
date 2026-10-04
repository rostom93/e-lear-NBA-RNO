# EduLearn — Plateforme E-Learning

Plateforme full-stack **Django REST + Angular 22** : catalogue de cours, crédits / paiements simulés, espaces étudiant / professeur / admin, chatbot d’aide, i18n FR-EN-AR et accessibilité de base.

## Stack

| Couche | Techno |
|--------|--------|
| Backend | Django 5+, DRF, SimpleJWT, SQLite, drf-spectacular, django-cors-headers |
| Frontend | Angular 22 (standalone), Signals, `inject()`, OnPush, control flow `@if/@for`, Vitest |
| Auth | JWT (email + mot de passe) |
| i18n | FR / EN / AR (RTL pour l’arabe) |

## Prérequis

- **Python 3.12+**
- **Node.js 20+** et npm
- Ports libres : `8000` (API) et `4200` (Angular). Le front est **fixé sur 4200** (`frontend/angular.json` → `serve.options.port`) : si le port est occupé, `ng serve` échoue au lieu de basculer ailleurs.

## Lancement rapide (Windows)

Une fois l’installation faite une première fois (section suivante) :

```powershell
.\start.ps1
```

Le script libère les ports `4200` et `8000` (un ancien `ng serve` resté ouvert fait
sinon échouer le démarrage avec `Port 4200 is already in use`), ouvre un terminal
par serveur, puis vérifie que les deux répondent. `Ctrl+C` dans une fenêtre arrête
le serveur correspondant.

## Installation from scratch

### 1. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows — ou : cp .env.example .env
python manage.py migrate
python manage.py seed_data
python manage.py test
python manage.py runserver
```

API : http://127.0.0.1:8000/  
Swagger : http://127.0.0.1:8000/api/schema/swagger-ui/

Variables utiles (`.env`) :

| Variable | Rôle |
|----------|------|
| `SECRET_KEY` | Clé Django |
| `DEBUG` | `True` en local (CORS permissif) |
| `ALLOWED_HOSTS` | Hôtes autorisés |
| `CORS_ALLOWED_ORIGINS` | Origines front (si `DEBUG=False`) |
| `LLM_API_KEY` / `LLM_API_URL` | Optionnel — sinon chatbot par mots-clés |

### 2. Frontend

Dans un **second** terminal :

```bash
cd frontend
npm install
npm start
```

App : http://127.0.0.1:4200/

> Le backend doit tourner (`seed_data` + `runserver`), sinon catalogue / login restent vides ou en erreur.

Configurer l’URL API si besoin : `frontend/src/environments/environment.ts` → `apiUrl: 'http://127.0.0.1:8000/api'`.

### 3. Vérifications rapides

```bash
# Backend
cd backend && python manage.py test

# Frontend
cd frontend && npx ng test --watch=false
cd frontend && npm run build

# Smoke test bout-en-bout (serveur Django démarré sur 8000)
cd backend && python smoke_test.py
```

`backend/smoke_test.py` couvre inscription, login, catalogue, achat de crédits,
cycle de vie d’un cours professeur (dont l’aperçu d’un cours inactif), KPIs admin,
chatbot et schéma OpenAPI.

## Comptes de test (`seed_data`)

| Email | Mot de passe | Rôle |
|-------|--------------|------|
| admin@platform.com | Admin123! | ADMIN |
| teacher@platform.com | Teacher123! | TEACHER |
| guest@gmail.com | Guest123! | STUDENT (500 crédits) |

Nouveaux comptes : page **Inscription** (`/auth/register`) — crée un étudiant avec 0 crédit, puis connecte automatiquement.

## Fonctionnalités par rôle

### Étudiant (`/student`)
- Catalogue filtré, détail cours, inscription (débit de crédits)
- Player : modules PDF / vidéo / quiz, progression
- Achat de packs de crédits (paiement simulé) + historique

### Professeur (`/teacher`)
- CRUD cours + modules
- **Aperçu** (`/teacher/courses/:id/preview`) : le cours rendu exactement comme les étudiants le verront (vidéo embarquée, PDF, quiz en lecture seule), y compris lorsqu’il est inactif
- Suivi des étudiants, e-mail groupé
- Quiz attachés aux modules

### Admin (`/admin`)
- KPIs (users, revenus, crédits, progression, cours populaires)
- CRUD utilisateurs / rôles
- Modération (activer / désactiver un cours)
- Historique global des transactions

### Commun
- Login JWT, thème clair/sombre, langues FR-EN-AR
- Chatbot **Aide** (bas à droite) → `POST /api/chatbot/`
- Skip-link, focus visible, labels ARIA de base

## Routes front utiles

| Route | Description |
|-------|-------------|
| `/` | Accueil |
| `/courses` | Catalogue |
| `/courses/:id` | Détail cours |
| `/auth/login` | Connexion |
| `/auth/register` | Création de compte étudiant |
| `/student` | Tableau de bord étudiant |
| `/student/credits` | Achat de crédits |
| `/student/learn/:enrollmentId` | Player |
| `/teacher` | Cours du professeur |
| `/teacher/courses/new` | Création |
| `/teacher/courses/:id/edit` | Modification |
| `/teacher/courses/:id/preview` | Aperçu vue étudiant |
| `/teacher/courses/:id/students` | Suivi + e-mail |
| `/admin` | KPIs |
| `/admin/users` | Utilisateurs |
| `/admin/moderation` | Modération cours |
| `/admin/transactions` | Transactions |

## API (aperçu)

| Méthode | URL | Notes |
|---------|-----|--------|
| POST | `/api/auth/token/` | JWT `{email,password}` |
| POST | `/api/auth/token/refresh/` | Refresh |
| POST | `/api/auth/register/` | Inscription étudiant |
| GET | `/api/auth/me/` | Profil |
| GET/POST | `/api/courses/` | Liste / création (teacher) |
| POST | `/api/courses/:id/enroll/` | Inscription |
| POST | `/api/courses/:id/toggle_active/` | Admin |
| GET | `/api/courses/:id/students/` | Teacher |
| POST | `/api/courses/:id/bulk-email/` | Teacher |
| GET | `/api/credit-packs/` | Packs |
| POST | `/api/transactions/purchase/` | Achat simulé |
| GET | `/api/admin/stats/` | KPIs admin |
| GET/POST | `/api/users/` | CRUD admin |
| POST | `/api/chatbot/` | Assistant (AllowAny) |

Documentation interactive : Swagger UI ci-dessus.

## Structure du dépôt

```text
el/
├── backend/          # Django project `config` + apps users, courses, payments, chatbot
├── frontend/         # Angular 22 (core / shared / features / layout)
└── README.md
```

## Dépannage

| Problème | Piste |
|----------|--------|
| Catalogue vide | Backend arrêté ou `seed_data` non exécuté |
| CORS | `DEBUG=True` en local, ou ajouter l’origine front dans `CORS_ALLOWED_ORIGINS` |
| `Port 4200 is already in use` | Arrêter l’ancien serveur : `npx kill-port 4200`, ou `Get-NetTCPConnection -LocalPort 4200` puis `Stop-Process -Id <pid> -Force` |
| Chatbot invisible | Recharger http://127.0.0.1:4200/ (et non un ancien `ng serve` sur un autre port) |
| Login 401 | Vérifier email/mot de passe seed ; token dans le localStorage |
| Création cours refusée | Remplir titre, description, catégorie ; URLs valides (`https://…`) |

## Hypothèses de conception

- Auth par **email** (`USERNAME_FIELD = email`).
- Quiz : `Quiz` + `QuizQuestion` + `QuizChoice`.
- Progression : `ModuleProgress` + `Enrollment.progress_percent`.
- Paiements : packs `CreditPack`, transactions `SUCCESS` / `PENDING` / `FAILED` (simulation).
- Chatbot : mots-clés par défaut ; hook LLM optionnel via env.
