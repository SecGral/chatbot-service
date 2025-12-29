from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sst_agent.app.services.embeddings import embed_text, get_embedding_dimension
from sst_agent.app.services import vector_db
from sst_agent.app.services.loader import get_all_files, load_file
from sst_agent.app.services.chunking import split_by_sections
from sst_agent.app.services.llm import generate
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


class Query(BaseModel):
    question: str


class IndexResponse(BaseModel):
    status: str
    indexed: int
    skipped: int
    total_docs: int
    message: str



@router.get("/health")
def health_check():
    """Endpoint de health check."""
    try:
        # Verificar conexión a base de datos
        count = vector_db.get_indexed_count()
        return {
            "status": "ok",
            "documents_indexed": count
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/index/status")
def index_status():
    """Verifica el estado de la indexación."""
    try:
        count = vector_db.get_indexed_count()
        return {
            "indexed": count > 0,
            "document_count": count,
            "message": f"Hay {count} documentos indexados" if count > 0 else "No hay documentos indexados"
        }
    except Exception as e:
        logger.error(f"Error verificando estado: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index", response_model=IndexResponse)
def index_docs():
    """
    Indexa los documentos PDF/DOCX/TXT en la carpeta data/docs.
    Solo indexa documentos que no existen en la base de datos.
    """
    try:
        # Inicializar base de datos si es necesario
        vector_db.init_vector_db()
        
        # Obtener archivos a indexar
        files = get_all_files()
        
        if not files:
            return IndexResponse(
                status="warning",
                indexed=0,
                skipped=0,
                total_docs=vector_db.get_indexed_count(),
                message="No se encontraron archivos para indexar en data/docs"
            )
        
        indexed = 0
        skipped = 0
        
        for file_path in files:
            filename = os.path.basename(file_path)
            
            # Verificar si ya está indexado
            if vector_db.document_exists(filename):
                logger.info(f"Documento '{filename}' ya indexado, saltando...")
                skipped += 1
                continue
            
            # Cargar documento
            logger.info(f"Indexando '{filename}'...")
            content = load_file(file_path)
            
            # Dividir en chunks más pequeños para evitar exceder límites del LLM
            chunks = split_by_sections(content, max_chunk_size=1200)
            logger.info(f"  Dividido en {len(chunks)} chunks")
            
            # Procesar cada chunk
            for chunk_idx, chunk in enumerate(chunks):
                # Generar embedding para este chunk
                embedding = embed_text([chunk])[0].tolist()
                
                # Guardar chunk en base de datos
                if vector_db.add_document_chunk(filename, chunk, embedding, chunk_idx):
                    logger.info(f"  ✓ Chunk {chunk_idx + 1}/{len(chunks)} indexado")
                else:
                    logger.error(f"  ✗ Error en chunk {chunk_idx + 1}")
            
            indexed += 1
            logger.info(f"✓ '{filename}' indexado con {len(chunks)} chunks")
        
        total_docs = vector_db.get_indexed_count()
        
        return IndexResponse(
            status="success",
            indexed=indexed,
            skipped=skipped,
            total_docs=total_docs,
            message=f"Indexación completada: {indexed} nuevos, {skipped} ya existentes, {total_docs} total en BD"
        )
        
    except Exception as e:
        logger.error(f"Error en indexación: {e}")
        raise HTTPException(status_code=500, detail=f"Error al indexar: {str(e)}")


@router.post("/query")
def query(req: Query):
    """
    Procesa una consulta usando los documentos indexados.
    """
    try:
        question = req.question.strip()
        question_lower = question.lower()
        
        # Detectar si es SOLO un saludo (sin pregunta adicional)
        saludos_simples = ["hola", "buenos dias", "buenas tardes", "buenas noches", "hey", "holi", "saludos"]
        despedidas_simples = ["adios", "chao", "hasta luego", "nos vemos", "bye", "adiós"]
        agradecimientos_simples = ["gracias", "muchas gracias", "thanks", "thank you"]
        
        # Verificar si es SOLO un saludo (máximo 5 palabras y contiene saludo)
        palabras = question_lower.split()
        es_solo_saludo = len(palabras) <= 3 and any(saludo == question_lower or question_lower.startswith(saludo) for saludo in saludos_simples)
        es_solo_despedida = len(palabras) <= 3 and any(despedida in question_lower for despedida in despedidas_simples)
        es_solo_agradecimiento = len(palabras) <= 4 and any(agradecimiento == question_lower for agradecimiento in agradecimientos_simples)
        
        # Responder SOLO si es únicamente un saludo
        if es_solo_saludo:
            return {
                "answer": "¡Hola! 👋 Soy tu asistente especializado en Seguridad y Salud en el Trabajo. ¿En qué puedo ayudarte hoy?",
                "sources": [],
                "context_used": 0
            }
        
        # Responder SOLO si es únicamente una despedida
        if es_solo_despedida:
            return {
                "answer": "¡Hasta pronto! 👋 Que tengas un excelente día.",
                "sources": [],
                "context_used": 0
            }
        
        # Responder SOLO si es únicamente un agradecimiento
        if es_solo_agradecimiento:
            return {
                "answer": "¡De nada! 😊 Estoy aquí para ayudarte cuando lo necesites.",
                "sources": [],
                "context_used": 0
            }
        
        # Si contiene saludo + pregunta, agregar saludo al inicio de la respuesta
        tiene_saludo = any(saludo in palabras[:3] for saludo in saludos_simples)
        
        # Verificar que hay documentos indexados
        doc_count = vector_db.get_indexed_count()
        if doc_count == 0:
            return {
                "error": "No hay documentos indexados. Usa /api/index primero.",
                "answer": None
            }
        
        # Generar embedding de la consulta
        logger.info(f"Procesando consulta: {req.question[:50]}...")
        q_vec = embed_text([req.question])[0].tolist()
        
        # Buscar más chunks para mejor cobertura (aumentado a 5)
        results = vector_db.search_similar(q_vec, k=5)
        
        if not results:
            return {
                "answer": "No encontré información relevante en los documentos indexados.",
                "sources": [],
                "context_used": 0
            }
        
        # Construir contexto con límite flexible
        context_parts = []
        total_chars = 0
        max_context = 3500  # Límite total de caracteres para el contexto
        
        for i, r in enumerate(results, 1):
            chunk_content = r['content']
            # Si agregar este chunk excede el límite, truncarlo
            if total_chars + len(chunk_content) > max_context:
                remaining = max_context - total_chars
                if remaining > 200:  # Solo agregar si quedan al menos 200 chars
                    chunk_content = chunk_content[:remaining]
                else:
                    break
            
            context_parts.append(f"[Fragmento {i}]\n{chunk_content}")
            total_chars += len(chunk_content)
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Generar respuesta con LLM usando un prompt más inteligente
        prompt = f"""Eres un asistente experto en Seguridad y Salud en el Trabajo (SST).

Tu tarea es responder preguntas usando la información del contexto proporcionado.

**INSTRUCCIONES:**
1. Lee CUIDADOSAMENTE todo el contexto
2. Si encuentras la información solicitada, explícala de forma clara y completa
3. Si la palabra exacta no aparece pero hay información relacionada, compártela
4. Si encuentras definiciones, cítalas textualmente
5. Sé conversacional y amigable en tu respuesta
6. SOLO di "no encuentro esa información específica" si realmente NO hay nada relacionado

**CONTEXTO DE LOS DOCUMENTOS:**
{context}

**PREGUNTA DEL USUARIO:**
{req.question}

**TU RESPUESTA:"""

        answer = generate(prompt, max_tokens=1200)
        
        # Si la pregunta tenía saludo al inicio, agregar saludo a la respuesta
        if tiene_saludo:
            answer = "¡Hola! 👋\n\n" + answer
        
        # Preparar lista de fuentes con información de chunks
        sources_list = []
        seen_files = set()
        for r in results:
            if r["file"] not in seen_files:
                sources_list.append({
                    "file": r["file"],
                    "page": f"chunk {r.get('chunk_index', 0)}"
                })
                seen_files.add(r["file"])
        
        return {
            "answer": answer,
            "sources": sources_list,
            "context_used": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error procesando consulta: {e}")
        raise HTTPException(status_code=500, detail=f"Error al procesar consulta: {str(e)}")


@router.delete("/index")
def clear_index():
    """
    CUIDADO: Elimina todos los documentos indexados.
    Usar solo para reiniciar el índice.
    """
    try:
        vector_db.clear_index()
        return {
            "status": "success",
            "message": "Índice limpiado correctamente"
        }
    except Exception as e:
        logger.error(f"Error limpiando índice: {e}")
        raise HTTPException(status_code=500, detail=str(e))
