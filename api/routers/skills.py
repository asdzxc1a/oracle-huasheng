"""Skill introspection router."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..dependencies import get_base_path

router = APIRouter(prefix="/skills", tags=["skills"])


class SkillResponse(BaseModel):
    name: str
    description: str
    has_scripts: bool
    has_references: bool
    has_assets: bool


@router.get("")
def list_skills(base_path=Depends(get_base_path)) -> list[SkillResponse]:
    """List all available skills."""
    from oracle.kernel import SkillRegistry

    registry = SkillRegistry()
    skills_dir = base_path / "skills"
    registry.discover(skills_dir)

    return [
        SkillResponse(
            name=m.name,
            description=m.description,
            has_scripts=m.has_scripts,
            has_references=m.has_references,
            has_assets=m.has_assets,
        )
        for m in registry.list_all()
    ]


@router.get("/{name}")
def get_skill(name: str, base_path=Depends(get_base_path)) -> dict[str, Any]:
    """Get full skill body by name."""
    from oracle.kernel import SkillRegistry, SkillLoader

    registry = SkillRegistry()
    skills_dir = base_path / "skills"
    registry.discover(skills_dir)

    try:
        meta = registry.get(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")

    loader = SkillLoader()
    body = loader.load_body(meta.path)

    return {
        "name": meta.name,
        "description": meta.description,
        "body": body,
        "has_scripts": meta.has_scripts,
        "has_references": meta.has_references,
        "has_assets": meta.has_assets,
    }
