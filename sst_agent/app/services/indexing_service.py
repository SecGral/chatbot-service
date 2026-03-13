"""
Servicio de indexación de documentos.
Orquesta el proceso completo de carga, chunking y embedding.
"""
import os
import logging
from typing import Dict, Any

from sst_agent.app.rag import vector_db
from sst_agent.app.rag.loader import load_file
from sst_agent.app.rag.chunking import split_by_sections
from sst_agent.app.rag.embeddings import embed_text

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 1200


class IndexingService:
    """Servicio de indexación de documentos."""
    
    @staticmethod
    def index_single_document(file_path: str, filename: str) -> Dict[str, Any]:
        """
        Indexa un único documento.
        
        Args:
            file_path: Ruta completa del archivo
            filename: Nombre del archivo
            
        Returns:
            Dict: Información de indexación
        """
        logger.info(f"Indexando '{filename}'...")
        
        try:
            # Verificar si ya está indexado
            if vector_db.document_exists(filename):
                logger.info(f"Documento '{filename}' ya indexado, saltando...")
                return {
                    "status": "skipped",
                    "filename": filename,
                    "chunks": 0
                }
            
            # Cargar documento
            content = load_file(file_path)
            
            # Dividir en chunks
            chunks = split_by_sections(content, max_chunk_size=DEFAULT_CHUNK_SIZE)
            logger.info(f"  Dividido en {len(chunks)} chunks")
            
            # Procesar cada chunk
            for chunk_idx, chunk in enumerate(chunks):
                embedding = embed_text([chunk])[0].tolist()
                
                if vector_db.add_document_chunk(filename, chunk, embedding, chunk_idx):
                    logger.debug(f"  ✓ Chunk {chunk_idx + 1}/{len(chunks)} indexado")
                else:
                    logger.error(f"  ✗ Error en chunk {chunk_idx + 1}")
            
            logger.info(f"✓ '{filename}' indexado con {len(chunks)} chunks")
            
            return {
                "status": "success",
                "filename": filename,
                "chunks": len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Error indexando '{filename}': {e}")
            raise
    
    @staticmethod
    def index_all_documents(file_list: list) -> Dict[str, Any]:
        """
        Indexa todos los documentos de una lista.
        
        Args:
            file_list: Lista de rutas de archivos
            
        Returns:
            Dict: Resumen de indexación
        """
        logger.info(f"Iniciando indexación de {len(file_list)} documentos...")
        
        # Inicializar base de datos
        vector_db.init_vector_db()
        
        indexed = 0
        skipped = 0
        errors = []
        
        for file_path in file_list:
            filename = os.path.basename(file_path)
            
            try:
                result = IndexingService.index_single_document(file_path, filename)
                
                if result["status"] == "success":
                    indexed += 1
                elif result["status"] == "skipped":
                    skipped += 1
                    
            except Exception as e:
                logger.error(f"Error procesando {filename}: {e}")
                errors.append({
                    "filename": filename,
                    "error": str(e)
                })
        
        total_docs = vector_db.get_indexed_count()
        
        return {
            "status": "completed",
            "indexed": indexed,
            "skipped": skipped,
            "errors": len(errors),
            "total_docs": total_docs,
            "error_details": errors if errors else None
        }
    
    @staticmethod
    def get_indexing_status() -> Dict[str, Any]:
        """
        Obtiene el estado actual de la indexación.
        
        Returns:
            Dict: Estado de indexación
        """
        try:
            count = vector_db.get_indexed_count()
            return {
                "indexed": count > 0,
                "document_count": count,
                "message": f"Hay {count} documentos indexados" if count > 0 else "No hay documentos indexados"
            }
        except Exception as e:
            logger.error(f"Error verificando estado: {e}")
            raise
