from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from sst_agent.app.services.query_service import QueryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


class Query(BaseModel):
    """Modelo de solicitud de query."""
    question: str


@router.post("/query")
def query(req: Query):
    """
    Procesa una consulta del usuario.
    
    Detecta intenciones (saludos, preguntas, etc) y genera una respuesta
    usando el contexto de documentos indexados.
    """
    try:
        # Validar entrada
        if not req.question or not req.question.strip():
            raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía")
        
        # Procesar con el servicio
        result = QueryService.process_query(req.question)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando consulta: {e}")
        raise HTTPException(status_code=500, detail=f"Error al procesar consulta: {str(e)}")
    