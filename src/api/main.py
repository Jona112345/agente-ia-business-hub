"""
🚀 API Principal - FastAPI Application
Sistema de Agentes de IA para Automatización Empresarial

El punto de entrada de la API con los endpoints principales
"""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Imports locales
from ..core.config import settings, DashboardConfig
from ..core.registry import agent_registry, register_agent
from ..agents.base_agent import AgentFactory
from ..agents.document_processor import DocumentProcessorAgent
from ..services.ai_service import ai_service
from ..utils.logger import setup_logging

# Imports de rutas
from .routes.agents import router as agents_router
from .routes.tasks import router as tasks_router
from .routes.health import router as health_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    
    # 🚀 Startup
    setup_logging()
    
    # Inicializar agentes por defecto
    await initialize_default_agents()
    
    print("🤖 Agentic AI Hub API iniciada")
    print(f"📊 Dashboard disponible en: http://{settings.DASHBOARD_HOST}:{settings.DASHBOARD_PORT}")
    print(f"📚 Docs disponibles en: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    
    yield
    
    # 🛑 Shutdown
    await shutdown_agents()
    print("👋 Agentic AI Hub API detenida")

# 🌟 Crear aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "agents",
            "description": "Gestión de agentes de IA",
        },
        {
            "name": "tasks", 
            "description": "Gestión de tareas y trabajos",
        },
        {
            "name": "health",
            "description": "Estado y salud del sistema",
        },
        {
            "name": "ai",
            "description": "Servicios de inteligencia artificial",
        }
    ]
)

# 🌐 Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📁 Servir archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 🛣️ Incluir routers
app.include_router(agents_router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(tasks_router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(health_router, prefix="/api/v1/health", tags=["health"])

# 🏠 Rutas principales
@app.get("/", response_model=Dict[str, Any])
async def root():
    """Endpoint raíz con información del sistema"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "docs": "/docs",
            "agents": "/api/v1/agents",
            "tasks": "/api/v1/tasks", 
            "health": "/api/v1/health",
            "dashboard": f"http://{settings.DASHBOARD_HOST}:{settings.DASHBOARD_PORT}"
        },
        "agent_count": len(agent_registry),
        "ai_provider": ai_service.provider
    }

# 🤖 Rutas de IA directas
@app.post("/api/v1/ai/generate", tags=["ai"])
async def generate_text(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """Generar texto usando IA"""
    try:
        prompt = request.get("prompt")
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt es requerido")
        
        model = request.get("model")
        max_tokens = request.get("max_tokens", 1000)
        temperature = request.get("temperature", 0.7)
        system_prompt = request.get("system_prompt")
        
        response = await ai_service.generate_text(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt
        )
        
        return {
            "success": True,
            "response": response,
            "metadata": {
                "prompt_length": len(prompt),
                "response_length": len(response),
                "model": model or "default",
                "provider": ai_service.provider
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ai/analyze", tags=["ai"])
async def analyze_text(request: Dict[str, Any]):
    """Analizar texto con IA"""
    try:
        text = request.get("text")
        if not text:
            raise HTTPException(status_code=400, detail="Texto es requerido")
        
        analysis_type = request.get("type", "general")
        
        result = await ai_service.analyze_text(text, analysis_type)
        
        return {
            "success": True,
            "analysis": result,
            "metadata": {
                "text_length": len(text),
                "analysis_type": analysis_type,
                "provider": ai_service.provider
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 📊 Rutas de estadísticas
@app.get("/api/v1/stats", tags=["health"])
async def get_system_stats():
    """Obtener estadísticas completas del sistema"""
    
    # Estadísticas de agentes
    agent_stats = {}
    for agent_id, agent in agent_registry.items():
        if hasattr(agent, 'get_processing_stats'):
            agent_stats[agent_id] = agent.get_processing_stats()
        else:
            agent_stats[agent_id] = agent.get_status()["metrics"]
    
    # Estadísticas de IA
    ai_stats = ai_service.get_stats()
    
    # Estadísticas del sistema
    system_stats = {
        "uptime": _get_uptime(),
        "active_agents": len([a for a in agent_registry.values() if a.status.value != "stopped"]),
        "total_agents": len(agent_registry),
        "timestamp": datetime.now().isoformat()
    }
    
    return {
        "success": True,
        "stats": {
            "system": system_stats,
            "agents": agent_stats,
            "ai_service": ai_stats
        }
    }

# 🔄 Rutas de gestión de agentes
@app.post("/api/v1/system/create-agent", tags=["agents"])
async def create_agent(request: Dict[str, Any]):
    """Crear un nuevo agente"""
    try:
        agent_type = request.get("type")
        name = request.get("name")
        description = request.get("description", "")
        config = request.get("config", {})
        
        if not agent_type or not name:
            raise HTTPException(
                status_code=400, 
                detail="Tipo y nombre del agente son requeridos"
            )
        
        # Crear agente usando factory
        agent = AgentFactory.create_agent(
            agent_type=agent_type,
            name=name,
            description=description,
            config=config
        )
        
        # Registrar agente
        register_agent(agent.id, agent)
        await agent.start()
        
        return {
            "success": True,
            "agent_id": agent.id,
            "message": f"Agente '{name}' creado exitosamente",
            "agent_info": agent.get_status()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/system/agents/{agent_id}", tags=["agents"])
async def delete_agent(agent_id: str):
    """Eliminar un agente"""
    from ..core.registry import get_agent, unregister_agent
    
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    await agent.stop()
    unregister_agent(agent_id)
    
    return {
        "success": True,
        "message": f"Agente {agent_id} eliminado exitosamente"
    }

# 🔧 Rutas de configuración
@app.get("/api/v1/config", tags=["health"])
async def get_config():
    """Obtener configuración actual del sistema"""
    return {
        "success": True,
        "config": {
            "project_name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "debug": settings.DEBUG,
            "ai_provider": ai_service.provider,
            "available_agent_types": AgentFactory.get_available_types(),
            "features": {
                "ai_analysis": settings.OPENAI_API_KEY is not None or settings.USE_OLLAMA,
                "file_upload": True,
                "batch_processing": True,
                "dashboard": True
            }
        }
    }

@app.post("/api/v1/config/cache/clear", tags=["health"])
async def clear_ai_cache():
    """Limpiar cache de IA"""
    ai_service.clear_cache()
    
    return {
        "success": True,
        "message": "Cache de IA limpiado exitosamente"
    }

# 🚨 Manejadores de errores
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Error interno del servidor",
            "timestamp": datetime.now().isoformat()
        }
    )

# 🔧 Funciones auxiliares
async def initialize_default_agents():
    """Inicializar agentes por defecto"""
    try:
        # Crear agente procesador de documentos
        doc_agent = DocumentProcessorAgent(
            name="DefaultDocumentProcessor",
            description="Procesador de documentos por defecto",
            config={
                "max_file_size": 10 * 1024 * 1024,  # 10MB
                "supported_formats": [".pdf", ".docx", ".txt", ".jpg", ".png"],
                "ocr_enabled": True,
                "ai_analysis_enabled": True
            }
        )
        
        register_agent(doc_agent.id, doc_agent)
        await doc_agent.start()
        
        print(f"✅ Agente por defecto creado: {doc_agent.name} (ID: {doc_agent.id})")
        
        # TODO: Agregar más agentes por defecto aquí
        # data_analyst = DataAnalystAgent(...)
        # customer_service = CustomerServiceAgent(...)
        
    except Exception as e:
        print(f"❌ Error inicializando agentes: {str(e)}")

async def shutdown_agents():
    """Detener todos los agentes"""
    for agent_id, agent in agent_registry.items():
        try:
            await agent.stop()
            print(f"🛑 Agente detenido: {agent.name}")
        except Exception as e:
            print(f"❌ Error deteniendo agente {agent_id}: {str(e)}")

def _get_uptime() -> float:
    """Calcular tiempo de actividad del sistema"""
    # Placeholder - en producción usarías un timestamp de inicio
    return 0.0

# 🎯 Función para ejecutar la aplicación
def run_server():
    """Ejecutar servidor de desarrollo"""
    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )

# 🚀 Script principal
if __name__ == "__main__":
    run_server()