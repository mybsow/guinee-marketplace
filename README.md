# GuinéeMarket 🇬🇳

Plateforme marketplace mobile-first pour la Guinée avec paiement sécurisé MobilePay.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![Licence](https://img.shields.io/badge/licence-MIT-yellow)

---

## 📱 Workflow MobilePay

```
Client commande → Paie via MobilePay → Fond séquestré
→ Marchand livre → Client confirme réception
→ Paiement libéré au marchand (- commission)
```

---

## 🚀 Stack Technique

| Composant | Technologie |
|-----------|------------|
| **Backend** | Python 3.11+ / FastAPI / SQLAlchemy |
| **Base de données** | PostgreSQL 15 + Redis 7 |
| **Frontend** | HTML5 / CSS3 / JavaScript (Vanilla) |
| **Mobile** | PWA (Progressive Web App) |
| **Paiement** | MobilePay Guinée API |
| **Notifications** | SMS (Orange Guinée) |
| **Déploiement** | Docker + Nginx |

---

## 📦 Installation

### Prérequis
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optionnel)

### Méthode 1 : Docker (Recommandé)

```bash
# Cloner le repo
git clone https://github.com/votre-org/guinee-marketplace.git
cd guinee-marketplace

# Configurer l'environnement
cp .env.example .env
nano .env  # Renseigner les vraies valeurs

# Lancer tous les services
docker-compose up -d

# Accéder à l'application
# Frontend : http://localhost
# API Docs : http://localhost:8000/api/docs
# Admin    : http://localhost/admin
```

### Méthode 2 : Développement local

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

pip install -r requirements.txt

# Configurer les variables d'environnement
cp ../.env.example ../.env
# Éditer .env avec vos configurations

# Lancer les migrations
alembic upgrade head

# Données de test (optionnel)
python ../scripts/seed_data.py

# Lancer le serveur
python run.py

# Dans un autre terminal, lancer Redis
redis-server
```

---

## 📁 Structure du projet

```
guinee-marketplace/
├── backend/                # API FastAPI
│   ├── app/
│   │   ├── config/        # Configuration
│   │   ├── models/        # Modèles SQLAlchemy
│   │   ├── schemas/       # Validation Pydantic
│   │   ├── routes/        # Endpoints API
│   │   ├── services/      # Logique métier
│   │   ├── integrations/  # API MobilePay, SMS
│   │   ├── middleware/     # Auth, Rate limiting
│   │   └── utils/         # Helpers
│   ├── tests/
│   ├── alembic/           # Migrations DB
│   └── requirements.txt
│
├── frontend/              # Interface utilisateur
│   ├── templates/         # Pages HTML
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── components/
│
├── admin/                 # Dashboard administration
│
├── docs/                  # Documentation
│   ├── API.md
│   └── ARCHITECTURE.md
│
├── scripts/               # Utilitaires
│   ├── seed_data.py
│   └── deploy.sh
│
├── docker-compose.yml
├── nginx.conf
├── .env.example
└── README.md
```

---

## 🔑 Variables d'environnement principales

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Connexion PostgreSQL |
| `REDIS_URL` | Connexion Redis |
| `SECRET_KEY` | Clé secrète application |
| `JWT_SECRET_KEY` | Clé JWT |
| `MOBILEPAY_API_KEY` | Clé API MobilePay |
| `MOBILEPAY_API_SECRET` | Secret API MobilePay |
| `MOBILEPAY_MERCHANT_ID` | ID Marchand MobilePay |
| `SMS_API_KEY` | Clé API SMS Orange |

---

## 🧪 Tests

```bash
cd backend

# Lancer tous les tests
pytest

# Avec couverture
pytest --cov=app --cov-report=html

# Tests spécifiques
pytest tests/test_payments.py -v
```

---

## 📡 API Endpoints principaux

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/auth/register` | Inscription |
| `POST` | `/api/auth/login` | Connexion |
| `GET` | `/api/products` | Liste annonces |
| `POST` | `/api/orders` | Créer commande |
| `POST` | `/api/payments/initiate` | Initier paiement MobilePay |
| `POST` | `/api/orders/{id}/confirm-delivery` | **Confirmer livraison → Libérer paiement** |
| `GET` | `/api/admin/dashboard` | Stats administrateur |

---

## 🔒 Sécurité

- Mots de passe hashés (bcrypt)
- Authentification JWT
- Vérification téléphone obligatoire
- Séquestre des fonds (paiement libéré après livraison)
- Rate limiting sur endpoints sensibles
- Validation KYC pour les marchands

---

## 🚀 Déploiement

```bash
# Production
docker-compose up -d

# Mise à jour
git pull
docker-compose build backend
docker-compose up -d --no-deps backend
```

---

## 📄 Licence

MIT © 2025 GuinéeMarket

[Politique de confidentialité](PRIVACY.md)
