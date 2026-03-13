"""
Servicio de RAG (Retrieval-Augmented Generation).
Operaciones de alto nivel para búsqueda y contexto.
"""
import logging
from typing import List, Dict, Any

from sst_agent.app.rag.embeddings import embed_text
from sst_agent.app.rag import vector_db

logger = logging.getLogger(__name__)

# Constantes de configuración
MAX_CONTEXT_CHARS = 3500
MIN_REMAINING_CHARS = 200
DEFAULT_K = 5


class RAGService:
    """Servicio de operaciones RAG de alto nivel."""
    
    @staticmethod
    def search_context(question: str, k: int = DEFAULT_K) -> List[Dict[str, Any]]:
        """
        Busca contexto relevante para una pregunta.
        
        Args:
            question: Pregunta del usuario
            k: Número de chunks a recuperar
            
        Returns:
            List[Dict]: Resultados de búsqueda
        """
        logger.info(f"Buscando contexto para: {question[:50]}...")
        
        try:
            # Generar embedding de la pregunta
            q_vec = embed_text([question])[0].tolist()
            
            # Buscar en la base de datos vectorial
            results = vector_db.search_similar(q_vec, k=k)
            
            logger.info(f"Encontrados {len(results)} chunks relevantes")
            return results
            
        except Exception as e:
            logger.error(f"Error buscando contexto: {e}")
            raise
    
    @staticmethod
    def build_context(results: List[Dict[str, Any]]) -> str:
        """
        Construye un string de contexto a partir de los resultados.
        Con límite flexible de caracteres.
        
        Args:
            results: Resultados de búsqueda
            
        Returns:
            str: Contexto formateado
        """
        context_parts = []
        total_chars = 0
        
        for i, result in enumerate(results, 1):
            chunk_content = result.get('content', '')
            
            # Verificar si agregar este chunk excede el límite
            if total_chars + len(chunk_content) > MAX_CONTEXT_CHARS:
                remaining = MAX_CONTEXT_CHARS - total_chars
                
                # Solo agregar si quedan suficientes caracteres
                if remaining > MIN_REMAINING_CHARS:
                    chunk_content = chunk_content[:remaining]
                else:
                    break
            
            context_parts.append(f"[Fragmento {i}]\n{chunk_content}")
            total_chars += len(chunk_content)
        
        context = "\n\n---\n\n".join(context_parts)
        logger.info(f"Contexto construido: {total_chars} caracteres")
        
        return context
    
    @staticmethod
    def has_documents() -> bool:
        """
        Verifica si hay documentos indexados.
        
        Returns:
            bool: True si hay documentos
        """
        try:
            count = vector_db.get_indexed_count()
            return count > 0
        except Exception as e:
            logger.error(f"Error verificando documentos: {e}")
            raise
