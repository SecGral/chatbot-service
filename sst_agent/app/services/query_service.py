"""
Servicio de procesamiento de queries.
Orquesta la detección de intenciones, búsqueda RAG y generación de respuestas.
"""
import logging
from typing import Dict, Any, Optional

from sst_agent.app.services.llm import generate
from sst_agent.app.services.rag_service import RAGService
from sst_agent.app.services.utils.intention_detector import IntentionDetector, IntentionType
from sst_agent.app.services.utils.response_formatter import ResponseFormatter
from sst_agent.app.services.utils.sst_domain_detector import SSTDomainDetector
from sst_agent.app.services.utils.directory_service import DirectoryService

logger = logging.getLogger(__name__)


class QueryService:
    """Servicio de procesamiento de queries del usuario."""
    
    @staticmethod
    def process_query(question: str, context_summary: Optional[str] = None) -> Dict[str, Any]:
        """
        Procesa una consulta del usuario completa.
        
        Args:
            question: Consulta del usuario
            context_summary: Resumen de conversaciones anteriores (para memoria)
            
        Returns:
            Dict: Respuesta procesada
            
        Raises:
            Exception: Si hay error en el procesamiento
        """
        question = question.strip()
        logger.info(f"Procesando consulta: {question[:50]}...")
        if context_summary:
            logger.debug(f"Usando contexto previo de sesión")
        
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
        
        # 3. Detectar dominio ANTES de buscar
        is_sst = SSTDomainDetector.is_sst_related(question)
        logger.info(f"Dominio detectado: {'SST' if is_sst else 'NO-SST'}")
        
        # 4. Si NO es SST, responder sin buscar en PDFs
        if not is_sst:
            logger.info("Pregunta no relacionada con SST")
            return ResponseFormatter.format_non_sst_query_response()
        
        # 5. Para preguntas SST: verificar documentos
        if not RAGService.has_documents():
            logger.warning("No hay documentos indexados")
            return ResponseFormatter.format_no_context_response()
        
        # 6. Buscar contexto en PDFs SST
        try:
            results = RAGService.search_context(question)
            
            if not results:
                logger.info("No se encontraron resultados relevantes para pregunta SST")
                # Es SST pero sin información → proporcionar contactos
                contact_info = DirectoryService.get_formatted_contact()
                return ResponseFormatter.format_sst_no_results_response(contact_info)
            
            # 7. Construir contexto
            context = RAGService.build_context(results)
            
            # 8. Generar respuesta
            # Construir prompt con contexto de sesión anterior si existe
            conversation_context = ""
            if context_summary:
                conversation_context = f"""CONTEXTO DE LA CONVERSACIÓN ANTERIOR:
{context_summary}

---

"""
            
            prompt_text = f"""Responde la siguiente pregunta basándote ÚNICAMENTE en el contexto proporcionado.

{conversation_context}IMPORTANTE:
- Solo usa información del contexto
- NO incluyas referencias a fuentes, fragmentos, artículos o números dentro de tu respuesta
- Responde de forma clara y concisa
- Las fuentes serán agregadas automáticamente al final
- Ten en cuenta la conversación anterior para mantener coherencia

Pregunta: {question}"""
            
            answer = generate(prompt_text, max_tokens=1200, context=context)
            
            # 9. Formatear respuesta final
            return ResponseFormatter.format_query_response(
                answer=answer,
                results=results,
                has_greeting_prefix=has_greeting
            )
            
        except Exception as e:
            logger.error(f"Error procesando consulta: {e}")
            raise
