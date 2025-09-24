"""
📝 Sistema de Logging - Configuración centralizada
"""
import sys
from pathlib import Path
from loguru import logger
from ..core.config import settings

def setup_logging():
    """Configurar sistema de logging"""
    
    # Crear directorio de logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Remover configuración por defecto
    logger.remove()
    
    # Configurar logging a consola
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True
    )
    
    # Configurar logging a archivo
    logger.add(
        settings.LOG_FILE,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.LOG_LEVEL,
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )
    
    logger.info("🚀 Sistema de logging inicializado")
    
    return logger