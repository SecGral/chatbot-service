from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sst_agent.app.api.routes import router
from sst_agent.app.core.config import PROJECT_NAME, VERSION
from sst_agent.app.services.db import init_db
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title=PROJECT_NAME, version=VERSION)

# Inicializar base de datos al arrancar la aplicación
try:
    init_db()
    logger.info("✓ Base de datos inicializada correctamente")
except Exception as e:
    logger.error(f"✗ Error al inicializar la base de datos: {e}")

# Configurar CORS para permitir peticiones del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Agregar más orígenes si es necesario
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API
app.include_router(router)

# Frontend
#app.mount("/", StaticFiles(directory="sst_agent/app/static", html=True), name="static")

@app.get("/health")
def health():
    return {"status": "ok"}
