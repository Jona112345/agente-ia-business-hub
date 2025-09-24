"""
🗄️ Registry - Registro global de agentes y servicios
"""
from typing import Dict, Any

# 📋 Global agent registry
agent_registry: Dict[str, Any] = {}

def get_agent_registry() -> Dict[str, Any]:
    """Obtener el registro de agentes"""
    return agent_registry

def register_agent(agent_id: str, agent: Any) -> None:
    """Registrar un agente"""
    agent_registry[agent_id] = agent

def unregister_agent(agent_id: str) -> bool:
    """Desregistrar un agente"""
    if agent_id in agent_registry:
        del agent_registry[agent_id]
        return True
    return False

def get_agent(agent_id: str) -> Any:
    """Obtener un agente específico"""
    return agent_registry.get(agent_id)

def clear_registry() -> None:
    """Limpiar todo el registro"""
    agent_registry.clear()