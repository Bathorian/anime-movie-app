from fastapi import FastAPI
from app.db import engine

app = FastAPI(title="Anime Movie APP")

@app.get("/health")
@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.on_event("shutdown")
async def shutdown():
    await engine.dispose()
