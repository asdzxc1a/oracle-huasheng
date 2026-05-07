"""Agent execution router."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel

from ..dependencies import get_base_path

router = APIRouter(tags=["agents"])


# ── Request/Response Models ──────────────────────────────────────────────────

class RunAgentRequest(BaseModel):
    instructions: dict[str, Any] | None = None


class RunAgentResponse(BaseModel):
    success: bool
    agent: str
    result: dict[str, Any] | None = None
    error: str | None = None


# ── Background task storage ──────────────────────────────────────────────────

# In-memory store for async job results. In production, use Redis or a DB.
_job_store: dict[str, dict[str, Any]] = {}


def _run_agent_task(
    base_path_str: str,
    investigation_id: str,
    agent_name: str,
    instructions: dict[str, Any] | None,
    job_id: str,
) -> None:
    """Background task that runs an agent."""
    from pathlib import Path
    from oracle.kernel import AgentRunner

    runner = AgentRunner(Path(base_path_str))
    result = runner.run_agent(
        investigation_id=investigation_id,
        agent_name=agent_name,
        instructions=instructions or {},
    )
    _job_store[job_id] = result


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/agents")
def list_agents(base_path=Depends(get_base_path)) -> list[dict[str, str]]:
    """List all available agents."""
    from oracle.kernel import AgentRunner

    runner = AgentRunner(base_path)
    return runner.list_agents()


@router.post("/investigations/{investigation_id}/agents/{agent_name}")
def run_agent(
    investigation_id: str,
    agent_name: str,
    req: RunAgentRequest,
    background_tasks: BackgroundTasks,
    base_path=Depends(get_base_path),
) -> dict[str, Any]:
    """
    Run an agent for an investigation.

    Returns immediately with a job_id. Poll /jobs/{job_id} for completion.
    """
    from oracle.kernel import load_manifest
    from uuid import uuid4

    try:
        load_manifest(base_path, investigation_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Investigation not found")

    job_id = f"{investigation_id}-{agent_name}-{uuid4().hex[:8]}"
    _job_store[job_id] = {"status": "running"}

    background_tasks.add_task(
        _run_agent_task,
        str(base_path),
        investigation_id,
        agent_name,
        req.instructions,
        job_id,
    )

    return {
        "success": True,
        "job_id": job_id,
        "investigation_id": investigation_id,
        "agent": agent_name,
        "status": "running",
    }


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str) -> dict[str, Any]:
    """Poll for agent job completion."""
    result = _job_store.get(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, **result}
