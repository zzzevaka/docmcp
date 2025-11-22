# Development Guide

Complete guide for developers working on DocMCP.

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

## Getting Started

### Prerequisites

- Docker and Docker Compose installed on your machine
- 2GB of available RAM
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd docs_mcp
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` if you need to customize database credentials or Google OAuth settings.

3. **Launch the application**
   ```bash
   docker-compose up --build
   ```

4. **Access DocMCP**

   Once all services are running, open your browser:
   - **Application**: https://localhost:9443
   - **API Docs**: https://localhost:9443/api/v1/docs
   - **Health Check**: https://localhost:9443/health

   Note: You'll see a security warning due to self-signed SSL certificates. This is normal for local development.

### Accessing the Services Directly

During development, you can also access services directly:
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:5173
- **Database**: localhost:5432

## Development Workflow

### Backend Development

The backend uses Poetry for dependency management. See `backend/README.md` for details.

#### Running Tests

```bash
# Run all tests
docker-compose exec backend poetry run pytest

# Run with coverage
docker-compose exec backend poetry run pytest --cov=app

# Run specific test file
docker-compose exec backend poetry run pytest tests/test_example.py
```

#### Database Migrations

```bash
# Create a new migration
docker-compose exec backend poetry run alembic revision --autogenerate -m "description"

# Run migrations
docker-compose exec backend poetry run alembic upgrade head

# Rollback migration
docker-compose exec backend poetry run alembic downgrade -1
```

#### Code Quality

```bash
# Format code
docker-compose exec backend poetry run black app/

# Lint code
docker-compose exec backend poetry run ruff check app/

# Type checking
docker-compose exec backend poetry run mypy app/
```

### Frontend Development

The frontend uses npm/vite. See `frontend/README.md` for details.

#### Running Tests

```bash
# Run tests
docker-compose exec frontend npm test

# Run tests in watch mode
docker-compose exec frontend npm test -- --watch

# Run tests with coverage
docker-compose exec frontend npm test -- --coverage
```

#### Code Quality

```bash
# Lint code
docker-compose exec frontend npm run lint

# Fix linting issues
docker-compose exec frontend npm run lint:fix

# Type checking
docker-compose exec frontend npm run type-check

# Format code
docker-compose exec frontend npm run format
```

#### Build

```bash
# Build for production
docker-compose exec frontend npm run build

# Preview production build
docker-compose exec frontend npm run preview
```

## Environment Variables

Key environment variables (see `.env.example`):

### Database Configuration

- `POSTGRES_USER`: Database user (default: app)
- `POSTGRES_PASSWORD`: Database password (default: app)
- `POSTGRES_DB`: Database name (default: app)
- `DATABASE_URL`: Full database connection string

### Application Configuration

- `APP_ENV`: Application environment (dev/prod)
- `SECRET_KEY`: Secret key for session encryption
- `CORS_ORIGINS`: Allowed CORS origins (comma-separated)

### Authentication

- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret

### MCP Configuration

- `MCP_SERVER_URL`: Base URL for MCP server
- `MCP_TIMEOUT`: Timeout for MCP requests (default: 30s)

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

### Component Details

#### NGINX
- SSL termination with self-signed certificates (development)
- Reverse proxy for frontend and backend
- Static file serving in production
- Port 9443 (HTTPS), 9080 (HTTP, redirects to HTTPS)

#### Frontend
- React 18+ with TypeScript
- Vite for development and building
- React Router for navigation
- TanStack Query for data fetching
- Tailwind CSS for styling
- shadcn/ui for UI components

#### Backend
- FastAPI with Python 3.11+
- SQLAlchemy ORM for database access
- Alembic for migrations
- Pydantic for validation
- OAuth2 for authentication
- MCP server implementation

#### Database
- PostgreSQL 15
- Stores users, projects, documents, templates
- Full-text search capabilities
- JSONB for flexible document metadata

## SSL Certificates

The project includes self-signed SSL certificates for local development in the `nginx/ssl/` directory.

### Generating New Certificates

If you need to regenerate the SSL certificates:

```bash
cd nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx-selfsigned.key \
  -out nginx-selfsigned.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

Your browser will show a security warning for self-signed certificates. This is expected and safe for local development.

## Stopping the Application

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (database data)
docker-compose down -v

# Stop and remove everything including images
docker-compose down -v --rmi all
```

## Debugging

### Backend Debugging

```bash
# View backend logs
docker-compose logs -f backend

# Access backend shell
docker-compose exec backend bash

# Access Python shell with app context
docker-compose exec backend poetry run python
```

### Frontend Debugging

```bash
# View frontend logs
docker-compose logs -f frontend

# Access frontend shell
docker-compose exec frontend sh

# Access Node REPL
docker-compose exec frontend node
```

### Database Debugging

```bash
# Access PostgreSQL shell
docker-compose exec db psql -U app -d app

# View database logs
docker-compose logs -f db

# Backup database
docker-compose exec db pg_dump -U app app > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T db psql -U app app
```

## Common Issues

### Port Already in Use

If ports 9443, 9080, 8000, 5173, or 5432 are already in use:

1. Find and stop the conflicting process
2. Or modify the ports in `docker-compose.yml`

### Database Connection Issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d db
# Wait for db to be ready
docker-compose up backend frontend
```

### Frontend Hot Reload Not Working

```bash
# Rebuild frontend container
docker-compose up -d --build frontend
```

## Contributing

### Code Style

- Follow PEP 8 for Python code
- Use TypeScript for all new frontend code
- Write meaningful commit messages
- Add tests for new features
- Update documentation

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Run tests and linting
4. Update documentation if needed
5. Submit pull request with clear description
6. Wait for code review

### Running CI Locally

```bash
# Run all checks
./scripts/ci-check.sh

# Or manually:
docker-compose exec backend poetry run pytest
docker-compose exec backend poetry run black --check app/
docker-compose exec backend poetry run ruff check app/
docker-compose exec frontend npm test
docker-compose exec frontend npm run lint
```

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Docker Documentation](https://docs.docker.com/)
