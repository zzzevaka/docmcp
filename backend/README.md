# DocMCP Backend

Backend service for DocMCP - Documentation as MCP.

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- Alembic
- Poetry

## Development

The backend is designed to run in Docker. See the main project README for setup instructions.

## Project Structure

```
backend/
├── app/
│   ├── config.py          # Application configuration
│   ├── database.py        # Database setup and base models
│   └── main.py            # FastAPI application entry point
├── alembic/               # Database migrations
├── tests/                 # Unit tests
├── pyproject.toml         # Poetry dependencies
└── README.md
```

## Running Tests

```bash
poetry run pytest
```
