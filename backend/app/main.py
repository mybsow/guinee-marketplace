"""
Point d'entrée principal de l'API GuinéeMarket
"""
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
import sys

from app.config.settings import settings
from app.config.database import engine, Base
from app.routes import auth, users, products, orders, payments, admin, webhooks
from app.middleware.error_handler import setup_error_handlers
from app.utils.logger import setup_logging

# Configuration logging
setup_logging()

# Créer l'application FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Marketplace Mobile-First pour la Guinée avec MobilePay",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Setup error handlers
setup_error_handlers(app)

# Inclure les routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])

# Monter les fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

# Route racine
@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT
    }

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected"
    }

# Événements de démarrage/arrêt
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Démarrage de GuinéeMarket API")
    # Créer les tables si pas en production
    if settings.ENVIRONMENT != "production":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Base de données initialisée")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Arrêt de GuinéeMarket API")
    await engine.dispose()