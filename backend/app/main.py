from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.library.api import category_routes, template_routes
from app.projects.api import (
    document_routes,
    mcp_routes,
    project_routes,
)
from app.users.api import (
    api_token_routes,
    auth_routes,
    invitation_routes,
    team_routes,
    user_routes,
)


class CachedStaticFiles(StaticFiles):
    """StaticFiles with cache control headers."""

    async def __call__(self, scope, receive, send):
        """Add cache headers to static files."""
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                # Cache static assets for 1 year (they have content hashes)
                headers[b"cache-control"] = b"public, max-age=31536000, immutable"
                message["headers"] = list(headers.items())
            await send(message)

        await super().__call__(scope, receive, send_wrapper)

app = FastAPI(
    title="DocMCP API",
    description="Documentation as MCP service",
    version="0.1.0",
)

# CORS middleware - allow all origins in dev, specific in production
# Note: allow_origins=["*"] doesn't work with credentials, so we use regex
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*" if settings.app_env == "dev" else r"https://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(team_routes.router)
app.include_router(invitation_routes.router)
app.include_router(api_token_routes.router)
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
    # Mount assets with long-term caching (files have content hashes)
    app.mount("/assets", CachedStaticFiles(directory=str(static_dir / "assets")), name="assets")

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

        # Otherwise serve index.html for SPA routing with no-cache
        # (so users always get the latest version with updated asset references)
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(
                index_path,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
            )

        return {"detail": "Not Found"}
