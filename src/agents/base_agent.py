"""
🤖 Agente Base - Clase padre para todos los agentes del sistema
"""
import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from loguru import logger

class AgentStatus(Enum):
    """Estados posibles de un agente"""
    IDLE = "idle"
    WORKING = "working"
    ERROR = "error"
    STOPPED = "stopped"

class TaskPriority(Enum):
    """Prioridades de tareas"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class AgentTask:
    """Estructura de una tarea para el agente"""
    id: str
    name: str
    data: Dict[str, Any]
    priority: TaskPriority = TaskPriority.MEDIUM
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class AgentMetrics:
    """Métricas de rendimiento del agente"""
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0
    last_activity: Optional[datetime] = None
    uptime: float = 0.0
    
    def update_on_success(self, processing_time: float):
        """Actualizar métricas cuando una tarea es exitosa"""
        self.tasks_completed += 1
        self.total_processing_time += processing_time
        self.average_processing_time = self.total_processing_time / max(1, self.tasks_completed)
        self.last_activity = datetime.now()
    
    def update_on_failure(self):
        """Actualizar métricas cuando una tarea falla"""
        self.tasks_failed += 1
        self.last_activity = datetime.now()

class BaseAgent(ABC):
    """
    🤖 Clase base para todos los agentes del sistema
    
    Proporciona funcionalidad común como:
    - Gestión de tareas
    - Sistema de logging
    - Métricas de rendimiento
    - Manejo de errores
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        config: Optional[Dict[str, Any]] = None
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.config = config or {}
        
        # Estado del agente
        self.status = AgentStatus.IDLE
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        
        # Sistema de tareas
        self.task_queue: List[AgentTask] = []
        self.current_task: Optional[AgentTask] = None
        
        # Métricas y logging
        self.metrics = AgentMetrics()
        self.logger = logger.bind(agent=self.name, agent_id=self.id)
        
        # Configuración
        self.max_concurrent_tasks = self.config.get("max_concurrent_tasks", 1)
        self.timeout = self.config.get("timeout", 300)  # 5 minutos por defecto
        
        self.logger.info(f"🚀 Agente {self.name} inicializado")
    
    # 🎯 Métodos abstractos (deben ser implementados por cada agente)
    
    @abstractmethod
    async def process_task(self, task: AgentTask) -> Any:
        """
        Procesar una tarea específica del agente
        Debe ser implementado por cada agente hijo
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Retorna lista de capacidades del agente
        Ejemplo: ["extract_text", "analyze_sentiment", "generate_summary"]
        """
        pass
    
    # 🔧 Métodos de gestión de tareas
    
    async def add_task(
        self, 
        name: str, 
        data: Dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM
    ) -> str:
        """Agregar nueva tarea a la cola"""
        task = AgentTask(
            id=str(uuid.uuid4()),
            name=name,
            data=data,
            priority=priority
        )
        
        # Insertar según prioridad
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.priority.value, reverse=True)
        
        self.logger.info(f"📝 Nueva tarea agregada: {name} (ID: {task.id})")
        
        # Procesar si el agente está disponible
        if self.status == AgentStatus.IDLE:
            asyncio.create_task(self._process_next_task())
        
        return task.id
    
    async def get_task_result(self, task_id: str) -> Optional[Any]:
        """Obtener resultado de una tarea completada"""
        # Buscar en tareas completadas
        completed_tasks = [t for t in self.task_queue if t.id == task_id and t.completed_at]
        
        if completed_tasks:
            return completed_tasks[0].result
        
        # Si es la tarea actual
        if self.current_task and self.current_task.id == task_id:
            if self.current_task.completed_at:
                return self.current_task.result
        
        return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancelar una tarea pendiente"""
        # No se puede cancelar la tarea actual en ejecución
        if self.current_task and self.current_task.id == task_id:
            return False
        
        # Remover de la cola
        self.task_queue = [t for t in self.task_queue if t.id != task_id]
        self.logger.info(f"❌ Tarea cancelada: {task_id}")
        return True
    
    # 🔄 Métodos de control del agente
    
    async def start(self):
        """Iniciar el agente"""
        if self.status != AgentStatus.STOPPED:
            self.status = AgentStatus.IDLE
            self.started_at = datetime.now()
            self.logger.info(f"▶️ Agente {self.name} iniciado")
            
            # Procesar tareas pendientes
            if self.task_queue:
                asyncio.create_task(self._process_next_task())
    
    async def stop(self):
        """Detener el agente"""
        self.status = AgentStatus.STOPPED
        self.logger.info(f"⏹️ Agente {self.name} detenido")
    
    async def restart(self):
        """Reiniciar el agente"""
        await self.stop()
        await asyncio.sleep(1)
        await self.start()
        self.logger.info(f"🔄 Agente {self.name} reiniciado")
    
    # 🔍 Métodos de información
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado actual del agente"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "current_task": {
                "id": self.current_task.id,
                "name": self.current_task.name,
                "started_at": self.current_task.started_at.isoformat() if self.current_task.started_at else None
            } if self.current_task else None,
            "tasks_in_queue": len(self.task_queue),
            "capabilities": self.get_capabilities(),
            "metrics": {
                "tasks_completed": self.metrics.tasks_completed,
                "tasks_failed": self.metrics.tasks_failed,
                "average_processing_time": round(self.metrics.average_processing_time, 2),
                "uptime": self._calculate_uptime(),
                "last_activity": self.metrics.last_activity.isoformat() if self.metrics.last_activity else None
            }
        }
        
    
    def get_queue_status(self) -> List[Dict[str, Any]]:
        """Obtener estado de la cola de tareas"""
        return [
            {
                "id": task.id,
                "name": task.name,
                "priority": task.priority.name,
                "created_at": task.created_at.isoformat(),
                "status": "completed" if task.completed_at else "pending"
            }
            for task in self.task_queue
        ]
    
    # 🔒 Métodos privados
    
    async def _process_next_task(self):
        """Procesar la siguiente tarea en la cola"""
        if not self.task_queue or self.status == AgentStatus.STOPPED:
            return
        
        # Tomar la tarea de mayor prioridad
        task = self.task_queue.pop(0)
        self.current_task = task
        self.status = AgentStatus.WORKING
        
        task.started_at = datetime.now()
        self.logger.info(f"🔄 Procesando tarea: {task.name} (ID: {task.id})")
        
        try:
            # Procesar con timeout
            result = await asyncio.wait_for(
                self.process_task(task),
                timeout=self.timeout
            )
            
            # Tarea completada exitosamente
            task.result = result
            task.completed_at = datetime.now()
            
            # Actualizar métricas
            processing_time = (task.completed_at - task.started_at).total_seconds()
            self.metrics.update_on_success(processing_time)
            
            self.logger.success(f"✅ Tarea completada: {task.name} ({processing_time:.2f}s)")
            
        except asyncio.TimeoutError:
            task.error = f"Timeout después de {self.timeout} segundos"
            self.metrics.update_on_failure()
            self.logger.error(f"⏱️ Timeout en tarea: {task.name}")
            
        except Exception as e:
            task.error = str(e)
            self.metrics.update_on_failure()
            self.logger.error(f"❌ Error en tarea {task.name}: {str(e)}")
        
        finally:
            # Limpiar estado
            self.current_task = None
            self.status = AgentStatus.IDLE
            
            # Procesar siguiente tarea si existe
            if self.task_queue and self.status != AgentStatus.STOPPED:
                asyncio.create_task(self._process_next_task())
    
    def _calculate_uptime(self) -> float:
        """Calcular tiempo de actividad en segundos"""
        if not self.started_at:
            return 0.0
        return (datetime.now() - self.started_at).total_seconds()
    
    # 🎨 Métodos de utilidad
    
    def __str__(self) -> str:
        return f"Agent({self.name}): {self.status.value}"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', status='{self.status.value}')>"

# 🔧 Decorador para validar configuración del agente
def validate_agent_config(required_keys: List[str]):
    """Decorador para validar que el agente tenga la configuración necesaria"""
    def decorator(cls):
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            
            # Validar configuración
            missing_keys = [key for key in required_keys if key not in self.config]
            if missing_keys:
                raise ValueError(f"Configuración faltante para {cls.__name__}: {missing_keys}")
        
        cls.__init__ = new_init
        return cls
    
    return decorator

# 🎯 Factory para crear agentes
class AgentFactory:
    """Factory para crear diferentes tipos de agentes"""
    
    _agent_classes = {}
    
    @classmethod
    def register(cls, agent_type: str, agent_class: type):
        """Registrar un nuevo tipo de agente"""
        cls._agent_classes[agent_type] = agent_class
    
    @classmethod
    def create_agent(
        cls, 
        agent_type: str, 
        name: str, 
        description: str,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseAgent:
        """Crear un agente del tipo especificado"""
        if agent_type not in cls._agent_classes:
            raise ValueError(f"Tipo de agente no registrado: {agent_type}")
        
        agent_class = cls._agent_classes[agent_type]
        return agent_class(name=name, description=description, config=config)
    
    @classmethod
    def get_available_types(cls) -> List[str]:
        """Obtener tipos de agentes disponibles"""
        return list(cls._agent_classes.keys())

# 🚀 Exportar clases principales
__all__ = [
    "BaseAgent",
    "AgentTask",
    "AgentStatus", 
    "TaskPriority",
    "AgentMetrics",
    "AgentFactory",
    "validate_agent_config"
]