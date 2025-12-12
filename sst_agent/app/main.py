from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sst_agent.app.api.routes import router
from sst_agent.app.core.config import PROJECT_NAME, VERSION

app = FastAPI(title=PROJECT_NAME, version=VERSION)

# API
app.include_router(router)

# Frontend
app.mount("/", StaticFiles(directory="sst_agent/app/static", html=True), name="static")

@app.get("/health")
def health():
    return {"status": "ok"}
