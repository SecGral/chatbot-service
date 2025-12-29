from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sst_agent.app.api.routes import router
from sst_agent.app.core.config import PROJECT_NAME, VERSION

app = FastAPI(title=PROJECT_NAME, version=VERSION)

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
