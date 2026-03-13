from fastapi import APIRouter
from sst_agent.app.rag import vector_db

router = APIRouter(prefix="/api", tags=["health"])

@router.get("/health")
def health_check():
    try:
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
    