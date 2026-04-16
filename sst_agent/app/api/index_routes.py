import logging
from fastapi import APIRouter, HTTPException
from sst_agent.app.rag.loader import get_all_files
from sst_agent.app.services.indexing_service import IndexingService

router = APIRouter(prefix="/api", tags=["index"])

logger = logging.getLogger(__name__)


@router.get("/index/status")
def index_status():
    """
    Obtiene el estado actual de la indexación.
    
    Returns:
        Dict con información del estado de indexación
    """
    try:
        status = IndexingService.get_indexing_status()
        return status
    except Exception as e:
        logger.error(f"Error verificando estado: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index")
def index_docs():
    """
    Indexa todos los documentos en la carpeta data/docs.
    
    Solo indexa documentos que no están ya en la base de datos.
    Returns:
        Dict con resumen de indexación (indexed, skipped, total_docs)
    """
    try:
        # Obtener archivos a indexar
        files = get_all_files()
        
        if not files:
            logger.warning("No hay archivos para indexar")
            return {
                "status": "warning",
                "indexed": 0,
                "skipped": 0,
                "total_docs": 0,
                "message": "No se encontraron archivos para indexar en data/docs"
            }
        
        # Procesar con servicio
        result = IndexingService.index_all_documents(files)
        
        return result
        
    except Exception as e:
        logger.error(f"Error indexando: {e}")
        raise HTTPException(status_code=500, detail=f"Error al indexar: {str(e)}")


@router.delete("/index")
def clear_index():
    """
    CUIDADO: Elimina todos los documentos indexados.
    Usar solo para reiniciar el índice.
    """
    try:
        from sst_agent.app.rag import vector_db
        vector_db.clear_index()
        return {
            "status": "success",
            "message": "Índice limpiado correctamente"
        }
    except Exception as e:
        logger.error(f"Error limpiando índice: {e}")
        raise HTTPException(status_code=500, detail=str(e))