# GuinéeMarket 🇬🇳

Plateforme marketplace mobile-first pour la Guinée avec intégration MobilePay.

## 🚀 Stack Technique

- **Backend**: Python 3.11+ / FastAPI / SQLAlchemy
- **Base de données**: PostgreSQL + Redis
- **Frontend**: HTML5 / CSS3 / JavaScript (Vanilla)
- **Mobile**: PWA (Progressive Web App)
- **Paiement**: MobilePay Guinée API
- **Déploiement**: Docker

## 📦 Installation

```bash
# Cloner le repo
git clone https://github.com/votre-org/guinee-marketplace.git
cd guinee-marketplace

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sur Windows
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos configurations

# Lancer les migrations
alembic upgrade head

# Lancer le serveur
python run.py
