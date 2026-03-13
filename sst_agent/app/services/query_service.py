"""
Servicio de procesamiento de queries.
Orquesta la detección de intenciones, búsqueda RAG y generación de respuestas.
"""
import logging
from typing import Dict, Any

from sst_agent.app.services.llm import generate
from sst_agent.app.services.rag_service import RAGService
from sst_agent.app.services.utils.intention_detector import IntentionDetector, IntentionType
from sst_agent.app.services.utils.response_formatter import ResponseFormatter

logger = logging.getLogger(__name__)


class QueryService:
    """Servicio de procesamiento de queries del usuario."""
    
    @staticmethod
    def process_query(question: str) -> Dict[str, Any]:
        """
        Procesa una consulta del usuario completa.
        
        Args:
            question: Consulta del usuario
            
        Returns:
            Dict: Respuesta procesada
            
        Raises:
            Exception: Si hay error en el procesamiento
        """
        question = question.strip()
        logger.info(f"Procesando consulta: {question[:50]}...")
        
        # 1. Detectar intención
        intention = IntentionDetector.detect(question)
        has_greeting = IntentionDetector.has_greeting_prefix(question)
        
        logger.debug(f"Intención detectada: {intention.value}")
        
        # 2. Responder según intención
        if intention == IntentionType.GREETING:
            return ResponseFormatter.format_greeting_response()
        
        if intention == IntentionType.FAREWELL:
            return ResponseFormatter.format_farewell_response()
        
        if intention == IntentionType.THANKS:
            return ResponseFormatter.format_thanks_response()
        
        # 3. Para preguntas: verificar documentos
        if not RAGService.has_documents():
            logger.warning("No hay documentos indexados")
            return ResponseFormatter.format_no_context_response()
        
        # 4. Buscar contexto
        try:
            results = RAGService.search_context(question)
            
            if not results:
                logger.info("No se encontraron resultados relevantes")
                return ResponseFormatter.format_no_results_response()
            
            # 5. Construir contexto
            context = RAGService.build_context(results)
            
            # 6. Generar respuesta
            prompt_text = f"""Based ONLY on the provided context, answer this question:

{question}"""
            
            answer = generate(prompt_text, max_tokens=1200, context=context)
            
            # 7. Formatear respuesta final
            return ResponseFormatter.format_query_response(
                answer=answer,
                results=results,
                has_greeting_prefix=has_greeting
            )
            
        except Exception as e:
            logger.error(f"Error procesando consulta: {e}")
            raise
