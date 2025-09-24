"""
🔧 Configuración principal del sistema
"""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # 🏢 Información del proyecto
    PROJECT_NAME: str = "Agentic AI Business Hub"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Sistema de agentes de IA para automatización empresarial"
    
    # 🌐 API Configuration
    API_HOST: str = Field(default="127.0.0.1", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # 🔐 Security
    SECRET_KEY: str = Field(
        default="your-super-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # 🗄️ Database
    DATABASE_URL: str = Field(
        default="sqlite:///./agentic_ai.db",
        env="DATABASE_URL"
    )
    
    # 🤖 AI Configuration
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    USE_OLLAMA: bool = Field(default=True, env="USE_OLLAMA")  # Usar Ollama por defecto (gratis)
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    DEFAULT_MODEL: str = Field(default="llama3.1", env="DEFAULT_MODEL")
    
    # 📊 Dashboard
    DASHBOARD_HOST: str = Field(default="127.0.0.1", env="DASHBOARD_HOST")
    DASHBOARD_PORT: int = Field(default=8501, env="DASHBOARD_PORT")
    
    # 📝 Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="logs/app.log", env="LOG_FILE")
    
    # 🔄 Task Queue (Celery)
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # 📁 File Storage
    UPLOAD_DIR: str = Field(default="uploads", env="UPLOAD_DIR")
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    
    # 🚨 Alertas
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    
    # 🌍 Environment - AGREGAMOS ESTE CAMPO
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        # IMPORTANTE: Permitir campos extra
        extra = "allow"

# 🌟 Instancia global de configuración
settings = Settings()

# 📂 Crear directorios necesarios
def create_directories():
    """Crear directorios necesarios si no existen"""
    dirs = [
        "logs",
        "uploads", 
        "uploads/documents",
        "uploads/images",
        "data",
        "data/processed",
        "data/models"
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)

# Crear directorios al importar
create_directories()

# 🎯 Configuraciones de agentes
class AgentConfig:
    """Configuración específica para agentes"""
    
    # 📄 Document Processor Agent
    DOCUMENT_PROCESSOR = {
        "name": "DocumentProcessor",
        "description": "Procesa y extrae información de documentos",
        "max_file_size": 10 * 1024 * 1024,  # 10MB
        "supported_formats": [".pdf", ".docx", ".txt", ".csv"],
        "max_processing_time": 300,  # 5 minutos
    }
    
    # 📊 Data Analyst Agent
    DATA_ANALYST = {
        "name": "DataAnalyst", 
        "description": "Analiza datos y genera insights",
        "max_data_points": 100000,
        "chart_types": ["line", "bar", "scatter", "pie", "heatmap"],
        "analysis_timeout": 180,  # 3 minutos
    }
    
    # 🎯 Customer Service Agent
    CUSTOMER_SERVICE = {
        "name": "CustomerService",
        "description": "Agente de atención al cliente",
        "max_conversation_length": 50,
        "escalation_threshold": 3,  # Número de "no sé" antes de escalar
        "response_timeout": 30,  # 30 segundos
    }
    
    # 🔍 Monitor Agent
    MONITOR = {
        "name": "SystemMonitor",
        "description": "Monitorea sistemas y procesos", 
        "check_interval": 60,  # 1 minuto
        "alert_threshold": 0.8,  # 80% CPU/memoria
        "max_alerts_per_hour": 10,
    }

# 🎨 Configuración del Dashboard
class DashboardConfig:
    """Configuración del dashboard Streamlit"""
    
    PAGE_CONFIG = {
        "page_title": "🤖 Agentic AI Hub",
        "page_icon": "🚀",
        "layout": "wide",
        "initial_sidebar_state": "expanded"
    }
    
    THEME = {
        "primaryColor": "#FF6B6B",
        "backgroundColor": "#FFFFFF", 
        "secondaryBackgroundColor": "#F0F2F6",
        "textColor": "#262730",
        "font": "sans serif"
    }
    
    CHART_COLORS = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", 
        "#96CEB4", "#FFEAA7", "#DDA0DD"
    ]

# 🚀 Funciones de utilidad para configuración
def get_ai_provider():
    """Determinar qué proveedor de IA usar"""
    if settings.USE_OLLAMA:
        return "ollama"
    elif settings.OPENAI_API_KEY:
        return "openai"
    else:
        return "mock"  # Para desarrollo sin IA real

def get_database_type():
    """Determinar tipo de base de datos"""
    if "postgresql" in settings.DATABASE_URL.lower():
        return "postgresql"
    elif "mysql" in settings.DATABASE_URL.lower():
        return "mysql"
    else:
        return "sqlite"

# 🎯 Exportar configuraciones
__all__ = [
    "settings",
    "AgentConfig", 
    "DashboardConfig",
    "get_ai_provider",
    "get_database_type"
]