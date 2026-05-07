"""Investigation CRUD router."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..dependencies import get_base_path

router = APIRouter(prefix="/investigations", tags=["investigations"])


# ── Request/Response Models ──────────────────────────────────────────────────

class CreateInvestigationRequest(BaseModel):
    actor: str
    client_question: str
    human_initial_read: str = ""


class CreateInvestigationResponse(BaseModel):
    id: str
    actor: str
    client_question: str
    status: str
    path: str


class InvestigationResponse(BaseModel):
    manifest: dict[str, Any]
    files: list[dict[str, Any]]


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("")
def list_investigations(base_path=Depends(get_base_path)) -> list[dict[str, Any]]:
    """List all investigations."""
    from oracle.kernel import list_investigations as kernel_list
    return kernel_list(base_path)


@router.post("")
def create_investigation(
    req: CreateInvestigationRequest,
    base_path=Depends(get_base_path),
) -> CreateInvestigationResponse:
    """Create a new investigation."""
    from oracle.kernel import create_manifest, investigation_dir

    manifest = create_manifest(
        base_path=base_path,
        actor=req.actor,
        client_question=req.client_question,
        human_initial_read=req.human_initial_read,
    )
    return CreateInvestigationResponse(
        id=manifest["id"],
        actor=manifest["actor"],
        client_question=manifest["client_question"],
        status=manifest["status"],
        path=str(investigation_dir(base_path, manifest["id"])),
    )


@router.get("/{investigation_id}")
def get_investigation(
    investigation_id: str,
    base_path=Depends(get_base_path),
) -> InvestigationResponse:
    """Get investigation manifest and file listing."""
    from oracle.kernel import load_manifest, investigation_dir

    try:
        manifest = load_manifest(base_path, investigation_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Investigation not found")

    inv_dir = investigation_dir(base_path, investigation_id)
    files = []
    if inv_dir.exists():
        for f in sorted(inv_dir.rglob("*")):
            if f.is_file():
                rel = f.relative_to(inv_dir).as_posix()
                files.append({"path": rel, "size": f.stat().st_size})

    return InvestigationResponse(manifest=manifest, files=files)


@router.post("/{investigation_id}/human")
def human_input(
    investigation_id: str,
    instructions: dict[str, str],
    base_path=Depends(get_base_path),
) -> dict[str, Any]:
    """Submit human instructions and resume the pipeline."""
    from oracle.kernel import clear_human_action, load_manifest

    try:
        load_manifest(base_path, investigation_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Investigation not found")

    manifest = clear_human_action(base_path, investigation_id)
    return {
        "success": True,
        "investigation_id": investigation_id,
        "instructions_received": instructions.get("instructions", ""),
        "status": manifest["status"],
    }
