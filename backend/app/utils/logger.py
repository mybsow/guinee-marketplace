"""
Configuration du logger
"""
import sys
from pathlib import Path
from loguru import logger
from app.config.settings import settings

def setup_logging():
    """Configurer le logging"""
    # Supprimer le handler par défaut
    logger.remove()
    
    # Format standard
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Console (stdout)
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.LOG_LEVEL,
        colorize=True
    )
    
    # Fichier de log
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "guinee_market_{time:YYYY-MM-DD}.log",
        format=log_format,
        level="INFO",
        rotation="00:00",  # Rotation quotidienne
        retention="30 days",
        compression="zip"
    )
    
    # Fichier d'erreurs séparé
    logger.add(
        log_dir / "errors_{time:YYYY-MM-DD}.log",
        format=log_format,
        level="ERROR",
        rotation="00:00",
        retention="90 days"
    )
    
    logger.info(f"✅ Logging configuré - Niveau: {settings.LOG_LEVEL}")