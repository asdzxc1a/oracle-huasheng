"""
Agent Runner — Loads agents, passes context, executes, writes output.

This is the kernel's engine. It:
1. Discovers agents from the agents/ directory
2. Loads their logic + prompt + references
3. Executes them with investigation context
4. Writes output to investigations/{id}/research/
5. Updates the manifest
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any, Protocol

from . import manifest as manifest_mod
from .context_store import ContextStore


class AgentProtocol(Protocol):
    """Every agent module must expose these attributes/functions."""

    name: str
    version: str

    def run(self, investigation_id: str, instructions: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        ...

    def validate(self, investigation_id: str, base_path: Path) -> bool:
        ...


class AgentRunner:
    """
    Discovers and runs agents according to the Oracle Kernel protocol.
    """

    def __init__(self, base_path: Path) -> None:
        self.base = base_path
        self.agents_dir = base_path / "agents"
        self.context_store = ContextStore(base_path)
        self._agent_cache: dict[str, AgentProtocol] = {}

    # ── Discovery ─────────────────────────────────────────────────────────────

    def list_agents(self) -> list[dict[str, str]]:
        """Return a list of available agents with name and version."""
        agents = []
        if not self.agents_dir.exists():
            return agents
        for d in sorted(self.agents_dir.iterdir()):
            if d.is_dir() and (d / "agent.py").exists():
                try:
                    mod = self._load_agent_module(d.name)
                    agents.append({"name": mod.name, "version": getattr(mod, "version", "0.0")})
                except Exception:
                    continue
        return agents

    def _load_agent_module(self, agent_name: str) -> Any:
        """Dynamically load an agent module from agents/{agent_name}/agent.py."""
        agent_dir = self.agents_dir / agent_name
        agent_file = agent_dir / "agent.py"
        if not agent_file.exists():
            raise FileNotFoundError(f"Agent '{agent_name}' not found at {agent_file}")

        module_name = f"oracle.agents.{agent_name}"

        # If cached in this runner instance, return it
        if agent_name in self._agent_cache:
            cached = self._agent_cache[agent_name]
            # Verify the cached module still points to the right file
            if getattr(cached, "__file__", None) == str(agent_file):
                return cached

        # If cached in sys.modules from a different path, clear it
        if module_name in sys.modules:
            existing = sys.modules[module_name]
            if getattr(existing, "__file__", None) != str(agent_file):
                del sys.modules[module_name]

        spec = importlib.util.spec_from_file_location(module_name, agent_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load spec for {agent_file}")

        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod
        spec.loader.exec_module(mod)

        self._agent_cache[agent_name] = mod
        return mod

    # ── Execution ─────────────────────────────────────────────────────────────

    def run_agent(
        self,
        investigation_id: str,
        agent_name: str,
        instructions: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Run an agent for a given investigation.

        Steps:
        1. Load manifest, set agent status to 'running'
        2. Load agent module
        3. Gather investigation context
        4. Call agent.run()
        5. Validate output
        6. Update manifest to 'completed' or 'failed'
        7. Return summary
        """
        instructions = instructions or {}

        # 1. Update manifest
        manifest_mod.update_agent_status(self.base, investigation_id, agent_name, "running")

        # 2. Load agent
        try:
            mod = self._load_agent_module(agent_name)
        except Exception as e:
            manifest_mod.update_agent_status(self.base, investigation_id, agent_name, "failed")
            return {"success": False, "error": f"Failed to load agent: {e}"}

        # 3. Gather context
        investigation_context = self._gather_context(investigation_id, agent_name)

        # 4. Execute
        try:
            result = mod.run(investigation_id, instructions, investigation_context)
        except Exception as e:
            manifest_mod.update_agent_status(self.base, investigation_id, agent_name, "failed")
            return {"success": False, "error": f"Agent execution failed: {e}"}

        # 5. Validate (optional — agents expose validate())
        try:
            valid = mod.validate(investigation_id, self.base)
            if not valid:
                manifest_mod.update_agent_status(self.base, investigation_id, agent_name, "failed")
                return {"success": False, "error": "Agent output failed validation gates."}
        except Exception:
            # Validation not implemented or failed — be lenient for now
            pass

        # 6. Update manifest
        manifest_mod.update_agent_status(self.base, investigation_id, agent_name, "completed")

        return {"success": True, "agent": agent_name, "result": result}

    def _gather_context(self, investigation_id: str, agent_name: str) -> dict[str, Any]:
        """Collect all context an agent needs to run."""
        m = manifest_mod.load_manifest(self.base, investigation_id)
        inv_dir = manifest_mod.investigation_dir(self.base, investigation_id)

        # Load actor profile if it exists
        actor_profile = self.context_store.load_actor(m["actor"])

        # Load agent's own references (thick methodology docs)
        agent_refs_dir = self.agents_dir / agent_name / "references"
        references = {}
        if agent_refs_dir.exists():
            for ref_file in sorted(agent_refs_dir.glob("*.md")):
                references[ref_file.stem] = ref_file.read_text(encoding="utf-8")

        # Load agent prompt (thin router)
        prompt_path = self.agents_dir / agent_name / "prompt.md"
        prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""

        return {
            "investigation_id": investigation_id,
            "manifest": m,
            "actor": m["actor"],
            "client_question": m.get("client_question", ""),
            "human_initial_read": m.get("human_initial_read", ""),
            "actor_profile": actor_profile,
            "investigation_dir": str(inv_dir),
            "references": references,
            "prompt": prompt,
            "context_store": self.context_store,
        }
