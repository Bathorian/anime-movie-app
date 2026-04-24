## Backend

Local run:

```bash
uv sync
uv run uvicorn app.main:app --reload
```

Alembic:

```bash
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "message"
```

Notes:

- `backend/.env` is for Docker (`db:5432`).
- `backend/.env.host` is for host-side Alembic commands (`localhost:5433`).
- Alembic reads `ALEMBIC_DATABASE_URL` first.
- Local `uvicorn` reads `APP_DATABASE_URL` first.
