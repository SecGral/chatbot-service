from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pgvector.sqlalchemy import Vector
from datetime import datetime
from sst_agent.app.core.config import DATABASE_URL, EMBEDDING_DIMENSION
from typing import List
import logging

logger = logging.getLogger(__name__)

# Configuración de SQLAlchemy
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Document(Base):
    """Modelo para almacenar documentos y sus embeddings (ahora con chunks)."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, index=True)
    chunk_index = Column(Integer, default=0)  # Índice del chunk dentro del documento
    content = Column(Text, nullable=False)  # Contenido del chunk
    content_preview = Column(Text)  # Primeros 200 caracteres para preview
    embedding = Column(Vector(EMBEDDING_DIMENSION))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', chunk={self.chunk_index})>"


def init_db():
    """
    Inicializa la base de datos creando la extensión pgvector y las tablas.
    """
    try:
        # Crear extensión pgvector
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        logger.info("Base de datos inicializada correctamente")
        return True
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}")
        raise


def get_db() -> Session:
    """
    Crea una sesión de base de datos.
    Usar con context manager: with get_db() as db:
    """
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


def add_document(filename: str, content: str, embedding: List[float], chunk_index: int = 0) -> Document:
    """
    Añade un chunk de documento a la base de datos.
    
    Args:
        filename: Nombre del archivo
        content: Contenido del chunk
        embedding: Vector de embedding del contenido
        chunk_index: Índice del chunk (para chunks del mismo documento)
        
    Returns:
        Document: El documento creado
    """
    db = SessionLocal()
    try:
        # Validar que el documento con este filename no tenga este mismo chunk
        existing = db.query(Document).filter(
            Document.filename == filename,
            Document.chunk_index == chunk_index
        ).first()
        
        if existing:
            logger.warning(f"Chunk {chunk_index} de '{filename}' ya existe, omitiendo duplicado")
            return existing
        
        # Crear preview del contenido (primeros 200 caracteres)
        content_preview = content[:200] if len(content) > 200 else content
        
        doc = Document(
            filename=filename,
            chunk_index=chunk_index,
            content=content,
            content_preview=content_preview,
            embedding=embedding
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        logger.info(f"Documento '{filename}' chunk {chunk_index} añadido con ID {doc.id}")
        return doc
    except Exception as e:
        db.rollback()
        logger.error(f"Error al añadir documento: {e}")
        raise
    finally:
        db.close()


def document_exists(filename: str) -> bool:
    """
    Verifica si un documento (cualquier chunk) ya existe en la base de datos.
    
    Args:
        filename: Nombre del archivo a verificar
        
    Returns:
        bool: True si existe al menos un chunk, False si no
    """
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.filename == filename).first()
        return doc is not None
    finally:
        db.close()


def delete_document_chunks(filename: str):
    """
    Elimina todos los chunks de un documento específico.
    
    Args:
        filename: Nombre del archivo cuyos chunks se eliminarán
    """
    db = SessionLocal()
    try:
        db.query(Document).filter(Document.filename == filename).delete()
        db.commit()
        logger.info(f"Chunks del documento '{filename}' eliminados")
    except Exception as e:
        db.rollback()
        logger.error(f"Error al eliminar chunks: {e}")
        raise
    finally:
        db.close()


def get_document_count() -> int:
    """
    Retorna el número total de documentos indexados.
    
    Returns:
        int: Cantidad de documentos
    """
    db = SessionLocal()
    try:
        count = db.query(Document).count()
        return count
    finally:
        db.close()


def search_similar_documents(query_embedding: List[float], k: int = 4) -> List[Document]:
    """
    Busca los k documentos más similares usando búsqueda vectorial.
    
    Args:
        query_embedding: Vector de embedding de la consulta
        k: Número de documentos a retornar
        
    Returns:
        List[Document]: Lista de documentos más similares
    """
    db = SessionLocal()
    try:
        # Búsqueda por similitud de coseno usando pgvector
        # El operador <=> es para distancia de coseno en pgvector
        results = db.query(Document).order_by(
            Document.embedding.cosine_distance(query_embedding)
        ).limit(k).all()
        
        return results
    finally:
        db.close()


def clear_all_documents():
    """
    CUIDADO: Elimina todos los documentos de la base de datos.
    Usar solo para reiniciar el índice.
    """
    db = SessionLocal()
    try:
        db.query(Document).delete()
        db.commit()
        logger.info("Todos los documentos han sido eliminados")
    except Exception as e:
        db.rollback()
        logger.error(f"Error al eliminar documentos: {e}")
        raise
    finally:
        db.close()
