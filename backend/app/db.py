import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")
if os.name == "nt":
    load_dotenv(PROJECT_ROOT / ".env.host")

DATABASE_URL = (
    os.getenv("APP_DATABASE_URL")
    or os.getenv("IMDB_DATABASE_URL")
    or os.getenv("DATABASE_URL")
    or "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/imdb"
)
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with SessionLocal() as session:
        yield session
