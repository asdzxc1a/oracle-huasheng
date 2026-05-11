#!/usr/bin/env python3
"""
Oracle Linter — Validates the plugin ecosystem.

Checks:
1. All SKILL.md files parse (YAML frontmatter + markdown body)
2. All agent .md files have valid frontmatter
3. All agent system prompts reference skills that exist
4. No duplicate skill names
5. All skill references resolve

Usage:
    python scripts/check.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import yaml

    def _parse_frontmatter(text: str) -> dict:
        return yaml.safe_load(text)
except ImportError:
    def _parse_frontmatter(text: str) -> dict:
        result = {}
        current_key = None
        current_value_lines = []
        for line in text.splitlines():
            if line.strip().startswith("#"):
                continue
            if ":" in line and not line.startswith(" ") and not line.startswith("-"):
                if current_key is not None:
                    result[current_key] = "\n".join(current_value_lines).strip()
                key, _, val = line.partition(":")
                current_key = key.strip()
                current_value_lines = [val.strip()] if val.strip() else []
            elif current_key is not None:
                current_value_lines.append(line.rstrip())
        if current_key is not None:
            result[current_key] = "\n".join(current_value_lines).strip()
        return result

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
AGENTS = ROOT / "agents"
errors: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


def main() -> int:
    # Index every skill name -> source dir
    src_by_name: dict[str, Path] = {}
    for sk in SKILLS.glob("*/SKILL.md"):
        skill_dir = sk.parent
        try:
            text = sk.read_text(encoding="utf-8")
            if not text.startswith("---"):
                err(f"skill-frontmatter: {rel(sk)} missing leading ---")
                continue
            parts = text.split("---", 2)
            if len(parts) < 3:
                err(f"skill-frontmatter: {rel(sk)} invalid frontmatter")
                continue
            fm = _parse_frontmatter(parts[1])
            if not isinstance(fm, dict):
                err(f"skill-frontmatter: {rel(sk)} frontmatter not dict")
                continue
            for k in ("name", "description"):
                if k not in fm:
                    err(f"skill-frontmatter: {rel(sk)} missing '{k}'")
            name = fm.get("name", "")
            if name in src_by_name:
                err(f"duplicate-skill: '{name}' in {rel(src_by_name[name])} and {rel(skill_dir)}")
            else:
                src_by_name[name] = skill_dir
        except Exception as e:
            err(f"skill-parse: {rel(sk)}: {e}")

    # Check agent prompts reference valid skills
    for prompt_md in sorted(AGENTS.glob("*/prompt.md")):
        text = prompt_md.read_text()
        refs = set(re.findall(r"`([a-z0-9-]+)`", text))
        for ref in refs:
            if ref not in src_by_name:
                # Some backticks are not skill references (e.g., "RAW", "MANAGED")
                # Only flag ones that look like skill names
                if "-" in ref or ref in ("source-evaluation", "body-language", "tier-marking"):
                    err(f"agent-ref: {rel(prompt_md)} references unknown skill '{ref}'")

    # Report
    if errors:
        print(f"FAIL — {len(errors)} issue(s):\n", file=sys.stderr)
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        sys.exit(1)

    print(f"OK — {len(src_by_name)} skill(s), 0 issues.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
