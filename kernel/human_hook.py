"""
Human-in-the-Loop Hook — Pauses execution, displays state, collects input.

The kernel calls pause_for_human() whenever:
- An agent completes and needs review
- A validation gate fails and needs human judgment
- The system needs instructions before proceeding
"""

from pathlib import Path
from typing import Any

from . import manifest as manifest_mod


def pause_for_human(
    base_path: Path,
    investigation_id: str,
    reason: str,
    options: list[str] | None = None,
) -> dict[str, Any]:
    """
    Pause the pipeline and prompt the human for input.

    This is the CLI version. The web UI (Phase 2) will call the same
    manifest functions but render via HTTP instead of stdin/stdout.
    """
    manifest = manifest_mod.load_manifest(base_path, investigation_id)
    inv_dir = manifest_mod.investigation_dir(base_path, investigation_id)

    # Update manifest
    manifest_mod.set_human_action(base_path, investigation_id, [reason], reason=reason)

    # ── Display banner ────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"  🎭 ORACLE — HUMAN REVIEW REQUIRED")
    print("=" * 70)
    print(f"  Investigation: {investigation_id}")
    print(f"  Actor:         {manifest['actor']}")
    print(f"  Question:      {manifest.get('client_question', 'N/A')}")
    print(f"  Status:        {manifest['status']}")
    print(f"  Reason:        {reason}")
    print("=" * 70)

    # ── Display recent output summary ─────────────────────────────────────────
    research_dir = inv_dir / "research"
    if research_dir.exists():
        files = sorted(research_dir.glob("*.md"))
        if files:
            print("\n  📁 Recent research files:")
            for f in files[-5:]:
                size = f.stat().st_size
                print(f"     • {f.name} ({size:,} bytes)")

    # ── Display brief if exists ───────────────────────────────────────────────
    brief_path = inv_dir / "brief.md"
    if brief_path.exists():
        print(f"\n  📄 Brief written to: {brief_path}")

    # ── Display options ───────────────────────────────────────────────────────
    if options:
        print("\n  Options:")
        for i, opt in enumerate(options, 1):
            print(f"     {i}. {opt}")

    # ── Prompt for input ──────────────────────────────────────────────────────
    print("\n" + "-" * 70)
    instructions = input("  Your instructions for the next step > ").strip()
    print("-" * 70)

    # Clear human action and return
    manifest_mod.clear_human_action(base_path, investigation_id)

    return {
        "human_instructions": instructions,
        "investigation_id": investigation_id,
        "reason": reason,
    }


def display_brief_summary(base_path: Path, investigation_id: str) -> None:
    """Print a quick summary of the investigation's current brief."""
    inv_dir = manifest_mod.investigation_dir(base_path, investigation_id)
    brief_path = inv_dir / "brief.md"

    if not brief_path.exists():
        print("  (No brief generated yet.)")
        return

    content = brief_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    # Print first 20 lines or first 1000 chars
    preview = "\n".join(lines[:30])
    if len(preview) > 1200:
        preview = preview[:1200] + "\n  ... [truncated]"

    print("\n  📄 Brief preview:")
    print("  " + "-" * 66)
    for line in preview.splitlines():
        print(f"  {line}")
    print("  " + "-" * 66)
