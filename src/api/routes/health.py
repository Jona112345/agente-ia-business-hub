"""
🔧 Health Routes - Estado y salud del sistema
"""
from datetime import datetime
from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()

@router.get("/")
async def health_check():
    """Verificación básica de salud del sistema"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Agentic AI Hub",
        "version": "1.0.0"
    }

@router.get("/status")
async def system_status():
    """Estado detallado del sistema"""
    return {
        "status": "online",
        "services": {
            "api": "running",
            "agents": "active",
            "database": "connected"
        },
        "timestamp": datetime.now().isoformat(),
        "uptime": "running"
    }

@router.get("/ping")
async def ping():
    """Ping simple para verificar conectividad"""
    return {"message": "pong"}