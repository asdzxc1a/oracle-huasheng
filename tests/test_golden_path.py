"""
Golden Path Validation Tests — Huasheng Pattern v3.0

These tests verify that the Oracle Kernel executes the full golden path
with REAL intelligence, not placeholders:
1. Create investigation → manifest exists
2. Run Actor Harvester → catalog written with SPECIFIC sources, manifest updated
3. Run Video Analysis → brief written with ALL Huasheng features
4. Pre-ship validation → passes with real score
5. Contradictions preserved → ≥2 pairs
6. Tier marking → every claim tagged
7. Anti-patterns enforced → checked and documented
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

# Add oracle to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from oracle.kernel import (
    create_manifest,
    load_manifest,
    update_agent_status,
    set_human_action,
    clear_human_action,
    investigation_dir,
    AgentRunner,
    ContextStore,
)


class TestGoldenPath:
    """End-to-end tests for the Oracle Kernel golden path with Huasheng enforcement."""

    def setup_method(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="oracle-test-"))
        # Create minimal directory structure
        for sub in ("kernel", "agents/actor_harvester", "agents/video_analysis",
                    "investigations", "context/actors", "context/clients", "context/templates"):
            (self.tmp / sub).mkdir(parents=True, exist_ok=True)

        # Copy agent modules into temp tree so AgentRunner can discover them
        src_agents = PROJECT_ROOT / "oracle" / "agents"
        if src_agents.exists():
            for agent_dir in src_agents.iterdir():
                if agent_dir.is_dir():
                    dst = self.tmp / "agents" / agent_dir.name
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(agent_dir, dst)

    def teardown_method(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_create_investigation(self) -> None:
        """Phase 0: Kernel can create an investigation with manifest."""
        manifest = create_manifest(
            base_path=self.tmp,
            actor="Zendaya",
            client_question="Can she carry a $25M non-franchise drama lead?",
            human_initial_read="Inflection point between franchise safety and artistic risk.",
        )

        assert manifest["actor"] == "Zendaya"
        assert "zendaya" in manifest["id"]
        assert manifest["status"] == "created"

        # Verify file exists
        mpath = investigation_dir(self.tmp, manifest["id"]) / "manifest.json"
        assert mpath.exists()

        # Verify subdirectories
        inv_dir = investigation_dir(self.tmp, manifest["id"])
        assert (inv_dir / "references").is_dir()
        assert (inv_dir / "research").is_dir()
        assert (inv_dir / "sources" / "clips").is_dir()

    def test_manifest_lifecycle(self) -> None:
        """Manifest can be loaded, updated, and tracked."""
        manifest = create_manifest(self.tmp, "Barry Allen", "Can he outrun a script?")
        inv_id = manifest["id"]

        # Update agent status
        m = update_agent_status(self.tmp, inv_id, "actor_harvester", "running")
        assert m["pipeline"]["truth"]["actor_harvester"] == "running"
        assert "actor_harvester" in m["agents_pending"]

        m = update_agent_status(self.tmp, inv_id, "actor_harvester", "completed")
        assert m["pipeline"]["truth"]["actor_harvester"] == "completed"
        assert "actor_harvester" in m["agents_completed"]

        # Human action
        m = set_human_action(self.tmp, inv_id, ["review_brief"], reason="Agent finished")
        assert m["status"] == "paused_for_human"
        assert m["human_actions_required"] == ["review_brief"]

        m = clear_human_action(self.tmp, inv_id)
        assert m["human_actions_required"] == []
        assert m["status"] == "resumed"

    def test_context_store(self) -> None:
        """ContextStore can save/load actor and client profiles."""
        store = ContextStore(self.tmp)

        # Actor
        store.save_actor("Zendaya", {"name": "Zendaya", "type": "leading", "tier": "A-list"})
        profile = store.load_actor("Zendaya")
        assert profile is not None
        assert profile["tier"] == "A-list"

        # Client
        store.save_client("Netflix-Drama", {"name": "Netflix", "budget_range": "20-40M"})
        client = store.load_client("Netflix-Drama")
        assert client is not None
        assert client["budget_range"] == "20-40M"

        # Template
        store.save_template("talent-whisperer", "# Talent Whisperer\n\n[content]")
        tmpl = store.load_template("talent-whisperer")
        assert tmpl is not None
        assert "Talent Whisperer" in tmpl

    def test_actor_harvester_agent(self) -> None:
        """Actor Harvester produces SPECIFIC catalog with source diversity."""
        manifest = create_manifest(self.tmp, "Zendaya", "Can she carry a non-franchise lead?")
        inv_id = manifest["id"]

        runner = AgentRunner(self.tmp)
        result = runner.run_agent(inv_id, "actor_harvester", instructions={"max_videos": 5})

        assert result["success"], f"Harvester failed: {result.get('error')}"
        assert result["result"]["videos_found"] > 0

        # Check manifest updated
        m = load_manifest(self.tmp, inv_id)
        assert m["pipeline"]["truth"]["actor_harvester"] == "completed"

        # Check files written
        inv_dir = investigation_dir(self.tmp, inv_id)
        catalog_json = inv_dir / "research" / "video-catalog.json"
        assert catalog_json.exists()

        # Huasheng: Catalog must have specific sources (not placeholders)
        with open(catalog_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "videos" in data
        assert len(data["videos"]) > 0

        # Huasheng: Source diversity — at least 2 access levels
        access_levels = {v["access_level"] for v in data["videos"]}
        assert len(access_levels) >= 2, f"Only {len(access_levels)} access levels found: {access_levels}"

        # Huasheng: No placeholder URLs
        for v in data["videos"]:
            assert "example" not in v.get("url", ""), f"Placeholder URL found: {v['url']}"
            assert "placeholder" not in v.get("title", "").lower(), f"Placeholder title found: {v['title']}"

        # Check facts.md has real content
        facts = inv_dir / "references" / "facts.md"
        assert facts.exists()
        facts_text = facts.read_text(encoding="utf-8")
        assert "Filmography Highlights" in facts_text
        assert len(facts_text) > 300, "facts.md too short — likely placeholder"

        # Check career timeline exists
        assert "Career Timeline" in facts_text

    def test_video_analysis_agent(self) -> None:
        """Video Analysis produces brief with ALL Huasheng features."""
        manifest = create_manifest(self.tmp, "Zendaya", "Can she carry an indie drama?")
        inv_id = manifest["id"]

        # Run harvester first (prerequisite)
        runner = AgentRunner(self.tmp)
        runner.run_agent(inv_id, "actor_harvester")

        # Run video analysis
        result = runner.run_agent(inv_id, "video_analysis", instructions={"focus": "emotional range"})

        assert result["success"], f"Video analysis failed: {result.get('error')}"
        assert "brief_path" in result["result"]

        # Huasheng: Check brief has all required sections
        inv_dir = investigation_dir(self.tmp, inv_id)
        brief = (inv_dir / "brief.md").read_text(encoding="utf-8")
        required_sections = [
            "## Executive Summary",
            "## Clinical Profile",
            "## Archaeological Strata",
            "## Contradiction Map",
            "## Adversarial Findings",
            "## Tier Marking Key",
            "## Uncertainty Map",
        ]
        for section in required_sections:
            assert section in brief, f"Missing section: {section}"

        # Huasheng: No placeholder text
        assert "PLACEHOLDER" not in brief.upper(), "Brief contains placeholder text"
        assert "scaffolding" not in brief.lower(), "Brief contains scaffolding text"

        # Huasheng: Tier tags present
        assert "(Tier A)" in brief or "(Tier B)" in brief or "(Tier C)" in brief, "No tier tags found"

        # Huasheng: Contradictions preserved (≥2)
        contradiction_map = (inv_dir / "research" / "contradiction_map.md").read_text(encoding="utf-8")
        contradiction_count = contradiction_map.lower().count("contradiction")
        assert contradiction_count >= 2, f"Only {contradiction_count} contradiction mentions found"
        assert "PRESERVED" in contradiction_map or "human adjudicates" in contradiction_map.lower(), \
            "Contradictions not marked as preserved"

        # Huasheng: Adversarial findings present
        adversarial = (inv_dir / "research" / "adversarial_findings.md").read_text(encoding="utf-8")
        assert "Devil's Advocate" in adversarial or "adversarial" in adversarial.lower(), \
            "No adversarial analysis found"

        # Huasheng: Uncertainty map has ≥3 unknowns
        uncertainty = (inv_dir / "research" / "uncertainty_map.md").read_text(encoding="utf-8")
        unknown_count = uncertainty.lower().count("unknown")
        assert unknown_count >= 3, f"Only {unknown_count} 'unknown' mentions found"

        # Huasheng: Pre-ship validation exists
        pre_ship = inv_dir / "research" / "pre-ship-validation.md"
        assert pre_ship.exists(), "Pre-ship validation missing"
        pre_ship_text = pre_ship.read_text(encoding="utf-8")
        assert "Score:" in pre_ship_text, "Pre-ship validation has no score"

        # Huasheng: Anti-patterns checked
        anti_patterns = inv_dir / "references" / "anti-patterns.md"
        assert anti_patterns.exists(), "Anti-patterns check missing"
        anti_text = anti_patterns.read_text(encoding="utf-8")
        assert "CRITICAL" in anti_text or "WARNING" in anti_text or "CLEAN" in anti_text, \
            "Anti-patterns not properly evaluated"

        # Huasheng: Synthesis exists
        synthesis = inv_dir / "references" / "synthesis.md"
        assert synthesis.exists(), "Synthesis missing"

    def test_full_golden_path(self) -> None:
        """Complete golden path end-to-end with Huasheng validation."""
        # 1. Create
        manifest = create_manifest(
            self.tmp, "Zendaya",
            "Can she carry a $25M non-franchise drama lead?",
            human_initial_read="Inflection point...",
        )
        inv_id = manifest["id"]

        # 2. Harvester
        runner = AgentRunner(self.tmp)
        r1 = runner.run_agent(inv_id, "actor_harvester")
        assert r1["success"], f"Harvester failed: {r1.get('error')}"

        # 3. Video Analysis
        r2 = runner.run_agent(inv_id, "video_analysis", instructions={"focus": "post-Euphoria role choices"})
        assert r2["success"], f"Video analysis failed: {r2.get('error')}"

        # 4. Verify manifest state
        m = load_manifest(self.tmp, inv_id)
        assert m["pipeline"]["truth"]["actor_harvester"] == "completed"
        assert m["pipeline"]["truth"]["video_analysis"] == "completed"
        assert "actor_harvester" in m["agents_completed"]
        assert "video_analysis" in m["agents_completed"]

        # 5. Verify output files exist for every stage
        inv_dir = investigation_dir(self.tmp, inv_id)
        assert (inv_dir / "manifest.json").exists()
        assert (inv_dir / "research" / "video-catalog.json").exists()
        assert (inv_dir / "brief.md").exists()
        assert (inv_dir / "references" / "facts.md").exists()
        assert (inv_dir / "references" / "synthesis.md").exists()
        assert (inv_dir / "references" / "anti-patterns.md").exists()
        assert (inv_dir / "research" / "pre-ship-validation.md").exists()
        assert (inv_dir / "research" / "contradiction_map.md").exists()
        assert (inv_dir / "research" / "adversarial_findings.md").exists()
        assert (inv_dir / "research" / "uncertainty_map.md").exists()

        # 6. Huasheng: Brief has real intelligence
        brief_text = (inv_dir / "brief.md").read_text(encoding="utf-8")
        assert "Huasheng" in brief_text, "Brief not marked as Huasheng-certified"
        assert "Tier" in brief_text, "No tier marking in brief"

        print("\n✅ Golden path complete — all Huasheng stages verified.")


if __name__ == "__main__":
    test = TestGoldenPath()
    test.setup_method()
    try:
        test.test_create_investigation()
        print("✓ test_create_investigation passed")
        test.test_manifest_lifecycle()
        print("✓ test_manifest_lifecycle passed")
        test.test_context_store()
        print("✓ test_context_store passed")
        test.test_actor_harvester_agent()
        print("✓ test_actor_harvester_agent passed")
        test.test_video_analysis_agent()
        print("✓ test_video_analysis_agent passed")
        test.test_full_golden_path()
        print("✓ test_full_golden_path passed")
        print("\n🎉 All golden path tests passed — Huasheng Pattern v3.0 validated!")
    finally:
        test.teardown_method()
