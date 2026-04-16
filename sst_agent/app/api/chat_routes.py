from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from typing import Optional

from sst_agent.app.services.query_service import QueryService
from sst_agent.app.services.session_manager import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


class Query(BaseModel):
    """Modelo de solicitud de query."""
    question: str
    session_id: Optional[str] = None


class SessionResponse(BaseModel):
    """Respuesta con ID de sesión."""
    session_id: str


@router.post("/session/create")
def create_session():
    """
    Crea una nueva sesión de conversación.
    
    El cliente debe guardar este session_id y enviarlo en cada pregunta.
    Cuando recarga la página o cierra el navegador, pierde el session_id
    y la sesión se pierde (sin persistencia de conversación).
    
    Returns:
        SessionResponse: ID de la nueva sesión
    """
    session_id = SessionManager.create_session()
    logger.info(f"Sesión creada: {session_id}")
    return SessionResponse(session_id=session_id)


@router.get("/session/history/{session_id}")
def get_history(session_id: str):
    """
    Obtiene el histórico de una sesión.
    
    Args:
        session_id: ID de la sesión
        
    Returns:
        List: Histórico de mensajes
    """
    history = SessionManager.get_history(session_id)
    if history is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada o expirada")
    
    return {"session_id": session_id, "history": history}


@router.post("/session/clear/{session_id}")
def clear_session(session_id: str):
    """
    Limpia una sesión manualmente.
    
    Args:
        session_id: ID de la sesión
    """
    success = SessionManager.clear_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    return {"message": "Sesión limpiada"}


@router.post("/query")
def query(req: Query):
    """
    Procesa una consulta del usuario.
    
    - Si session_id es null → crea sesión nueva automáticamente
    - Si session_id existe → continúa conversación
    - Detecta intenciones (saludos, preguntas, etc)
    - Genera respuesta usando contexto de documentos
    - Guarda mensajes en sesión para próximas preguntas
    """
    try:
        # Validar entrada
        if not req.question or not req.question.strip():
            raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía")
        
        # Obtener o crear sesión
        session_id = req.session_id
        is_new_session = False
        if not session_id:
            session_id = SessionManager.create_session()
            is_new_session = True
            logger.warning(f"⚠️ Cliente NO envió session_id → Nueva sesión: {session_id}")
        else:
            logger.debug(f"✓ Usando session_id del cliente: {session_id}")
        
        # Obtener contexto previo ANTES de guardar el mensaje actual
        context_summary = SessionManager.get_context_summary(session_id)
        
        # Guardar pregunta del usuario
        SessionManager.add_user_message(session_id, req.question)
        
        # Procesar con el servicio (pasando contexto previo)
        result = QueryService.process_query(req.question, context_summary=context_summary)
        
        # Guardar respuesta del asistente
        answer = result.get("answer", "")
        if answer:
            SessionManager.add_assistant_message(session_id, answer)
        
        # Incluir session_id en respuesta para cliente
        result["session_id"] = session_id
        
        # Log para verificar flujo
        active_sessions = SessionManager.get_active_sessions_count()
        logger.debug(f"📊 Sesiones activas: {active_sessions} | Sesión: {session_id}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando consulta: {e}")
        raise HTTPException(status_code=500, detail=f"Error al procesar consulta: {str(e)}")
    