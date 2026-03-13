import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from sst_agent.app.services.document_service import DocumentService
from sst_agent.app.rag.loader import DATA_FOLDER

router = APIRouter(prefix="/api", tags=["documents"])

logger = logging.getLogger(__name__)


@router.get("/documents")
def list_documents():
    """
    Lista todos los documentos en la carpeta data/docs.
    
    Retorna información como nombre, fecha, estado de indexación y tamaño.
    """
    try:
        result = DocumentService.list_documents()
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error listando documentos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Sube un documento (PDF, DOCX o TXT) y lo indexa automáticamente.
    
    Args:
        file: Archivo a subir
        
    Returns:
        Dict con estado de carga e indexación
    """
    try:
        # Validar formato
        if not file.filename.lower().endswith(('.pdf', '.docx', '.txt')):
            raise HTTPException(
                status_code=400,
                detail="Solo se permiten archivos PDF, DOCX o TXT"
            )
        
        # Guardar documento
        file_path = f"{DATA_FOLDER}/{file.filename}"
        content = await file.read()
        
        DocumentService.save_document(file_path, content, file.filename)
        logger.info(f"Archivo guardado: {file.filename}")
        
        # Indexar automáticamente
        try:
            index_result = DocumentService.index_document(file_path, file.filename)
            
            return JSONResponse(content={
                "status": "success",
                "message": f"Archivo subido e indexado correctamente ({index_result.get('chunks', 0)} chunks)",
                "filename": file.filename,
                "chunks": index_result.get("chunks")
            })
            
        except Exception as index_error:
            logger.error(f"Error al indexar: {index_error}")
            # El archivo se guardó pero no se indexó
            return JSONResponse(
                status_code=202,
                content={
                    "status": "partial_success",
                    "message": f"Archivo guardado pero error al indexar: {str(index_error)}",
                    "filename": file.filename
                }
            )
        
    except HTTPException:
        raise
    except FileExistsError as e:
        logger.warning(f"Archivo duplicado: {e}")
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Error subiendo archivo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{filename}")
def delete_document(filename: str):
    """
    Elimina un documento del sistema.
    
    Elimina tanto el archivo como sus embeddings de la base de datos.
    
    Args:
        filename: Nombre del archivo a eliminar
        
    Returns:
        Dict con estado de eliminación
    """
    try:
        # Validar formato
        if not filename.lower().endswith(('.pdf', '.docx', '.txt')):
            raise HTTPException(
                status_code=400,
                detail="Solo se pueden eliminar archivos PDF, DOCX o TXT"
            )
        
        result = DocumentService.delete_document(filename)
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except FileNotFoundError as e:
        logger.warning(f"Archivo no encontrado: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error eliminando documento: {e}")
        raise HTTPException(status_code=500, detail=str(e))
