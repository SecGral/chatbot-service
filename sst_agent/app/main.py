import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sst_agent.app.core.config import PROJECT_NAME, VERSION
from sst_agent.app.services.db import init_db
from sst_agent.app.api.router import router

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
