"""
Skill Registry — Discovery and indexing of all skills.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .skill_loader import SkillLoader, SkillMetadata


class SkillRegistry:
    """
    Discovers and indexes all skills in the skills/ directory.
    """

    def __init__(self) -> None:
        self._skills: dict[str, SkillMetadata] = {}
        self._loader = SkillLoader()

    def discover(self, skills_dir: Path) -> None:
        """Scan skills/ directory and index all skills."""
        if not skills_dir.exists():
            return

        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            if not (skill_dir / "SKILL.md").exists():
                continue

            try:
                meta = self._loader.load_metadata(skill_dir)
                self._skills[meta.name] = meta
            except Exception:
                continue

    def get(self, name: str) -> SkillMetadata:
        if name not in self._skills:
            raise KeyError(f"Skill '{name}' not found")
        return self._skills[name]

    def list_all(self) -> list[SkillMetadata]:
        return sorted(self._skills.values(), key=lambda s: s.name)

    def exists(self, name: str) -> bool:
        return name in self._skills

    def validate_references(self) -> list[str]:
        """Check for broken references in all skill bodies."""
        import re

        broken: list[str] = []
        for meta in self._skills.values():
            body = self._loader.load_body(meta.path)
            # Find references to other skills by backtick name
            refs = set(re.findall(r"`([a-z0-9-]+)`", body))
            for ref in refs:
                if ref != meta.name and not self.exists(ref):
                    broken.append(f"{meta.name} references unknown skill '{ref}'")
        return broken
