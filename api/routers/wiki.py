"""Wiki router — serves and edits actor wiki pages."""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..dependencies import get_base_path

router = APIRouter(prefix="/wiki", tags=["wiki"])

WIKI_DIR = Path(__file__).resolve().parent.parent.parent / "wiki"


class WikiPage(BaseModel):
    actor_slug: str
    content: str


class WikiUpdateRequest(BaseModel):
    content: str


@router.get("")
def list_wiki_pages() -> list[dict[str, str]]:
    """List all wiki pages."""
    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    pages = []
    for f in sorted(WIKI_DIR.glob("*.md")):
        pages.append({
            "actor_slug": f.stem,
            "title": f.stem.replace("-", " ").title(),
            "updated": str(f.stat().st_mtime),
        })
    return pages


@router.get("/{actor_slug}")
def get_wiki_page(actor_slug: str) -> dict[str, Any]:
    """Get a wiki page by actor slug."""
    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    page_path = WIKI_DIR / f"{actor_slug}.md"
    if not page_path.exists():
        raise HTTPException(status_code=404, detail="Wiki page not found")
    return {
        "actor_slug": actor_slug,
        "content": page_path.read_text(encoding="utf-8"),
    }


@router.put("/{actor_slug}")
def update_wiki_page(actor_slug: str, req: WikiUpdateRequest) -> dict[str, Any]:
    """Update a wiki page."""
    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    page_path = WIKI_DIR / f"{actor_slug}.md"
    page_path.write_text(req.content, encoding="utf-8")
    return {
        "actor_slug": actor_slug,
        "updated": True,
    }


@router.delete("/{actor_slug}")
def delete_wiki_page(actor_slug: str) -> dict[str, Any]:
    """Delete a wiki page."""
    page_path = WIKI_DIR / f"{actor_slug}.md"
    if page_path.exists():
        page_path.unlink()
    return {"actor_slug": actor_slug, "deleted": True}
