from fastapi import APIRouter
from pydantic import BaseModel
from sst_agent.app.services.embeddings import embed_text, load_model
from sst_agent.app.services.vector_db import load_index, add_vectors, search
from sst_agent.app.services.loader import get_all_files, load_file
from sst_agent.app.services.llm import generate
import os


router = APIRouter(prefix="/api")

MODEL_DIM = None
INDEX_LOADED = False

class Query(BaseModel):
    question: str

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.post("/index")
def index_docs():
    global INDEX_LOADED, MODEL_DIM

    model = load_model()
    MODEL_DIM = model.get_sentence_embedding_dimension()

    index = load_index(MODEL_DIM)
    files = get_all_files()

    docs = []
    texts = []

    for path in files:
        content = load_file(path)
        texts.append(content)
        docs.append({"file": os.path.basename(path), "content": content[:1000]})

    vectors = embed_text(texts)
    add_vectors(vectors, docs)

    INDEX_LOADED = True
    return {"indexed": len(docs)}

@router.post("/query")
def query(req: Query):
    global INDEX_LOADED

    if not INDEX_LOADED:
        return {"error": "Primero indexa documentos con /api/index"}

    q_vec = embed_text([req.question])[0]
    results = search(q_vec)

    context = "\n\n".join(r["content"] for r in results)

    prompt = f"""
Eres un especialista en Seguridad y Salud en el Trabajo.

Responde usando SOLO el contexto disponible:

{context}

Pregunta:
{req.question}

Respuesta:
"""

    answer = generate(prompt)
    return {"answer": answer}
