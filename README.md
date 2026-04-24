# anime-movie-app

## Run with Docker

1. Make sure `backend/.env` exists (or copy from `backend/.env.example`).
2. Start the stack:

```bash
docker compose up --build
```

Services:
- Frontend: `http://localhost`
- Backend health: `http://localhost:8000/health`
