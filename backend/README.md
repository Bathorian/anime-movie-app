## Backend

Local run:

```bash
uv sync
uv run uvicorn app.main:app --reload
```

Run SQL migrations manually:

```bash
uv run python -m app.migrations
```

Notes:

- `backend/.env` is for Docker (`db:5432`).
- `backend/.env.host` is for host-side commands (`localhost:5433`).
- Local `uvicorn` reads `APP_DATABASE_URL` first.
- Movie descriptions are fetched from OMDb by IMDb ID (example: `tt0245090`).
- Set `OMDB_API_KEY` to use your own key (defaults to the public demo key when empty).
