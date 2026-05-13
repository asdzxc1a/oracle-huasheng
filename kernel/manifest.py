"""
Investigation Manifest — State tracker for every Oracle investigation.

Every investigation gets a manifest.json that tracks:
- Pipeline stage
- Agent completion status
- Human actions required
- Timestamps
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── Pipeline schema ──────────────────────────────────────────────────────────

DEFAULT_PIPELINE: dict[str, dict[str, str]] = {
    "truth": {
        "actor_harvester": "not_started",
        "video_analysis": "not_started",
        "video_analyzer_v2": "not_started",
        "voice_register": "not_started",
    },
    "readiness": {
        "knowledge_sync": "not_started",
        "psychological_profiler": "not_started",
        "wiki_sync": "not_started",
        "dossier_builder": "not_started",
        "psychological_portrait": "not_started",
    },
    "presence": {
        "landing_page": "not_started",
        "pitch_deck": "not_started",
    },
    "proof": {
        "red_team_agent": "not_started",
        "forensic_archive": "not_started",
        "cryptographic_vault": "not_started",
    },
    "deployment": {
        "outreach": "not_started",
        "ads": "not_started",
    },
}

VALID_STATUSES = {
    "not_started",
    "running",
    "completed",
    "failed",
    "paused_for_human",
}


# ── Manifest helpers ─────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def investigation_dir(base_path: Path, investigation_id: str) -> Path:
    """Return the path to an investigation folder."""
    return base_path / "investigations" / investigation_id


def manifest_path(base_path: Path, investigation_id: str) -> Path:
    """Return the path to an investigation's manifest.json."""
    return investigation_dir(base_path, investigation_id) / "manifest.json"


def create_manifest(
    base_path: Path,
    actor: str,
    client_question: str,
    human_initial_read: str = "",
    investigation_id: str | None = None,
) -> dict[str, Any]:
    """
    Create a new investigation folder with manifest.json.

    Returns the manifest dict and writes it to disk.
    """
    if investigation_id is None:
        slug = actor.lower().replace(" ", "-")
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        investigation_id = f"{slug}-{today}-{uuid.uuid4().hex[:6]}"

    inv_dir = investigation_dir(base_path, investigation_id)
    inv_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    for sub in ("references", "research", "sources/clips", "sources/screenshots", "sources/transcripts"):
        (inv_dir / sub).mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "id": investigation_id,
        "actor": actor,
        "client_question": client_question,
        "human_initial_read": human_initial_read,
        "status": "created",
        "pipeline": _deep_copy_pipeline(DEFAULT_PIPELINE),
        "agents_completed": [],
        "agents_pending": [],
        "agents_failed": [],
        "human_actions_required": [],
        "created_at": _now(),
        "updated_at": _now(),
    }

    _write_manifest(base_path, investigation_id, manifest)
    return manifest


def load_manifest(base_path: Path, investigation_id: str) -> dict[str, Any]:
    """Load a manifest from disk. Raises FileNotFoundError if missing."""
    path = manifest_path(base_path, investigation_id)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(base_path: Path, investigation_id: str, manifest: dict[str, Any]) -> None:
    """Write a manifest back to disk, bumping updated_at."""
    manifest["updated_at"] = _now()
    _write_manifest(base_path, investigation_id, manifest)


def _write_manifest(base_path: Path, investigation_id: str, manifest: dict[str, Any]) -> None:
    path = manifest_path(base_path, investigation_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def update_agent_status(
    base_path: Path,
    investigation_id: str,
    agent_name: str,
    status: str,
    stage: str | None = None,
) -> dict[str, Any]:
    """
    Update an agent's status in the pipeline and manifest metadata.

    Valid statuses: not_started, running, completed, failed, paused_for_human
    """
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of {VALID_STATUSES}")

    manifest = load_manifest(base_path, investigation_id)

    # Update pipeline
    if stage is None:
        # Auto-detect stage from agent name
        stage = _find_stage_for_agent(manifest["pipeline"], agent_name)

    if stage and stage in manifest["pipeline"]:
        if agent_name in manifest["pipeline"][stage]:
            manifest["pipeline"][stage][agent_name] = status

    # Update metadata lists
    for lst in ("agents_completed", "agents_pending", "agents_failed"):
        if agent_name in manifest[lst]:
            manifest[lst].remove(agent_name)

    if status == "completed":
        manifest["agents_completed"].append(agent_name)
    elif status == "running":
        manifest["agents_pending"].append(agent_name)
    elif status == "failed":
        manifest["agents_failed"].append(agent_name)

    manifest["status"] = f"{agent_name}_{status}"

    save_manifest(base_path, investigation_id, manifest)
    return manifest


def set_human_action(
    base_path: Path,
    investigation_id: str,
    actions: list[str],
    reason: str = "",
) -> dict[str, Any]:
    """Set human_actions_required and pause the pipeline."""
    manifest = load_manifest(base_path, investigation_id)
    manifest["human_actions_required"] = actions
    manifest["status"] = "paused_for_human"
    if reason:
        manifest["human_pause_reason"] = reason
    save_manifest(base_path, investigation_id, manifest)
    return manifest


def clear_human_action(base_path: Path, investigation_id: str) -> dict[str, Any]:
    """Clear human_actions_required and resume."""
    manifest = load_manifest(base_path, investigation_id)
    manifest["human_actions_required"] = []
    manifest["status"] = "resumed"
    manifest.pop("human_pause_reason", None)
    save_manifest(base_path, investigation_id, manifest)
    return manifest


def list_investigations(base_path: Path) -> list[dict[str, Any]]:
    """Return a list of all investigation manifests."""
    inv_root = base_path / "investigations"
    if not inv_root.exists():
        return []
    manifests = []
    for d in sorted(inv_root.iterdir()):
        if d.is_dir():
            mp = d / "manifest.json"
            if mp.exists():
                with open(mp, "r", encoding="utf-8") as f:
                    manifests.append(json.load(f))
    return manifests


# ── Internal helpers ─────────────────────────────────────────────────────────

def _deep_copy_pipeline(pipeline: dict) -> dict:
    import copy
    return copy.deepcopy(pipeline)


def _find_stage_for_agent(pipeline: dict[str, dict[str, str]], agent_name: str) -> str | None:
    for stage, agents in pipeline.items():
        if agent_name in agents:
            return stage
    return None
