import asyncio
from pathlib import Path

from sqlalchemy import text

from app.db import engine

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"


def _split_statements(sql_script: str) -> list[str]:
    return [statement.strip() for statement in sql_script.split(";") if statement.strip()]


async def run_migrations() -> None:
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        return

    async with engine.begin() as connection:
        await connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        )

        applied_result = await connection.execute(text("SELECT version FROM schema_migrations"))
        applied_versions = set(applied_result.scalars().all())

        for migration_file in migration_files:
            version = migration_file.name
            if version in applied_versions:
                continue

            sql_script = migration_file.read_text(encoding="utf-8")
            for statement in _split_statements(sql_script):
                await connection.execute(text(statement))

            await connection.execute(
                text("INSERT INTO schema_migrations (version) VALUES (:version)"),
                {"version": version},
            )


async def _main() -> None:
    await run_migrations()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
