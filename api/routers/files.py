"""File serving router."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse, FileResponse

from ..dependencies import get_base_path

router = APIRouter(tags=["files"])


@router.get("/investigations/{investigation_id}/files")
def list_files(
    investigation_id: str,
    base_path=Depends(get_base_path),
) -> list[dict[str, str | int]]:
    """List all files in an investigation."""
    from oracle.kernel import investigation_dir

    inv_dir = investigation_dir(base_path, investigation_id)
    if not inv_dir.exists():
        raise HTTPException(status_code=404, detail="Investigation not found")

    files = []
    for f in sorted(inv_dir.rglob("*")):
        if f.is_file():
            rel = f.relative_to(inv_dir).as_posix()
            files.append({
                "path": rel,
                "size": f.stat().st_size,
            })
    return files


@router.get("/investigations/{investigation_id}/files/{file_path:path}")
def read_file(
    investigation_id: str,
    file_path: str,
    base_path=Depends(get_base_path),
):
    """Read a specific file from an investigation."""
    from oracle.kernel import investigation_dir

    inv_dir = investigation_dir(base_path, investigation_id)
    target = inv_dir / file_path

    # Security: ensure the resolved path is within the investigation directory
    try:
        target.resolve().relative_to(inv_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    # Serve markdown/json/txt as plain text; everything else as FileResponse
    ext = target.suffix.lower()
    if ext in (".md", ".json", ".txt", ".py", ".yml", ".yaml"):
        content = target.read_text(encoding="utf-8")
        return PlainTextResponse(content)

    return FileResponse(target)
