from sentence_transformers import SentenceTransformer
from sst_agent.app.core.config import EMBEDDING_MODEL
from typing import List
import numpy as np

_model = None

def load_model():
    """Carga el modelo de embeddings (singleton)."""
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model

def embed_text(texts: List[str]) -> np.ndarray:
    """
    Genera embeddings para una lista de textos.
    
    Args:
        texts: Lista de textos a convertir en embeddings
        
    Returns:
        np.ndarray: Array de embeddings
    """
    model = load_model()
    return model.encode(texts)

def get_embedding_dimension() -> int:
    """Retorna la dimensión de los embeddings del modelo."""
    model = load_model()
    return model.get_sentence_embedding_dimension()
