"""
Servicio de gestión de documentos.
Operaciones CRUD de documentos en el sistema.
"""
import os
import logging
from datetime import datetime
from typing import List, Dict, Any

from sst_agent.app.rag import vector_db
from sst_agent.app.rag.loader import DATA_FOLDER
from sst_agent.app.services.indexing_service import IndexingService

logger = logging.getLogger(__name__)


class DocumentService:
    """Servicio de gestión de documentos."""
    
    @staticmethod
    def list_documents() -> Dict[str, Any]:
        """
        Lista todos los documentos en la carpeta de datos.
        
        Returns:
            Dict: Lista de documentos con información
        """
        try:
            docs_path = DATA_FOLDER
            
            if not os.path.exists(docs_path):
                logger.warning(f"Carpeta de documentos no existe: {docs_path}")
                return {
                    "documents": [],
                    "total": 0,
                    "message": f"Carpeta no existe: {docs_path}"
                }
            
            documents = []
            
            # Listar solo archivos soportados
            for filename in os.listdir(docs_path):
                if filename.lower().endswith(('.pdf', '.docx', '.txt')):
                    filepath = os.path.join(docs_path, filename)
                    
                    try:
                        file_stats = os.stat(filepath)
                        is_indexed = vector_db.document_exists(filename)
                        
                        documents.append({
                            "nombre": filename,
                            "fecha": datetime.fromtimestamp(file_stats.st_mtime).strftime("%d/%m/%Y"),
                            "estado": "Procesado" if is_indexed else "Pendiente",
                            "size": file_stats.st_size
                        })
                    except Exception as e:
                        logger.warning(f"Error obteniendo info de {filename}: {e}")
            
            # Ordenar por fecha (más recientes primero)
            documents.sort(key=lambda x: x["fecha"], reverse=True)
            
            logger.info(f"Listados {len(documents)} documentos")
            
            return {
                "documents": documents,
                "total": len(documents)
            }
            
        except Exception as e:
            logger.error(f"Error listando documentos: {e}")
            raise
    
    @staticmethod
    def save_document(file_path: str, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Guarda un documento en la carpeta de datos.
        
        Args:
            file_path: Ruta destino
            file_content: Contenido del archivo
            filename: Nombre del archivo
            
        Returns:
            Dict: Estado del guardado
        """
        try:
            docs_path = DATA_FOLDER
            os.makedirs(docs_path, exist_ok=True)
            
            # Verificar si ya existe
            if os.path.exists(file_path):
                raise FileExistsError(f"El archivo {filename} ya existe")
            
            # Guardar archivo
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            logger.info(f"Archivo guardado: {filename}")
            
            return {
                "status": "success",
                "filename": filename,
                "path": file_path
            }
            
        except FileExistsError as e:
            logger.warning(f"Archivo duplicado: {e}")
            raise
        except Exception as e:
            logger.error(f"Error guardando documento: {e}")
            raise
    
    @staticmethod
    def index_document(file_path: str, filename: str) -> Dict[str, Any]:
        """
        Indexa un documento.
        
        Args:
            file_path: Ruta del archivo
            filename: Nombre del archivo
            
        Returns:
            Dict: Resultado de indexación
        """
        try:
            return IndexingService.index_single_document(file_path, filename)
        except Exception as e:
            logger.error(f"Error indexando documento: {e}")
            raise
    
    @staticmethod
    def delete_document(filename: str) -> Dict[str, Any]:
        """
        Elimina un documento (archivo y embeddings).
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            Dict: Estado de eliminación
        """
        try:
            docs_path = DATA_FOLDER
            file_path = os.path.join(docs_path, filename)
            
            # Verificar si existe
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Archivo no encontrado: {filename}")
            
            # Eliminar de base de datos
            deleted_from_db = vector_db.delete_document(filename)
            
            # Eliminar archivo físico
            os.remove(file_path)
            
            logger.info(f"Documento eliminado: {filename}")
            
            return {
                "status": "success",
                "filename": filename,
                "deleted_from_db": deleted_from_db
            }
            
        except FileNotFoundError as e:
            logger.warning(f"Archivo no encontrado: {e}")
            raise
        except Exception as e:
            logger.error(f"Error eliminando documento: {e}")
            raise
