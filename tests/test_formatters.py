"""Unit tests for kernel/formatters.py"""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from oracle.kernel.formatters import (
    format_contradiction_map,
    format_adversarial_findings,
    format_tier_marking,
    generate_uncertainty_map,
    compile_brief,
    extract_thesis,
    count_tiers,
)
from oracle.kernel.intelligence import Claim, Contradiction, AdversarialFinding


class TestFormatters(unittest.TestCase):
    def test_format_contradiction_map_with_contradictions(self):
        contradictions = [
            Contradiction(
                claim_a="Actor is confident",
                source_a="interview",
                claim_b="Actor shows hesitation",
                source_b="bts",
                tension="Confidence vs. insecurity",
                implication="May need more direction",
            )
        ]
        result = format_contradiction_map(contradictions)
        self.assertIn("Total Contradictions Preserved", result)
        self.assertIn("PRESERVED", result)

    def test_format_contradiction_map_empty(self):
        result = format_contradiction_map([])
        self.assertIn("No contradictions detected", result)

    def test_format_adversarial_findings(self):
        findings = [
            AdversarialFinding(
                challenge="Thesis is too optimistic",
                evidence_against="No evidence of risk-taking",
                blind_spot="Missed franchise dependency",
                counter_thesis="Actor plays it safe",
                confidence_in_challenge="moderate",
            )
        ]
        result = format_adversarial_findings(findings)
        self.assertIn("Devil's Advocate Budget", result)

    def test_format_tier_marking(self):
        claims = [
            Claim(text="Claim A", source_type="bts", access_level="RAW", tier="A", confidence=0.8),
            Claim(text="Claim B", source_type="interview", access_level="MANAGED", tier="B", confidence=0.6),
            Claim(text="Claim C", source_type="late_night", access_level="SCRIPTED", tier="C", confidence=0.4),
        ]
        result = format_tier_marking(claims)
        self.assertIn("Tier A: 1 claims", result)
        self.assertIn("Tier B: 1 claims", result)
        self.assertIn("Tier C: 1 claims", result)

    def test_generate_uncertainty_map(self):
        videos = [{"source_type": "podcast"}, {"source_type": "bts"}]
        result = generate_uncertainty_map("Test Actor", videos)
        self.assertIn("Unknown #1", result)
        self.assertIn("Unknown #2", result)
        self.assertIn("Unknown #3", result)

    def test_compile_brief(self):
        sections = {
            "executive_summary": "Summary text",
            "clinical_profile": "Clinical text",
            "intelligence_assessment": "Intel text",
            "archaeological_strata": "Strata text",
            "contradiction_map": "Contradictions",
            "adversarial_findings": "Adversarial",
            "tier_marking": "Tiers",
            "uncertainty_map": "Unknowns",
        }
        claims = [Claim(text="Test", source_type="bts", access_level="RAW", tier="A")]
        videos = [{"source_type": "bts", "access_level": "RAW"}]
        result = compile_brief("Actor", "Can they lead?", sections, videos, claims)
        self.assertIn("Actor Brief — Actor", result)
        self.assertIn("Executive Summary", result)
        self.assertIn("Clinical Profile", result)

    def test_extract_thesis_from_verdict(self):
        text = "**Verdict:** Actor is ready for drama lead. More details here."
        thesis = extract_thesis(text)
        self.assertTrue(thesis.startswith("Actor is ready for drama lead"))

    def test_extract_thesis_fallback(self):
        text = "This actor presents a complex profile with mixed signals."
        thesis = extract_thesis(text)
        self.assertIn("complex profile", thesis)

    def test_count_tiers(self):
        claims = [
            Claim(text="A", source_type="bts", access_level="RAW", tier="A"),
            Claim(text="B", source_type="bts", access_level="RAW", tier="B"),
            Claim(text="A2", source_type="bts", access_level="RAW", tier="A"),
        ]
        counts = count_tiers(claims)
        self.assertEqual(counts["A"], 2)
        self.assertEqual(counts["B"], 1)


if __name__ == "__main__":
    unittest.main()
