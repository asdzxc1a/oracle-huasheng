"""Unit tests for kernel/skill_registry.py"""

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from oracle.kernel.skill_registry import SkillRegistry


class TestSkillRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = SkillRegistry()
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _make_skill(self, name: str, description: str) -> Path:
        skill_dir = self.tmp / name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: |\n  {description}\n---\n\n# Body\n",
            encoding="utf-8",
        )
        return skill_dir

    def test_discover_finds_all_skills(self):
        self._make_skill("skill-a", "First skill")
        self._make_skill("skill-b", "Second skill")
        self.registry.discover(self.tmp)
        self.assertEqual(len(self.registry.list_all()), 2)

    def test_get_by_name(self):
        self._make_skill("skill-a", "First skill")
        self.registry.discover(self.tmp)
        meta = self.registry.get("skill-a")
        self.assertEqual(meta.name, "skill-a")

    def test_get_missing_raises(self):
        self.registry.discover(self.tmp)
        with self.assertRaises(KeyError):
            self.registry.get("nonexistent")

    def test_exists(self):
        self._make_skill("skill-a", "First skill")
        self.registry.discover(self.tmp)
        self.assertTrue(self.registry.exists("skill-a"))
        self.assertFalse(self.registry.exists("missing"))

    def test_validate_references_finds_broken(self):
        skill_dir = self.tmp / "skill-a"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: skill-a\ndescription: test\n---\n\nUses `nonexistent-skill`.\n",
            encoding="utf-8",
        )
        self.registry.discover(self.tmp)
        broken = self.registry.validate_references()
        self.assertEqual(len(broken), 1)
        self.assertIn("nonexistent-skill", broken[0])

    def test_validate_references_ok_when_valid(self):
        self._make_skill("skill-a", "First")
        self._make_skill("skill-b", "Second")
        skill_dir = self.tmp / "skill-a"
        (skill_dir / "SKILL.md").write_text(
            "---\nname: skill-a\ndescription: test\n---\n\nUses `skill-b`.\n",
            encoding="utf-8",
        )
        self.registry.discover(self.tmp)
        broken = self.registry.validate_references()
        self.assertEqual(len(broken), 0)


if __name__ == "__main__":
    unittest.main()
