"""
Formateador de respuestas del sistema.
Transforma respuestas del LLM en formatos estructurados para el cliente.
"""
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """Formatea respuestas en estructuras consistentes."""
    
    @staticmethod
    def format_query_response(
        answer: str,
        results: List[Dict[str, Any]],
        has_greeting_prefix: bool = False
    ) -> Dict[str, Any]:
        """
        Formatea una respuesta de query.
        
        Args:
            answer: Respuesta del LLM
            results: Resultados de búsqueda RAG
            has_greeting_prefix: Si la pregunta tenía saludo
            
        Returns:
            Dict: Respuesta formateada
        """
        # Limpiar menciones de fuentes del LLM (como defensa adicional)
        answer = ResponseFormatter._remove_source_references(answer)
        
        if has_greeting_prefix:
            answer = "¡Hola! 👋\n\n" + answer
        
        # Preparar lista de fuentes
        sources = ResponseFormatter._extract_sources(results)
        
        return {
            "answer": answer,
            "sources": sources,
            "context_used": len(results)
        }
    
    @staticmethod
    def format_no_context_response() -> Dict[str, Any]:
        """Respuesta cuando no hay documentos indexados."""
        return {
            "error": "No hay documentos indexados. Usa /api/index primero.",
            "answer": None
        }
    
    @staticmethod
    def format_no_results_response() -> Dict[str, Any]:
        """Respuesta cuando no hay resultados relevantes."""
        return {
            "answer": "No encontré información relevante en los documentos indexados.",
            "sources": [],
            "context_used": 0
        }
    
    @staticmethod
    def format_non_sst_query_response() -> Dict[str, Any]:
        """Respuesta cuando la pregunta NO es sobre SST."""
        return {
            "answer": "Lo siento, mi especialidad es responder preguntas sobre Seguridad y Salud en el Trabajo (SST). "
                     "Tu pregunta no parece estar relacionada con este tema.\n\n"
                     "Te sugiero que consultes otras fuentes de información especializadas en el tema que mencionas.",
            "sources": [],
            "context_used": 0
        }
    
    @staticmethod
    def format_sst_no_results_response(contact_info: str) -> Dict[str, Any]:
        """
        Respuesta cuando es pregunta SST pero no hay resultados.
        Incluye información de contacto.
        
        Args:
            contact_info: Información de contacto formateada
            
        Returns:
            Dict: Respuesta con contacto
        """
        return {
            "answer": f"Lo siento, no encontré información específica sobre esto en la documentación disponible. "
                     f"Sin embargo, como se trata de un tema relacionado con SST, te puedo proporcionar un contacto "
                     f"que puede ayudarte:\n\n{contact_info}",
            "sources": [],
            "context_used": 0
        }
    
    @staticmethod
    def format_greeting_response() -> Dict[str, Any]:
        """Respuesta a un saludo."""
        return {
            "answer": "¿En qué puedo ayudarte hoy?",
            "sources": [],
            "context_used": 0
        }
    
    @staticmethod
    def format_farewell_response() -> Dict[str, Any]:
        """Respuesta a una despedida."""
        return {
            "answer": "¡Hasta pronto! 👋 Que tengas un excelente día.",
            "sources": [],
            "context_used": 0
        }
    
    @staticmethod
    def format_thanks_response() -> Dict[str, Any]:
        """Respuesta a un agradecimiento."""
        return {
            "answer": "¡De nada! 😊 Estoy aquí para ayudarte cuando lo necesites.",
            "sources": [],
            "context_used": 0
        }
    
    @staticmethod
    def format_regional_contact_response(contact_info: str, region: str) -> Dict[str, Any]:
        """
        Respuesta cuando se solicita contacto de una región específica.
        
        Args:
            contact_info: Información de contacto formateada
            region: Nombre de la región
            
        Returns:
            Dict: Respuesta con información de contacto regional
        """
        return {
            "answer": f"Para reportar accidentes de trabajo en la región {region.title()}, "
                     f"aquí está la información de contacto:\n\n{contact_info}",
            "sources": [],
            "context_used": 0
        }
    
    @staticmethod
    def _remove_source_references(text: str) -> str:
        """
        Elimina referencias a fuentes que el LLM pueda haber incluido en la respuesta.
        
        Args:
            text: Texto de la respuesta
            
        Returns:
            str: Texto limpio sin referencias a fuentes
        """
        import re
        
        if not text:
            return text
        
        # Patrones de referencias de fuentes a remover
        patterns = [
            r'Fuentes?:\s*.*?(?:\n|$)',  # Cualquier línea que comience con "Fuente:" o "Fuentes:"
            r'Fuente:\s*Fragmento\s*\d+.*?(?:\n|$)',  # Fuente: Fragmento 3, Artículo 3°
            r'\(Fuente:.*?\)',  # (Fuente: ...)
            r'\[\d+\]',  # Referencias numéricas [1], [2]
            r'📚.*?(?:\n|$)',  # Líneas que contienen emoji de libros
            r'Según.*?(?:proporcionado|contexto).*?(?:\n|$)',  # Frases como "Según el contexto proporcionado"
        ]
        
        result = text
        for pattern in patterns:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE | re.MULTILINE)
        
        # Limpiar líneas vacías múltiples
        result = re.sub(r'\n\n+', '\n\n', result)
        
        return result.strip()
    
    @staticmethod
    def _extract_sources(results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Extrae y deduplica las fuentes de los resultados.
        
        Args:
            results: Resultados de búsqueda
            
        Returns:
            List[Dict]: Lista de fuentes únicas
        """
        sources_list = []
        seen_files = set()
        
        for r in results:
            if r.get("file") not in seen_files:
                sources_list.append({
                    "file": r.get("file", "unknown"),
                    "page": f"chunk {r.get('chunk_index', 0)}"
                })
                seen_files.add(r.get("file"))
        
        return sources_list
