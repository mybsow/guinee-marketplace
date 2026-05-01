#!/bin/bash
# Script de déploiement GuinéeMarket

echo "🚀 Déploiement GuinéeMarket..."

# Variables
ENV=${1:-production}
BRANCH=${2:-main}

echo "Environnement: $ENV"
echo "Branche: $BRANCH"

# Pull latest code
git checkout $BRANCH
git pull origin $BRANCH

# Backend
cd backend
echo "📦 Installation dépendances backend..."
pip install -r requirements.txt

echo "🗄️ Migrations base de données..."
alembic upgrade head

# Frontend
cd ../frontend
echo "🎨 Build frontend..."
# Minifier les assets si nécessaire

# Docker
cd ..
echo "🐳 Build Docker..."
docker-compose build

echo "🔄 Redémarrage services..."
docker-compose down
docker-compose up -d

echo "✅ Déploiement terminé!"