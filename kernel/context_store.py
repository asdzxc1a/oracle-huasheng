"""
Context Store — Reads/writes shared actor/client context and templates.

The context store is file-based (markdown + json).
Every agent reads from here to get persistent profiles and writes
actor discoveries back for future investigations.
"""

import json
from pathlib import Path
from typing import Any


class ContextStore:
    """
    File-based context store for shared actor/client data and templates.

    Directory layout:
        context/
        ├── actors/
        │   └── zendaya.json          # Persistent actor profile
        ├── clients/
        │   └── netflix-drama.json    # Client psychological profile
        └── templates/
            ├── deliverable-the-talent-whisperer.md
            ├── deliverable-the-greenlight-confessor.md
            └── ...
    """

    def __init__(self, base_path: Path) -> None:
        self.base = base_path / "context"
        for sub in ("actors", "clients", "templates"):
            (self.base / sub).mkdir(parents=True, exist_ok=True)

    # ── Actors ────────────────────────────────────────────────────────────────

    def load_actor(self, actor_name: str) -> dict[str, Any] | None:
        """Load a persistent actor profile by name. Returns None if not found."""
        path = self._actor_path(actor_name)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_actor(self, actor_name: str, profile: dict[str, Any]) -> None:
        """Save (or overwrite) an actor profile."""
        path = self._actor_path(actor_name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)

    def list_actors(self) -> list[str]:
        """Return a list of all actor names with saved profiles."""
        actors_dir = self.base / "actors"
        if not actors_dir.exists():
            return []
        return sorted([p.stem for p in actors_dir.glob("*.json")])

    def _actor_path(self, actor_name: str) -> Path:
        slug = actor_name.lower().replace(" ", "-")
        return self.base / "actors" / f"{slug}.json"

    # ── Clients ───────────────────────────────────────────────────────────────

    def load_client(self, client_name: str) -> dict[str, Any] | None:
        """Load a client profile. Returns None if not found."""
        path = self._client_path(client_name)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_client(self, client_name: str, profile: dict[str, Any]) -> None:
        """Save (or overwrite) a client profile."""
        path = self._client_path(client_name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)

    def list_clients(self) -> list[str]:
        """Return a list of all client names with saved profiles."""
        clients_dir = self.base / "clients"
        if not clients_dir.exists():
            return []
        return sorted([p.stem for p in clients_dir.glob("*.json")])

    def _client_path(self, client_name: str) -> Path:
        slug = client_name.lower().replace(" ", "-")
        return self.base / "clients" / f"{slug}.json"

    # ── Templates ─────────────────────────────────────────────────────────────

    def load_template(self, template_name: str) -> str | None:
        """
        Load a markdown template by name.
        e.g. template_name='the-talent-whisperer'
        """
        path = self._template_path(template_name)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def save_template(self, template_name: str, content: str) -> None:
        """Save (or overwrite) a markdown template."""
        path = self._template_path(template_name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def list_templates(self) -> list[str]:
        """Return a list of all template names."""
        templates_dir = self.base / "templates"
        if not templates_dir.exists():
            return []
        return sorted([p.stem.replace("deliverable-", "") for p in templates_dir.glob("*.md")])

    def _template_path(self, template_name: str) -> Path:
        safe = template_name.lower().replace(" ", "-")
        if not safe.startswith("deliverable-"):
            safe = f"deliverable-{safe}"
        return self.base / "templates" / f"{safe}.md"

    # ── Investigation-scoped context ──────────────────────────────────────────

    def load_investigation_context(self, investigation_id: str) -> dict[str, Any]:
        """
        Load all relevant shared context for an investigation.
        Returns a dict with actor_profile, client_profile, and templates.
        """
        # This is a lightweight helper — agents call it to get everything they need.
        return {
            "store": self,
            "available_actors": self.list_actors(),
            "available_clients": self.list_clients(),
            "available_templates": self.list_templates(),
        }
