import logging
import logging.config
import asyncio

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sst_agent.app.core.config import PROJECT_NAME, VERSION
from sst_agent.app.services.db import init_db
from sst_agent.app.api.router import router
from sst_agent.app.services.session_manager import SessionManager

logger = logging.getLogger(__name__)

app = FastAPI(title=PROJECT_NAME, version=VERSION)

# Inicializar base de datos
try:
    init_db()
    logger.info("✓ Base de datos inicializada correctamente")
except Exception as e:
    logger.error(f"✗ Error al inicializar la base de datos: {e}")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


# ← NUEVO: Tarea periódica para limpiar sesiones expiradas
async def cleanup_sessions_task():
    """Limpia sesiones expiradas cada 30 minutos."""
    while True:
        try:
            await asyncio.sleep(1800)  # 30 minutos = 1800 segundos
            count = SessionManager.cleanup_expired_sessions()
            if count > 0:
                logger.info(f"🧹 Limpiadas {count} sesiones expiradas")
        except Exception as e:
            logger.error(f"Error en tarea de limpieza: {e}")


@app.on_event("startup")
async def startup_event():
    """Inicia tareas de fondo al arrancar la app."""
    logger.info("🚀 Iniciando SST Bot...")
    logger.info("📅 Iniciando tarea de limpieza de sesiones (cada 30 min)")
    asyncio.create_task(cleanup_sessions_task())
