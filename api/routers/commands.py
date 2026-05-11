"""Command router — slash command endpoints."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel

from ..dependencies import get_base_path

router = APIRouter(prefix="/commands", tags=["commands"])


class AssessRequest(BaseModel):
    actor: str
    question: str
    initial_read: str = ""
    focus: list[str] = []
    process_videos: bool = False


class HarvestRequest(BaseModel):
    actor: str
    focus_areas: list[str] = []
    max_videos: int = 10


class CompareRequest(BaseModel):
    actors: list[str]
    question: str


class CommandResponse(BaseModel):
    investigation_id: str
    actor: str
    question: str
    status: str
    agent: str
    job_id: str


# In-memory job store (replace with Redis/DB in production)
_job_store: dict[str, dict[str, Any]] = {}


def _run_command_task(
    base_path_str: str,
    investigation_id: str,
    agent_name: str,
    instructions: dict[str, Any],
    job_id: str,
) -> None:
    """Background task that runs a command agent."""
    from pathlib import Path
    from oracle.kernel import AgentRunner

    runner = AgentRunner(Path(base_path_str))
    result = runner.run_agent(
        investigation_id=investigation_id,
        agent_name=agent_name,
        instructions=instructions,
    )
    _job_store[job_id] = result


@router.post("/assess")
def command_assess(
    req: AssessRequest,
    background_tasks: BackgroundTasks,
    base_path=Depends(get_base_path),
) -> CommandResponse:
    """/assess [actor] — [question]"""
    from oracle.kernel import create_manifest
    from uuid import uuid4

    manifest = create_manifest(
        base_path=base_path,
        actor=req.actor,
        client_question=req.question,
        human_initial_read=req.initial_read,
    )
    inv_id = manifest["id"]

    job_id = f"{inv_id}-assess-{uuid4().hex[:8]}"
    _job_store[job_id] = {"status": "running"}

    # Run source-harvester first, then video_analysis
    # For now, video_analysis orchestrates the full pipeline
    background_tasks.add_task(
        _run_command_task,
        str(base_path),
        inv_id,
        "video_analysis",
        {
            "focus": req.focus,
            "process_videos": req.process_videos,
        },
        job_id,
    )

    return CommandResponse(
        investigation_id=inv_id,
        actor=req.actor,
        question=req.question,
        status="created",
        agent="video_analysis",
        job_id=job_id,
    )


@router.post("/harvest")
def command_harvest(
    req: HarvestRequest,
    background_tasks: BackgroundTasks,
    base_path=Depends(get_base_path),
) -> CommandResponse:
    """/harvest [actor] — [focus]"""
    from oracle.kernel import create_manifest
    from uuid import uuid4

    manifest = create_manifest(
        base_path=base_path,
        actor=req.actor,
        client_question=f"Source harvest: {', '.join(req.focus_areas) or 'general assessment'}",
    )
    inv_id = manifest["id"]

    job_id = f"{inv_id}-harvest-{uuid4().hex[:8]}"
    _job_store[job_id] = {"status": "running"}

    background_tasks.add_task(
        _run_command_task,
        str(base_path),
        inv_id,
        "actor_harvester",
        {
            "focus_areas": req.focus_areas,
            "max_videos": req.max_videos,
        },
        job_id,
    )

    return CommandResponse(
        investigation_id=inv_id,
        actor=req.actor,
        question=", ".join(req.focus_areas) or "general assessment",
        status="created",
        agent="actor_harvester",
        job_id=job_id,
    )


@router.post("/compare")
def command_compare(
    req: CompareRequest,
    background_tasks: BackgroundTasks,
    base_path=Depends(get_base_path),
) -> CommandResponse:
    """/compare [actor A] vs [actor B] — [question]"""
    from oracle.kernel import create_manifest
    from uuid import uuid4

    if len(req.actors) != 2:
        raise HTTPException(status_code=400, detail="Exactly 2 actors required for comparison")

    actor_str = " vs ".join(req.actors)
    manifest = create_manifest(
        base_path=base_path,
        actor=actor_str,
        client_question=req.question,
    )
    inv_id = manifest["id"]

    job_id = f"{inv_id}-compare-{uuid4().hex[:8]}"
    _job_store[job_id] = {"status": "running"}

    background_tasks.add_task(
        _run_command_task,
        str(base_path),
        inv_id,
        "comparable_mapper",
        {
            "actors": req.actors,
            "question": req.question,
        },
        job_id,
    )

    return CommandResponse(
        investigation_id=inv_id,
        actor=actor_str,
        question=req.question,
        status="created",
        agent="comparable_mapper",
        job_id=job_id,
    )
