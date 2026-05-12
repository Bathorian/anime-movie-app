from fastapi import FastAPI

from app.db import engine
from app.migrations import run_migrations
from app.routers.movies import router as movies_router

app = FastAPI(title="Anime Movie APP")
app.include_router(movies_router, prefix="/api")


@app.on_event("startup")
async def startup():
    await run_migrations()



@app.get("/health")
@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.on_event("shutdown")
async def shutdown():
    await engine.dispose()
