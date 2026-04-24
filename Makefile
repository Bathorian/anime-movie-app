.PHONY: up down build logs migrate migration shell-db shell-backend backend frontend

up:
	docker compose up

down:
	docker compose down

build:
	docker compose up --build

logs:
	docker compose logs -f

migrate:
	docker compose run --rm backend alembic upgrade head

migration:
	docker compose run --rm backend alembic revision --autogenerate -m "$(name)"

shell-db:
	docker compose exec db psql -U user -d imdb

shell-backend:
	docker compose exec backend sh

backend:
	cd backend && uv run uvicorn app.main:app --reload

frontend:
	npm --prefix frontend run dev
