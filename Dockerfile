# Multi-stage build for single container deployment
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build frontend static files
RUN npm run build


# Python backend stage
FROM python:3.11-slim

WORKDIR /app

# Install poetry
RUN pip install poetry==1.8.4

# Configure poetry to not create virtual env
RUN poetry config virtualenvs.create false

# Copy backend application code first
COPY backend/ ./

# Update lock file if pyproject.toml changed
RUN poetry lock --no-update

# Install all dependencies (both SQLite and PostgreSQL drivers included)
RUN poetry install --no-interaction --no-ansi --without dev

# Copy frontend build from previous stage
COPY --from=frontend-builder /frontend/dist ./static

# Create directory for SQLite database
RUN mkdir -p /app/data

# Create directory for alembic migrations if needed
RUN mkdir -p /app/alembic/versions

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run database migrations and start the application
CMD alembic upgrade head && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000
