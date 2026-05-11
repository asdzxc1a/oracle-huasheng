"""Unit tests for kernel/skill_loader.py"""

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from oracle.kernel.skill_loader import SkillLoader, SkillMetadata


class TestSkillLoader(unittest.TestCase):
    def setUp(self):
        self.loader = SkillLoader()
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _make_skill(self, name: str, description: str) -> Path:
        skill_dir = self.tmp / name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: |\n  {description}\n---\n\n# {name.title()}\n\nBody text here.\n",
            encoding="utf-8",
        )
        return skill_dir

    def test_load_metadata_extracts_frontmatter(self):
        skill_dir = self._make_skill("test-skill", "A test skill")
        meta = self.loader.load_metadata(skill_dir)
        self.assertEqual(meta.name, "test-skill")
        self.assertIn("A test skill", meta.description)
        self.assertEqual(meta.path, skill_dir)

    def test_load_body_under_threshold(self):
        skill_dir = self._make_skill("test-skill", "A test skill")
        body = self.loader.load_body(skill_dir)
        self.assertIn("Body text here", body)
        self.assertNotIn("name: test-skill", body)

    def test_missing_skill_md_raises(self):
        empty_dir = self.tmp / "empty"
        empty_dir.mkdir()
        with self.assertRaises(FileNotFoundError):
            self.loader.load_metadata(empty_dir)

    def test_missing_frontmatter_raises(self):
        bad_dir = self.tmp / "bad"
        bad_dir.mkdir()
        (bad_dir / "SKILL.md").write_text("No frontmatter here", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.loader.load_metadata(bad_dir)

    def test_load_full_with_resources(self):
        skill_dir = self._make_skill("test-skill", "A test skill")
        (skill_dir / "references").mkdir()
        (skill_dir / "references" / "guide.md").write_text("Guide content", encoding="utf-8")
        (skill_dir / "scripts").mkdir()
        (skill_dir / "scripts" / "run.py").write_text("print('ok')", encoding="utf-8")

        skill = self.loader.load_full(skill_dir, with_resources=True)
        self.assertEqual(skill.metadata.name, "test-skill")
        self.assertIn("guide", skill.references or {})
        self.assertIn("run", skill.scripts or {})
        self.assertTrue(skill.metadata.has_references)
        self.assertTrue(skill.metadata.has_scripts)

    def test_load_reference_on_demand(self):
        skill_dir = self._make_skill("test-skill", "A test skill")
        (skill_dir / "references").mkdir()
        (skill_dir / "references" / "guide.md").write_text("Guide content", encoding="utf-8")

        text = self.loader.load_reference(skill_dir, "guide")
        self.assertEqual(text, "Guide content")

    def test_load_reference_missing_raises(self):
        skill_dir = self._make_skill("test-skill", "A test skill")
        with self.assertRaises(FileNotFoundError):
            self.loader.load_reference(skill_dir, "missing")


if __name__ == "__main__":
    unittest.main()
