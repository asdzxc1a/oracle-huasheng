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

from .routers import investigations, agents, files, commands, skills, wiki, knowledge

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
app.include_router(commands.router, prefix="/api")
app.include_router(skills.router, prefix="/api")
app.include_router(wiki.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "oracle-api"}


@app.get("/api/status")
def system_status() -> dict[str, Any]:
    """Comprehensive system status — dependencies, agents, LLM."""
    import shutil
    import subprocess

    from oracle.kernel.llm_client_v2 import LLMClientV2
    from oracle.kernel.knowledge_graph import KnowledgeGraph

    status: dict[str, Any] = {
        "api": "ok",
        "version": "0.2.0",
    }

    # LLM
    llm = LLMClientV2()
    status["llm"] = {
        "available": llm.is_available(),
        "provider": "gemini",
        "text_model": llm.text_model,
        "video_model": llm.video_model,
    }

    # External tools
    status["tools"] = {
        "yt_dlp": shutil.which("yt-dlp") is not None,
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "ffprobe": shutil.which("ffprobe") is not None,
    }

    # ChromaDB
    try:
        kg = KnowledgeGraph()
        status["knowledge_graph"] = {
            "available": True,
            "actors": len(kg.list_actors()),
        }
    except Exception as e:
        status["knowledge_graph"] = {"available": False, "error": str(e)}

    # Agents
    try:
        from oracle.kernel import AgentRunner
        runner = AgentRunner(Path(__file__).resolve().parent.parent)
        agents = runner.list_agents()
        status["agents"] = {
            "count": len(agents),
            "names": [a["name"] for a in agents],
        }
    except Exception as e:
        status["agents"] = {"count": 0, "error": str(e)}

    return status


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
