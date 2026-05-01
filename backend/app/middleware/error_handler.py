"""
Gestionnaire d'erreurs global
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger
import traceback
from typing import Union

class AppException(Exception):
    """Exception personnalisée de l'application"""
    def __init__(self, message: str, status_code: int = 400, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

def setup_error_handlers(app: FastAPI):
    """Configurer les gestionnaires d'erreurs"""
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """Gérer les exceptions métier"""
        logger.warning(f"AppException: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "message": exc.message,
                "details": exc.details
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Gérer les exceptions HTTP"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "message": exc.detail,
                "status_code": exc.status_code
            }
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        """Gérer les erreurs de base de données"""
        logger.error(f"Erreur DB: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "message": "Erreur de base de données"
            }
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Gérer les erreurs de validation"""
        return JSONResponse(
            status_code=400,
            content={
                "error": True,
                "message": str(exc)
            }
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Gérer toutes les autres exceptions"""
        logger.error(f"Exception non gérée: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "message": "Erreur interne du serveur"
            }
        )