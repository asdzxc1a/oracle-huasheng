#!/usr/bin/env python3
"""
Sync agent skills from skills/ source of truth to agent bundles.

In the full Anthropic architecture, skills live in vertical-plugins/ and are
synced to agent-plugins/. In Oracle V1, skills/ is the source of truth.

This script validates that all skills referenced by agents exist in skills/.
Future versions will copy skill bundles into agent directories.

Usage:
    python scripts/sync-agent-skills.py [--dry-run]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
AGENTS = ROOT / "agents"


def main(dry_run: bool = False) -> int:
    # Index skills
    skills = {d.name for d in SKILLS.iterdir() if d.is_dir() and (d / "SKILL.md").exists()}

    # Check agent prompts
    missing_refs: list[str] = []
    for prompt_md in sorted(AGENTS.glob("*/prompt.md")):
        text = prompt_md.read_text()
        refs = set(re.findall(r"`([a-z0-9-]+)`", text))
        for ref in refs:
            if ref not in skills and "-" in ref:
                missing_refs.append(f"{prompt_md.parent.name}: '{ref}'")

    if dry_run:
        print("Dry run mode — no changes made.")

    print(f"Found {len(skills)} skill(s) in skills/")
    print(f"Checked {sum(1 for _ in AGENTS.glob('*/prompt.md'))} agent prompt(s)")

    if missing_refs:
        print("\nMissing skill references:")
        for m in missing_refs:
            print(f"  - {m}")
        return 1

    print("\nAll agent skill references resolved.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    sys.exit(main(dry_run=args.dry_run))
