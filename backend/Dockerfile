FROM python:3.12-slim

RUN pip install --no-cache-dir uv
ENV UV_PROJECT_ENVIRONMENT=/usr/local
WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
