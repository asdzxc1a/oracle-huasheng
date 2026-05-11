"""
Skill Loader — Progressive Disclosure Implementation

Three-tier progressive disclosure:
1. Metadata (name + description) — always in context (~100 words)
2. SKILL.md body — loaded when skill triggers (<5,000 words)
3. References/scripts/assets — loaded on demand
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def _parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse simple YAML frontmatter without external dependencies."""
    if HAS_YAML:
        return yaml.safe_load(text)
    # Simple manual parser for basic key: value pairs
    result: dict[str, Any] = {}
    current_key = None
    current_value_lines: list[str] = []
    for line in text.splitlines():
        if line.strip().startswith("#"):
            continue
        # Check for key: value pattern
        if ":" in line and not line.startswith(" ") and not line.startswith("-"):
            # Save previous key
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


@dataclass
class SkillMetadata:
    name: str
    description: str
    path: Path
    has_scripts: bool = False
    has_references: bool = False
    has_assets: bool = False


@dataclass
class Skill:
    metadata: SkillMetadata
    body: str
    references: dict[str, str] | None = None
    scripts: dict[str, Path] | None = None
    assets: dict[str, Path] | None = None


class SkillLoader:
    """Load skills with progressive disclosure."""

    def load_metadata(self, skill_path: Path) -> SkillMetadata:
        """Parse YAML frontmatter only. Fast. Always safe to call."""
        skill_file = skill_path / "SKILL.md"
        if not skill_file.exists():
            raise FileNotFoundError(f"SKILL.md not found in {skill_path}")

        text = skill_file.read_text(encoding="utf-8")
        if not text.startswith("---"):
            raise ValueError(f"SKILL.md missing frontmatter: {skill_file}")

        parts = text.split("---", 2)
        if len(parts) < 3:
            raise ValueError(f"SKILL.md invalid frontmatter: {skill_file}")

        frontmatter = _parse_frontmatter(parts[1])
        if not isinstance(frontmatter, dict):
            raise ValueError(f"SKILL.md frontmatter not a dict: {skill_file}")

        name = frontmatter.get("name", "")
        description = frontmatter.get("description", "")

        return SkillMetadata(
            name=name,
            description=description,
            path=skill_path,
            has_scripts=(skill_path / "scripts").exists(),
            has_references=(skill_path / "references").exists(),
            has_assets=(skill_path / "assets").exists(),
        )

    def load_body(self, skill_path: Path) -> str:
        """Load full SKILL.md body (without frontmatter)."""
        skill_file = skill_path / "SKILL.md"
        text = skill_file.read_text(encoding="utf-8")
        parts = text.split("---", 2)
        return parts[2].strip() if len(parts) >= 3 else text

    def load_full(self, skill_path: Path, with_resources: bool = False) -> Skill:
        """Load skill with optional resource expansion."""
        metadata = self.load_metadata(skill_path)
        body = self.load_body(skill_path)

        references = None
        scripts = None
        assets = None

        if with_resources:
            ref_dir = skill_path / "references"
            if ref_dir.exists():
                references = {
                    f.stem: f.read_text(encoding="utf-8")
                    for f in sorted(ref_dir.glob("*.md"))
                }

            script_dir = skill_path / "scripts"
            if script_dir.exists():
                scripts = {
                    f.stem: f
                    for f in sorted(script_dir.glob("*.py"))
                }

            asset_dir = skill_path / "assets"
            if asset_dir.exists():
                assets = {
                    str(f.relative_to(asset_dir)): f
                    for f in sorted(asset_dir.rglob("*"))
                    if f.is_file()
                }

        return Skill(
            metadata=metadata,
            body=body,
            references=references,
            scripts=scripts,
            assets=assets,
        )

    def load_reference(self, skill_path: Path, ref_name: str) -> str:
        """Load a single reference file on demand."""
        ref_file = skill_path / "references" / f"{ref_name}.md"
        if not ref_file.exists():
            raise FileNotFoundError(f"Reference not found: {ref_file}")
        return ref_file.read_text(encoding="utf-8")

    def load_script(self, skill_path: Path, script_name: str) -> Path:
        """Return path to script for execution."""
        script_file = skill_path / "scripts" / f"{script_name}.py"
        if not script_file.exists():
            raise FileNotFoundError(f"Script not found: {script_file}")
        return script_file
