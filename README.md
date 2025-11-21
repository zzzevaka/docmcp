# DocMCP - Documentation as MCP

DocMCP is a web application that allows individuals and teams to create project documentation and expose it as MCP (Model Context Protocol) for LLM agents.

## Tech Stack

- **Backend**: Python 3.11+ with FastAPI
- **Frontend**: React with Vite
- **Database**: PostgreSQL 15
- **Deployment**: Docker Compose
- **Load Balancer**: NGINX with SSL

## Project Structure

```
docs_mcp/
├── backend/               # FastAPI backend application
│   ├── app/              # Application code
│   ├── alembic/          # Database migrations
│   ├── tests/            # Unit tests
│   ├── Dockerfile        # Backend Docker configuration
│   └── pyproject.toml    # Python dependencies (Poetry)
├── frontend/             # React frontend application
│   ├── src/              # Source code
│   ├── Dockerfile        # Frontend Docker configuration
│   └── package.json      # JavaScript dependencies
├── nginx/                # NGINX configuration
│   ├── nginx.conf        # NGINX config file
│   └── ssl/              # Self-signed SSL certificates
├── docker-compose.yml    # Docker Compose configuration
├── .env                  # Environment variables (copy from .env.example)
├── .env.example          # Environment variables template
└── README.md             # This file
```

## Quick Start

### Prerequisites

- Docker
- Docker Compose

### Installation

1. Clone the repository or navigate to the project directory

2. Copy the environment file:
   ```bash
   cp .env.example .env
   ```

3. Start the application:
   ```bash
   docker-compose up --build
   ```

4. Wait for all services to start. The application will be available at:
   - **HTTPS**: https://localhost:9443 (recommended)
   - **HTTP**: http://localhost:9080 (redirects to HTTPS)
   - **Backend API**: https://localhost:9443/api/v1
   - **Health Check**: https://localhost:9443/health

### Accessing the Services Directly

During development, you can also access services directly:
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:5173
- **Database**: localhost:5432

## Development

### Backend Development

The backend uses Poetry for dependency management. See `backend/README.md` for details.

```bash
# Run tests
docker-compose exec backend poetry run pytest

# Run migrations
docker-compose exec backend poetry run alembic upgrade head
```

### Frontend Development

The frontend uses npm/vite. See `frontend/README.md` for details.

```bash
# Run tests
docker-compose exec frontend npm test

# Lint code
docker-compose exec frontend npm run lint
```

## Stopping the Application

```bash
docker-compose down
```

To also remove volumes (database data):
```bash
docker-compose down -v
```

## SSL Certificates

The project includes self-signed SSL certificates for local development. Your browser will show a security warning - this is expected for self-signed certificates. You can safely proceed to the site during development.

## Environment Variables

Key environment variables (see `.env.example`):

- `POSTGRES_USER`: Database user (default: app)
- `POSTGRES_PASSWORD`: Database password (default: app)
- `POSTGRES_DB`: Database name (default: app)
- `DATABASE_URL`: Full database connection string
- `APP_ENV`: Application environment (dev/prod)
- `GOOGLE_CLIENT_ID`: Google OAuth client ID (for authentication)

## Architecture

The application follows a microservices architecture:

1. **NGINX**: Entry point, handles SSL termination and routes requests
2. **Frontend**: React SPA served by Vite dev server (production: static files)
3. **Backend**: FastAPI application with REST API
4. **Database**: PostgreSQL for data persistence

Request flow:
```
Client -> NGINX (SSL) -> Frontend (/) or Backend (/api)
                              ↓
                         PostgreSQL
```

## Next Steps

- Implement authentication (Task-2)
- Add user and team management
- Implement project and document features (Task-3)
- Add document library (Task-4)
- Implement MCP endpoints

## License

TBD
