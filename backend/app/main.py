import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.users.api import auth_routes, user_routes, team_routes, invitation_routes
from app.projects.api import project_routes, document_routes, mcp_routes
from app.library.api import category_routes, template_routes

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
app.include_router(mcp_routes.router)
app.include_router(category_routes.router)
app.include_router(template_routes.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/v1")
async def api_root() -> dict[str, str]:
    """API root endpoint."""
    return {"message": "DocMCP API v1"}


# Serve static files (frontend build)
# Check if static files directory exists (for production)
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve SPA for all non-API routes."""
        # Don't interfere with API routes
        if full_path.startswith("api/"):
            return {"detail": "Not Found"}

        # Try to serve the file directly
        file_path = static_dir / full_path
        if file_path.is_file():
            return FileResponse(file_path)

        # Otherwise serve index.html for SPA routing
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)

        return {"detail": "Not Found"}
