"""
Oracle API — FastAPI backend.

Serves:
- REST API at /api/*
- Static React SPA from ui/dist/ at /
- WebSocket for real-time updates (future)

Usage:
    cd oracle && uvicorn api.main:app --reload --port 8000
"""

import sys
from pathlib import Path

# Add project root to path so `oracle` package is importable
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .routers import investigations, agents, files

# ── App initialization ───────────────────────────────────────────────────────

app = FastAPI(
    title="Oracle API",
    description="Actor Assessment Intelligence System",
    version="0.1.0",
)

# CORS — allow local dev frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routers ──────────────────────────────────────────────────────────────

app.include_router(investigations.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(files.router, prefix="/api")


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "oracle-api"}


# ── Static file serving ──────────────────────────────────────────────────────

# The React build output goes to oracle/ui/dist/
DIST_DIR = Path(__file__).resolve().parent.parent / "ui" / "dist"

if DIST_DIR.exists():
    # Serve static assets
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str) -> FileResponse:
        """Serve index.html for all non-API routes (SPA catch-all)."""
        # Don't catch API routes
        if full_path.startswith("api/"):
            return FileResponse(DIST_DIR / "index.html", status_code=404)
        index_file = DIST_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return FileResponse(DIST_DIR / "index.html", status_code=404)
