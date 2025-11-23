FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package*.json ./

RUN npm ci

COPY frontend/ ./

RUN npm run build


FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry==1.8.4

RUN poetry config virtualenvs.create false

COPY backend/ ./

RUN poetry install --no-interaction --no-ansi --without dev

COPY --from=frontend-builder /frontend/dist ./static

RUN mkdir -p /app/data
RUN mkdir -p /app/alembic/versions

EXPOSE 8000

CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
