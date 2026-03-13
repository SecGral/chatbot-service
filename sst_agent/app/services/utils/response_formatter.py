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
