"""
Módulo de abstracción para operaciones con la base de datos vectorial.
Ahora usa PostgreSQL con pgvector en lugar de FAISS.
"""
import logging
from typing import List, Dict
from sst_agent.app.services import db

logger = logging.getLogger(__name__)

MAX_CHUNKS_PER_DOC = 2
SEARCH_MULTIPLIER = 3

def init_vector_db():
    """
    Inicializa la base de datos vectorial (PostgreSQL + pgvector).
    """
    try:
        db.init_db()
        logger.info("Base de datos vectorial inicializada")
        return True
    except Exception as e:
        logger.error(f"Error inicializando base de datos vectorial: {e}")
        raise

def add_document_chunk(filename: str, content: str, embedding: List[float], chunk_index: int = 0) -> bool:
    """
    Añade un chunk de documento con su embedding a la base de datos.
    
    Args:
        filename: Nombre del archivo
        content: Contenido del chunk
        embedding: Vector de embedding
        chunk_index: Índice del chunk
        
    Returns:
        bool: True si se añadió correctamente
    """
    try:
        db.add_document(filename, content, embedding, chunk_index)
        return True
    except Exception as e:
        logger.error(f"Error añadiendo chunk de documento: {e}")
        return False

def delete_document(filename: str) -> bool:
    """
    Elimina todos los chunks de un documento.
    
    Args:
        filename: Nombre del archivo
        
    Returns:
        bool: True si se eliminó correctamente
    """
    try:
        db.delete_document_chunks(filename)
        return True
    except Exception as e:
        logger.error(f"Error eliminando documento: {e}")
        return False

def document_exists(filename: str) -> bool:
    """
    Verifica si un documento ya está indexado.
    
    Args:
        filename: Nombre del archivo
        
    Returns:
        bool: True si existe
    """
    return db.document_exists(filename)

def get_indexed_count() -> int:
    """
    Retorna el número de documentos indexados.
    
    Returns:
        int: Cantidad de documentos
    """
    return db.get_document_count()

def search_similar(query_embedding: List[float], k: int = 5) -> List[Dict]:
    """
    Busca los k chunks más similares a la consulta.
    Limitando la cantidad de chunks por documento para mejorar diversidad.
    """
    try:
        if not query_embedding:
            logger.error("Embedding de consulta vacío")
            return []

        documents = db.search_similar_documents(query_embedding, k * SEARCH_MULTIPLIER)

        results = []
        seen_files = {}

        for doc in documents:
            filename = doc.filename

            if seen_files.get(filename, 0) >= MAX_CHUNKS_PER_DOC:
                continue

            results.append({
                "file": filename,
                "content": doc.content,
                "chunk_index": doc.chunk_index,
                "score": getattr(doc, "similarity", None)
                # El campo "score" es opcional, pero puede ser útil para futuras mejoras como el filtrado de respuestas
            })

            seen_files[filename] = seen_files.get(filename, 0) + 1

            if len(results) >= k:
                break

        return results

    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        return []

def clear_index():
    """
    Limpia todos los documentos del índice.
    CUIDADO: Esta operación es irreversible.
    """
    try:
        db.clear_all_documents()
        logger.info("Índice limpiado")
        return True
    except Exception as e:
        logger.error(f"Error limpiando índice: {e}")
        return False
