from fastapi import FastAPI
from sst_agent.app.api.routes import router
from sst_agent.app.core.config import PROJECT_NAME, VERSION

app = FastAPI(title=PROJECT_NAME, version=VERSION)

app.include_router(router)

@app.get("/")
def root():
    return {"message": "SST Agent funcionando ✅"}
