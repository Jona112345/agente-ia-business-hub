"""
🤖 Rutas de Agentes - Gestión completa de agentes de IA
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel

# Imports locales
from ...agents.base_agent import AgentFactory, TaskPriority
from ...core.config import settings
from ...core.registry import agent_registry

router = APIRouter()

# 📋 Modelos Pydantic
class TaskRequest(BaseModel):
    name: str
    data: Dict[str, Any]
    priority: str = "medium"

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

class AgentStatus(BaseModel):
    id: str
    name: str
    description: str
    status: str
    capabilities: List[str]
    metrics: Dict[str, Any]

# 🌟 Rutas principales de agentes

@router.get("/", response_model=List[AgentStatus])
async def list_agents():
    """Listar todos los agentes registrados"""
    agents_info = []
    
    for agent_id, agent in agent_registry.items():
        status_info = agent.get_status()
        agents_info.append(AgentStatus(
            id=status_info["id"],
            name=status_info["name"],
            description=status_info["description"],
            status=status_info["status"],
            capabilities=status_info["capabilities"],
            metrics=status_info["metrics"]
        ))
    
    return agents_info

@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """Obtener información detallada de un agente específico"""
    if agent_id not in agent_registry:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    agent = agent_registry[agent_id]
    status = agent.get_status()
    queue_status = agent.get_queue_status()
    
    return {
        "success": True,
        "agent": status,
        "queue": queue_status,
        "available_actions": [
            "start", "stop", "restart", "add_task", "cancel_task"
        ]
    }

@router.get("/types/available")
async def get_available_agent_types():
    """Obtener tipos de agentes disponibles"""
    return {
        "success": True,
        "available_types": AgentFactory.get_available_types(),
        "descriptions": {
            "document_processor": "Procesa y analiza documentos (PDF, Word, imágenes)",
            "data_analyst": "Analiza datos y genera insights",
            "customer_service": "Agente de atención al cliente",
            "monitor": "Monitorea sistemas y procesos"
        }
    }

# 🔄 Control de agentes

@router.post("/{agent_id}/start")
async def start_agent(agent_id: str):
    """Iniciar un agente"""
    if agent_id not in agent_registry:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    agent = agent_registry[agent_id]
    await agent.start()
    
    return {
        "success": True,
        "message": f"Agente {agent.name} iniciado",
        "status": agent.status.value
    }

@router.post("/{agent_id}/stop")
async def stop_agent(agent_id: str):
    """Detener un agente"""
    if agent_id not in agent_registry:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    agent = agent_registry[agent_id]
    await agent.stop()
    
    return {
        "success": True,
        "message": f"Agente {agent.name} detenido",
        "status": agent.status.value
    }

@router.post("/{agent_id}/restart")
async def restart_agent(agent_id: str):
    """Reiniciar un agente"""
    if agent_id not in agent_registry:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    agent = agent_registry[agent_id]
    await agent.restart()
    
    return {
        "success": True,
        "message": f"Agente {agent.name} reiniciado",
        "status": agent.status.value
    }

# 📝 Gestión de tareas

@router.post("/{agent_id}/tasks", response_model=TaskResponse)
async def add_task(agent_id: str, task: TaskRequest):
    """Agregar una nueva tarea a un agente"""
    if agent_id not in agent_registry:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    agent = agent_registry[agent_id]
    
    # Convertir prioridad string a enum
    priority_map = {
        "low": TaskPriority.LOW,
        "medium": TaskPriority.MEDIUM,
        "high": TaskPriority.HIGH,
        "critical": TaskPriority.CRITICAL
    }
    
    priority = priority_map.get(task.priority.lower(), TaskPriority.MEDIUM)
    
    try:
        task_id = await agent.add_task(
            name=task.name,
            data=task.data,
            priority=priority
        )
        
        return TaskResponse(
            task_id=task_id,
            status="queued",
            message=f"Tarea '{task.name}' agregada exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{agent_id}/tasks")
async def get_agent_tasks(agent_id: str):
    """Obtener todas las tareas de un agente"""
    if agent_id not in agent_registry:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    agent = agent_registry[agent_id]
    
    return {
        "success": True,
        "agent_id": agent_id,
        "current_task": {
            "id": agent.current_task.id,
            "name": agent.current_task.name,
            "started_at": agent.current_task.started_at.isoformat() if agent.current_task.started_at else None
        } if agent.current_task else None,
        "queue": agent.get_queue_status()
    }

@router.get("/{agent_id}/tasks/{task_id}")
async def get_task_result(agent_id: str, task_id: str):
    """Obtener resultado de una tarea específica"""
    if agent_id not in agent_registry:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    agent = agent_registry[agent_id]
    result = await agent.get_task_result(task_id)
    
    if result is None:
        # Buscar en la cola para obtener información de la tarea
        queue_status = agent.get_queue_status()
        task_info = next((t for t in queue_status if t["id"] == task_id), None)
        
        if task_info:
            return {
                "success": True,
                "task_id": task_id,
                "status": task_info["status"],
                "result": None,
                "message": "Tarea aún no completada"
            }
        else:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    return {
        "success": True,
        "task_id": task_id,
        "result": result,
        "status": "completed"
    }

@router.delete("/{agent_id}/tasks/{task_id}")
async def cancel_task(agent_id: str, task_id: str):
    """Cancelar una tarea pendiente"""
    if agent_id not in agent_registry:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    agent = agent_registry[agent_id]
    success = await agent.cancel_task(task_id)
    
    if not success:
        raise HTTPException(
            status_code=400, 
            detail="No se puede cancelar la tarea (puede estar ejecutándose actualmente)"
        )
    
    return {
        "success": True,
        "message": f"Tarea {task_id} cancelada exitosamente"
    }

# 📄 Rutas específicas para Document Processor

@router.post("/{agent_id}/upload-document")
async def upload_document(
    agent_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    analysis_type: str = Form("extract_text"),
    auto_classify: bool = Form(True)
):
    """Subir y procesar un documento"""
    if agent_id not in agent_registry:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    agent = agent_registry[agent_id]
    
    # Verificar que sea un Document Processor
    if "extract_text_pdf" not in agent.get_capabilities():
        raise HTTPException(
            status_code=400, 
            detail="Este agente no puede procesar documentos"
        )
    
    # Validar archivo
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo requerido")
    
    # Guardar archivo
    import os
    from pathlib import Path
    
    upload_dir = Path("uploads/documents")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Crear tarea de procesamiento
    task_data = {
        "file_path": str(file_path),
        "original_filename": file.filename,
        "file_size": len(content),
        "auto_classify": auto_classify
    }
    
    try:
        # Agregar tarea de extracción de texto
        extract_task_id = await agent.add_task(
            name=analysis_type,
            data=task_data,
            priority=TaskPriority.HIGH
        )
        
        # Si se requiere clasificación automática, agregar tarea adicional
        classify_task_id = None
        if auto_classify:
            # Esperar a que termine la extracción (simplificado)
            background_tasks.add_task(
                _add_classification_task,
                agent, extract_task_id, task_data
            )
        
        return {
            "success": True,
            "message": "Documento subido y procesamiento iniciado",
            "file_info": {
                "filename": file.filename,
                "size": len(content),
                "path": str(file_path)
            },
            "tasks": {
                "extraction": extract_task_id,
                "classification": "pending" if auto_classify else None
            }
        }
        
    except Exception as e:
        # Limpiar archivo si hay error
        if file_path.exists():
            os.unlink(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{agent_id}/batch-upload")
async def batch_upload_documents(
    agent_id: str,
    files: List[UploadFile] = File(...),
    max_files: int = Form(10)
):
    """Subir múltiples documentos para procesamiento por lotes"""
    if agent_id not in agent_registry:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    agent = agent_registry[agent_id]
    
    # Verificar que sea un Document Processor
    if "extract_text_pdf" not in agent.get_capabilities():
        raise HTTPException(
            status_code=400, 
            detail="Este agente no puede procesar documentos"
        )
    
    if len(files) > max_files:
        raise HTTPException(
            status_code=400, 
            detail=f"Máximo {max_files} archivos permitidos"
        )
    
    uploaded_files = []
    failed_uploads = []
    
    # Guardar archivos
    upload_dir = Path("uploads/batch") / datetime.now().strftime('%Y%m%d_%H%M%S')
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    for file in files:
        try:
            if not file.filename:
                continue
                
            file_path = upload_dir / file.filename
            
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            uploaded_files.append(str(file_path))
            
        except Exception as e:
            failed_uploads.append({
                "filename": file.filename if file.filename else "unknown",
                "error": str(e)
            })
    
    if not uploaded_files:
        raise HTTPException(
            status_code=400, 
            detail="No se pudieron subir archivos"
        )
    
    # Crear tarea de procesamiento por lotes
    try:
        task_id = await agent.add_task(
            name="process_batch",
            data={
                "file_paths": uploaded_files,
                "batch_id": upload_dir.name
            },
            priority=TaskPriority.HIGH
        )
        
        return {
            "success": True,
            "message": f"Lote de {len(uploaded_files)} archivos procesándose",
            "task_id": task_id,
            "uploaded_files": len(uploaded_files),
            "failed_uploads": failed_uploads,
            "batch_id": upload_dir.name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 📊 Rutas de estadísticas específicas

@router.get("/{agent_id}/stats")
async def get_agent_stats(agent_id: str):
    """Obtener estadísticas detalladas de un agente"""
    if agent_id not in agent_registry:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    agent = agent_registry[agent_id]
    
    # Estadísticas base
    base_stats = agent.get_status()["metrics"]
    
    # Estadísticas específicas si el agente las tiene
    if hasattr(agent, 'get_processing_stats'):
        specific_stats = agent.get_processing_stats()
    else:
        specific_stats = {}
    
    return {
        "success": True,
        "agent_id": agent_id,
        "agent_name": agent.name,
        "stats": {
            **base_stats,
            **specific_stats
        },
        "performance": {
            "success_rate": (base_stats["tasks_completed"] / 
                           max(1, base_stats["tasks_completed"] + base_stats["tasks_failed"])),
            "avg_processing_time": base_stats["average_processing_time"],
            "uptime": base_stats.get("uptime", 0)
        }
    }

# 🔧 Funciones auxiliares

async def _add_classification_task(agent, extract_task_id: str, task_data: Dict):
    """Agregar tarea de clasificación después de la extracción"""
    # Esperar a que termine la extracción
    max_wait = 60  # 1 minuto máximo
    waited = 0
    
    while waited < max_wait:
        result = await agent.get_task_result(extract_task_id)
        if result is not None:
            # La extracción terminó, agregar clasificación
            await agent.add_task(
                name="classify_document",
                data={
                    "text": result.get("text", ""),
                    "file_name": task_data.get("original_filename", "")
                },
                priority=TaskPriority.MEDIUM
            )
            break
        
        await asyncio.sleep(1)
        waited += 1

# 🎯 Exportar router
__all__ = ["router"]