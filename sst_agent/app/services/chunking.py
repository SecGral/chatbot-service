"""
Utilidades para dividir documentos en chunks más pequeños.
"""
from typing import List
import re


def split_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Divide un texto largo en chunks más pequeños con solapamiento.
    
    Args:
        text: Texto completo a dividir
        chunk_size: Tamaño máximo de cada chunk en caracteres
        overlap: Número de caracteres que se solapan entre chunks
        
    Returns:
        List[str]: Lista de chunks de texto
    """
    # Limpiar espacios múltiples y saltos de línea excesivos
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Calcular el final del chunk
        end = start + chunk_size
        
        # Si no es el último chunk, buscar un buen punto de corte
        if end < len(text):
            # Buscar el último punto, salto de línea o espacio
            cutoff = max(
                text.rfind('.', start, end),
                text.rfind('\n', start, end),
                text.rfind(' ', start, end)
            )
            
            # Si encontramos un buen punto de corte, usarlo
            if cutoff > start:
                end = cutoff + 1
        
        # Extraer el chunk
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Mover el inicio con solapamiento
        start = end - overlap if end < len(text) else len(text)
    
    return chunks


def split_by_sections(text: str, max_chunk_size: int = 2000) -> List[str]:
    """
    Divide un documento en chunks usando chunking simple mejorado.
    
    Args:
        text: Texto completo
        max_chunk_size: Tamaño máximo de cada chunk
        
    Returns:
        List[str]: Lista de chunks
    """
    # Usar chunking simple con overlap
    return split_into_chunks(text, chunk_size=max_chunk_size, overlap=200)
