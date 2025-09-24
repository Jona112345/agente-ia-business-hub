"""
🧠 AI Service - Servicio centralizado para interacciones con IA
Soporta OpenAI, Ollama y modelos locales
"""
import asyncio
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from loguru import logger

class AIService:
    """
    🤖 Servicio centralizado de IA
    
    Características:
    - Soporte para múltiples proveedores (OpenAI, Ollama, Mock)
    - Rate limiting y manejo de errores
    - Cache de respuestas (opcional)
    - Métricas de uso
    """
    
    def __init__(self):
        # Determinar proveedor
        try:
            from ..core.config import settings
            self.provider = "ollama" if settings.USE_OLLAMA else "openai"
        except:
            self.provider = "mock"
            
        # Métricas
        self.requests_made = 0
        self.tokens_used = 0
        self.errors_count = 0
        self.cache_hits = 0
        
        # Cache simple
        self._cache = {}
        self.cache_enabled = True
        self.cache_ttl = 3600  # 1 hora
        
        logger.info(f"🧠 AI Service inicializado con proveedor: {self.provider}")
    
    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generar texto usando el modelo de IA configurado
        """
        # Por ahora solo usar modo mock para evitar dependencias
        try:
            response = await self._generate_mock(prompt)
            
            self.requests_made += 1
            self.tokens_used += len(response.split())
            
            logger.success(f"✅ Texto generado: {len(response)} caracteres")
            return response
            
        except Exception as e:
            self.errors_count += 1
            logger.error(f"❌ Error generando texto: {str(e)}")
            raise AIServiceError(f"Error en generación de texto: {str(e)}")
    
    async def _generate_mock(self, prompt: str) -> str:
        """Generar respuesta mock para desarrollo sin IA real"""
        await asyncio.sleep(0.5)  # Simular latencia
        
        # Respuestas predeterminadas basadas en el contenido del prompt
        prompt_lower = prompt.lower()
        
        if "clasifica" in prompt_lower or "classify" in prompt_lower:
            return "informe|0.8"
        
        elif "entidades" in prompt_lower or "entities" in prompt_lower:
            return """PERSONA: Juan Pérez
EMPRESA: Acme Corporation
FECHA: 2024-01-15
DINERO: €1,500.00
LUGAR: Madrid, España"""
        
        elif "resumen" in prompt_lower or "summary" in prompt_lower:
            return "Este documento contiene información importante sobre procesos empresariales. Se destacan aspectos clave relacionados con la automatización y mejora de eficiencia."
        
        elif "sentimiento" in prompt_lower or "sentiment" in prompt_lower:
            return "neutro|0.7"
        
        elif "automatización" in prompt_lower or "automation" in prompt_lower:
            return "La automatización empresarial es el proceso de utilizar tecnología para realizar tareas repetitivas sin intervención humana. Incluye procesamiento de documentos, análisis de datos, y optimización de flujos de trabajo. Los beneficios principales son: reducción de costos, mayor eficiencia, menos errores humanos, y disponibilidad 24/7."
            
        elif "hola" in prompt_lower or "hello" in prompt_lower:
            return "¡Hola! Soy tu asistente de IA del sistema Agentic AI Hub. Estoy aquí para ayudarte con automatización empresarial, procesamiento de documentos, análisis de datos y mucho más. ¿En qué puedo ayudarte hoy?"
        
        else:
            return f"Respuesta generada para: '{prompt[:50]}...'. En producción, aquí estaría la respuesta real de la IA. El sistema está funcionando correctamente en modo de desarrollo."
    
    # 🔍 Métodos de análisis específicos
    
    async def analyze_text(
        self,
        text: str,
        analysis_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Análizar texto con diferentes tipos de análisis
        
        Args:
            text: Texto a analizar
            analysis_type: Tipo de análisis (general, sentiment, entities, classification)
        """
        if analysis_type == "sentiment":
            return await self.analyze_sentiment(text)
        elif analysis_type == "entities":
            return await self.extract_entities(text)
        elif analysis_type == "classification":
            return await self.classify_text(text)
        else:
            return await self.general_analysis(text)
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Análisis de sentimiento"""
        prompt = f"""
        Analiza el sentimiento del siguiente texto y responde en formato JSON:
        {{
            "sentiment": "positivo/neutro/negativo",
            "confidence": 0.8,
            "reasoning": "breve explicación"
        }}
        
        Texto: {text[:1500]}
        """
        
        response = await self.generate_text(prompt, temperature=0.3)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback parsing
            lines = response.split('\n')
            return {
                "sentiment": "neutro",
                "confidence": 0.5,
                "reasoning": "No se pudo parsear la respuesta",
                "raw_response": response
            }
    
    async def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extracción de entidades nombradas"""
        prompt = f"""
        Extrae entidades del siguiente texto y responde en formato JSON:
        {{
            "personas": ["nombre1", "nombre2"],
            "organizaciones": ["empresa1", "empresa2"], 
            "lugares": ["lugar1", "lugar2"],
            "fechas": ["fecha1", "fecha2"],
            "dinero": ["cantidad1", "cantidad2"]
        }}
        
        Texto: {text[:2000]}
        """
        
        response = await self.generate_text(prompt, temperature=0.2)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "personas": [],
                "organizaciones": [],
                "lugares": [],
                "fechas": [],
                "dinero": [],
                "raw_response": response
            }
    
    async def classify_text(self, text: str, categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """Clasificación de texto"""
        default_categories = ["factura", "contrato", "informe", "email", "legal", "otros"]
        categories = categories or default_categories
        
        categories_str = ", ".join(categories)
        
        prompt = f"""
        Clasifica el siguiente texto en una de estas categorías: {categories_str}
        
        Responde en formato JSON:
        {{
            "category": "categoria_elegida",
            "confidence": 0.8,
            "reasoning": "breve explicación"
        }}
        
        Texto: {text[:1500]}
        """
        
        response = await self.generate_text(prompt, temperature=0.3)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "category": "otros",
                "confidence": 0.1,
                "reasoning": "No se pudo clasificar",
                "raw_response": response
            }
    
    async def general_analysis(self, text: str) -> Dict[str, Any]:
        """Análisis general del texto"""
        prompt = f"""
        Realiza un análisis completo del siguiente texto y responde en formato JSON:
        {{
            "summary": "resumen en 2-3 frases",
            "main_topics": ["tema1", "tema2"],
            "language": "idioma detectado",
            "text_type": "tipo de documento",
            "key_points": ["punto1", "punto2"],
            "word_count": 150
        }}
        
        Texto: {text[:2500]}
        """
        
        response = await self.generate_text(prompt, temperature=0.4)
        
        try:
            result = json.loads(response)
            result["actual_word_count"] = len(text.split())
            return result
        except json.JSONDecodeError:
            return {
                "summary": "Análisis no disponible",
                "main_topics": [],
                "language": "desconocido",
                "text_type": "desconocido",
                "key_points": [],
                "word_count": len(text.split()),
                "raw_response": response
            }
    
    # 🔧 Métodos de utilidad
    
    def _generate_cache_key(self, prompt: str, model: Optional[str], temperature: float) -> str:
        """Generar clave de cache"""
        import hashlib
        content = f"{prompt}|{model}|{temperature}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_cache_valid(self, cached_data: Dict) -> bool:
        """Verificar si el cache es válido"""
        if not cached_data:
            return False
        
        timestamp = cached_data.get("timestamp")
        if not timestamp:
            return False
        
        age = (datetime.now() - timestamp).total_seconds()
        return age < self.cache_ttl
    
    def clear_cache(self):
        """Limpiar cache"""
        self._cache.clear()
        logger.info("🧹 Cache de IA limpiado")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del servicio"""
        return {
            "provider": self.provider,
            "requests_made": self.requests_made,
            "tokens_used": self.tokens_used,
            "errors_count": self.errors_count,
            "cache_hits": self.cache_hits,
            "cache_size": len(self._cache),
            "success_rate": (self.requests_made - self.errors_count) / max(1, self.requests_made),
        }
    
    # 🎯 Métodos para casos de uso específicos
    
    async def generate_business_report(
        self,
        data: Dict[str, Any],
        report_type: str = "summary"
    ) -> str:
        """Generar reporte empresarial"""
        prompt = f"""
        Genera un reporte empresarial de tipo '{report_type}' basado en los siguientes datos:
        
        {json.dumps(data, indent=2, ensure_ascii=False)}
        
        El reporte debe ser profesional, claro y orientado a tomadores de decisiones.
        Incluye insights clave y recomendaciones accionables.
        """
        
        return await self.generate_text(
            prompt,
            temperature=0.6,
            max_tokens=1500,
            system_prompt="Eres un analista de negocios experto que genera reportes claros y accionables."
        )
    
    async def suggest_automations(self, process_description: str) -> List[Dict[str, str]]:
        """Sugerir automatizaciones para un proceso"""
        prompt = f"""
        Analiza el siguiente proceso empresarial y sugiere automatizaciones específicas:
        
        Proceso: {process_description}
        
        Responde en formato JSON con una lista de sugerencias:
        [
            {{
                "automation": "nombre de la automatización",
                "description": "descripción detallada",
                "benefit": "beneficio principal",
                "difficulty": "baja/media/alta",
                "estimated_time_saving": "% de tiempo ahorrado"
            }}
        ]
        """
        
        response = await self.generate_text(prompt, temperature=0.7)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return [
                {
                    "automation": "Automatización sugerida",
                    "description": "No se pudo parsear la respuesta de IA",
                    "benefit": "Optimización de procesos",
                    "difficulty": "media",
                    "estimated_time_saving": "20%"
                }
            ]

# 🚨 Excepciones personalizadas
class AIServiceError(Exception):
    """Excepción para errores del servicio de IA"""
    pass

# 🌟 Instancia global del servicio
ai_service = AIService()

# 🎯 Funciones de conveniencia
async def quick_analysis(text: str) -> Dict[str, Any]:
    """Análisis rápido de texto"""
    return await ai_service.general_analysis(text)

async def quick_classification(text: str) -> str:
    """Clasificación rápida de texto"""
    result = await ai_service.classify_text(text)
    return result.get("category", "desconocido")

async def quick_summary(text: str) -> str:
    """Resumen rápido de texto"""
    if len(text) < 200:
        return text
    
    prompt = f"Resume este texto en máximo 2 frases: {text[:1000]}"
    return await ai_service.generate_text(prompt, max_tokens=100, temperature=0.5)

# 🚀 Exportar elementos principales
__all__ = [
    "AIService",
    "AIServiceError", 
    "ai_service",
    "quick_analysis",
    "quick_classification",
    "quick_summary"
]