from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.users.api import auth_routes, user_routes, team_routes, invitation_routes
from app.projects.api import project_routes, document_routes

app = FastAPI(
    title="DocMCP API",
    description="Documentation as MCP service",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "dev" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(team_routes.router)
app.include_router(invitation_routes.router)
app.include_router(project_routes.router)
app.include_router(document_routes.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/v1")
async def api_root() -> dict[str, str]:
    """API root endpoint."""
    return {"message": "DocMCP API v1"}
