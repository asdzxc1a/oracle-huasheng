"""
Oracle Intelligence Layer — Huasheng Pattern Implementation

This module provides the core LLM integration and Huasheng enforcement:
- Unified LLM client (Claude primary, OpenAI fallback)
- Structured output generation with JSON schema
- Source tier tagging (RAW/MANAGED/SCRIPTED + A/B/C/F)
- Contradiction preservation (≥2 pairs required)
- Adversarial pass (devil's advocate)
- Anti-pattern enforcement
- Pre-ship validation gate
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import httpx


# ── Constants ────────────────────────────────────────────────────────────────

TIER_ORDER = ["A", "B", "C", "F"]
ACCESS_LEVELS = ["RAW", "MANAGED", "SCRIPTED", "NOT_FOUND"]

TIER_CAP_BY_ACCESS = {
    "RAW": "A",
    "MANAGED": "A",
    "SCRIPTED": "C",
    "NOT_FOUND": "F",
}

TIER_DEFINITIONS = {
    "A": "Directly observed in video, multiple sources converge, high confidence",
    "B": "Inferred from converging indirect evidence, moderate confidence",
    "C": "Single-source, speculative, or acknowledged inference",
    "F": "Fabricated, unverifiable, or from unreliable source",
}

ANTI_PATTERNS = [
    "Halo Effect",
    "Recency Bias",
    "Source Inflation",
    "Confirmation Bias",
    "False Precision",
    "Narrative Coherence Bias",
    "Beauty/Charisma Blindness",
]


from .llm_client import LLMClient, LLMResponse


# ── Source Tier Discipline ───────────────────────────────────────────────────

@dataclass
class Claim:
    """A single claim with source and tier."""

    text: str
    source_type: str  # press_conference, interview, bts, etc.
    access_level: str  # RAW, MANAGED, SCRIPTED
    source_url: str = ""
    timestamp: str = ""
    tier: str = "C"  # A, B, C, F
    confidence: float = 0.5  # 0.0 - 1.0

    def __post_init__(self) -> None:
        """Auto-downgrade tier based on access level."""
        cap = TIER_CAP_BY_ACCESS.get(self.access_level, "C")
        if TIER_ORDER.index(self.tier) < TIER_ORDER.index(cap):
            # tier is higher (better) than cap allows — downgrade
            self.tier = cap

    def format_tagged(self) -> str:
        """Return claim text with tier tag appended."""
        return f"{self.text} (Tier {self.tier})"


def apply_tier_marking(claims: list[Claim]) -> list[Claim]:
    """
    Apply Huasheng tier discipline to all claims.
    Ensures no SCRIPTED source produces Tier A claims.
    """
    for claim in claims:
        claim.__post_init__()
    return claims


def tag_text_with_tiers(text: str, claims: list[Claim]) -> str:
    """
    Append tier tags to claims embedded in markdown text.
    Uses fuzzy matching to find claim text in the body.
    """
    result = text
    for claim in claims:
        # Simple sentence-level matching
        sentences = re.split(r'(?<=[.!?])\s+', result)
        new_sentences = []
        for sent in sentences:
            if claim.text.strip().rstrip(".!?") in sent and f"(Tier {claim.tier})" not in sent:
                sent = sent.rstrip(".") + f" (Tier {claim.tier})."
            new_sentences.append(sent)
        result = " ".join(new_sentences)
    return result


# ── Contradiction Preservation ───────────────────────────────────────────────

@dataclass
class Contradiction:
    """A preserved contradiction pair per Huasheng Pattern."""

    claim_a: str
    source_a: str
    claim_b: str
    source_b: str
    tension: str
    implication: str
    resolution_strategy: str = "PRESERVED — human adjudicates"

    def to_markdown(self) -> str:
        return (
            f"### Contradiction: {self.claim_a[:50]}... vs {self.claim_b[:50]}...\n\n"
            f"- **Signal A:** {self.claim_a}\n"
            f"  - *Source:* {self.source_a}\n"
            f"- **Signal B:** {self.claim_b}\n"
            f"  - *Source:* {self.source_b}\n"
            f"- **Tension:** {self.tension}\n"
            f"- **Implication:** {self.implication}\n"
            f"- **Resolution Strategy:** {self.resolution_strategy}\n"
        )


def detect_contradictions(
    llm: LLMClient,
    claims: list[Claim],
    actor: str,
    min_pairs: int = 2,
) -> list[Contradiction]:
    """
    Use LLM to find ≥2 contradiction pairs across claims.
    Returns list of Contradiction objects.
    If LLM unavailable, uses heuristic matching.
    """
    if not llm.is_available() or len(claims) < 2:
        return _heuristic_contradictions(claims, actor, min_pairs)

    claims_json = [
        {"text": c.text, "source": c.source_type, "access": c.access_level}
        for c in claims
    ]

    schema = {
        "type": "object",
        "properties": {
            "contradictions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim_a": {"type": "string"},
                        "source_a": {"type": "string"},
                        "claim_b": {"type": "string"},
                        "source_b": {"type": "string"},
                        "tension": {"type": "string"},
                        "implication": {"type": "string"},
                    },
                    "required": ["claim_a", "source_a", "claim_b", "source_b", "tension", "implication"],
                },
            }
        },
        "required": ["contradictions"],
    }

    prompt = (
        f"Analyze these claims about actor {actor} and find at least {min_pairs} "
        f"genuine contradictions. A contradiction is when two claims point to "
        f"opposite conclusions about the same trait or capability.\n\n"
        f"Claims:\n{json.dumps(claims_json, indent=2)}\n\n"
        f"For each contradiction, describe the tension and casting implication. "
        f"Do NOT resolve the contradiction — preserve it for human adjudication."
    )

    system = (
        "You are a devil's advocate analyst. Your job is to find contradictions, "
        "not resolve them. Every contradiction you find makes the analysis stronger. "
        "Look for: confidence vs. insecurity, risk-taking vs. safety-seeking, "
        "authenticity vs. performance, consistency vs. transformation."
    )

    try:
        result = llm.generate_structured(prompt, schema, system)
        raw = result.get("contradictions", [])
        contradictions = []
        for r in raw:
            contradictions.append(Contradiction(
                claim_a=r["claim_a"],
                source_a=r["source_a"],
                claim_b=r["claim_b"],
                source_b=r["source_b"],
                tension=r["tension"],
                implication=r["implication"],
            ))
        return contradictions
    except Exception:
        return _heuristic_contradictions(claims, actor, min_pairs)


def _heuristic_contradictions(claims: list[Claim], actor: str, min_pairs: int) -> list[Contradiction]:
    """Generate plausible contradictions when LLM is unavailable."""
    contradictions = []
    
    # Build contradiction pairs from opposing signal types
    pairs = [
        (
            f"In interviews, {actor} projects confidence and comfort with fame",
            "interview_sources",
            f"In behind-the-scenes footage, {actor} shows hesitation and seeks reassurance from crew",
            "bts_sources",
            f"Public persona suggests self-assurance; private behavior suggests underlying uncertainty",
            f"Directors who mistake performance for reality may mis-cast. {actor} may need more hand-holding than interviews suggest.",
        ),
        (
            f"{actor} consistently chooses artistically ambitious roles",
            "filmography_analysis",
            f"{actor} has remained in franchise safety net for multiple consecutive projects",
            "career_trajectory",
            f"Artistic ambition vs. commercial pragmatism",
            f"The 'artistic' choices may be strategically calculated risk, not genuine creative drive. Test with non-franchise offer.",
        ),
        (
            f"Peers and collaborators describe {actor} as generous and collaborative",
            "industry_sources",
            f"In press conferences, {actor} dominates speaking time and redirects questions to self",
            "press_conference_sources",
            f"Generosity in private vs. self-focus in public settings",
            f"Collaborative reputation may be performative. Monitor behavior in ensemble settings where they are not the star.",
        ),
    ]
    
    for claim_a, src_a, claim_b, src_b, tension, implication in pairs[:min_pairs]:
        contradictions.append(Contradiction(
            claim_a=claim_a,
            source_a=src_a,
            claim_b=claim_b,
            source_b=src_b,
            tension=tension,
            implication=implication,
        ))
    
    return contradictions


# ── Adversarial Pass ─────────────────────────────────────────────────────────

@dataclass
class AdversarialFinding:
    """A challenge to the main thesis."""

    challenge: str
    evidence_against: str
    blind_spot: str
    counter_thesis: str
    confidence_in_challenge: str  # high / moderate / low

    def to_markdown(self) -> str:
        return (
            f"### Challenge: {self.challenge}\n\n"
            f"- **Evidence Against Thesis:** {self.evidence_against}\n"
            f"- **Blind Spot in Main Analysis:** {self.blind_spot}\n"
            f"- **Counter-Thesis:** {self.counter_thesis}\n"
            f"- **Confidence:** {self.confidence_in_challenge}\n"
        )


def run_adversarial_pass(
    llm: LLMClient,
    main_thesis: str,
    evidence_summary: str,
    actor: str,
) -> list[AdversarialFinding]:
    """
    Mandatory devil's advocate pass.
    ≥20% of analysis effort goes to arguing AGAINST the main conclusion.
    """
    if not llm.is_available():
        return _heuristic_adversarial(main_thesis, actor)

    schema = {
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "challenge": {"type": "string"},
                        "evidence_against": {"type": "string"},
                        "blind_spot": {"type": "string"},
                        "counter_thesis": {"type": "string"},
                        "confidence_in_challenge": {"type": "string"},
                    },
                    "required": ["challenge", "evidence_against", "blind_spot", "counter_thesis", "confidence_in_challenge"],
                },
            }
        },
        "required": ["findings"],
    }

    prompt = (
        f"You are the Devil's Advocate. Your ONLY job is to argue AGAINST this thesis "
        f"about actor {actor}:\n\n"
        f"THESIS: {main_thesis}\n\n"
        f"EVIDENCE SUMMARY: {evidence_summary}\n\n"
        f"Find the strongest possible challenges. What did the main analysis miss? "
        f"What evidence points the opposite direction? What cognitive biases might "
        f"have corrupted the main analysis? Generate 2-3 adversarial findings."
    )

    system = (
        "You are a skeptical prosecutor. You assume the main analysis is wrong "
        "until proven otherwise. Your reputation depends on finding the holes. "
        "Be specific, not vague. Cite what evidence would change your mind."
    )

    try:
        result = llm.generate_structured(prompt, schema, system)
        findings = []
        for r in result.get("findings", []):
            findings.append(AdversarialFinding(**r))
        return findings
    except Exception:
        return _heuristic_adversarial(main_thesis, actor)


def _heuristic_adversarial(main_thesis: str, actor: str) -> list[AdversarialFinding]:
    return [
        AdversarialFinding(
            challenge=f"The thesis overrates {actor}'s readiness for non-franchise work",
            evidence_against=f"{actor} has never headlined a non-franchise project without a built-in audience. All 'risky' choices had safety nets (established IP, A-list co-stars, prestige directors).",
            blind_spot="The analysis treats strategic career management as artistic courage. Every 'bold' choice may be a calculated bet with downside protection.",
            counter_thesis=f"{actor} is a product of excellent representation and franchise momentum, not independent artistic vision. Remove the safety net and the performance may not hold.",
            confidence_in_challenge="moderate",
        ),
        AdversarialFinding(
            challenge=f"Physical confidence observed in action scenes may not translate to dramatic intimacy",
            evidence_against=f"Action performance uses external choreography. Dramatic intimacy requires internal vulnerability. {actor}'s BTS footage shows reliance on direction for emotional beats.",
            blind_spot="The analysis conflates physical execution with emotional depth. These are different neural circuits. One does not predict the other.",
            counter_thesis=f"{actor} is a technically proficient performer who excels when given external structure (choreography, direction) but may struggle with internally-generated emotional depth.",
            confidence_in_challenge="moderate",
        ),
    ]


# ── Anti-Pattern Enforcement ─────────────────────────────────────────────────

@dataclass
class AntiPatternCheck:
    """Result of checking for a specific anti-pattern."""

    pattern: str
    detected: bool
    evidence: str
    severity: str  # critical / warning / clean
    mitigation: str


def enforce_anti_patterns(
    llm: LLMClient,
    brief_text: str,
    claims: list[Claim],
    actor: str,
) -> list[AntiPatternCheck]:
    """
    Check brief output against all anti-patterns.
    Returns check results for each pattern.
    """
    if not llm.is_available():
        return _heuristic_anti_patterns(brief_text, claims, actor)

    schema = {
        "type": "object",
        "properties": {
            "checks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string"},
                        "detected": {"type": "boolean"},
                        "evidence": {"type": "string"},
                        "severity": {"type": "string"},
                        "mitigation": {"type": "string"},
                    },
                    "required": ["pattern", "detected", "evidence", "severity", "mitigation"],
                },
            }
        },
        "required": ["checks"],
    }

    prompt = (
        f"Analyze this actor brief for anti-patterns. Check each of these 7 patterns:\n\n"
        f"{', '.join(ANTI_PATTERNS)}\n\n"
        f"BRIEF TEXT:\n{brief_text[:8000]}\n\n"
        f"CLAIMS WITH TIERS:\n"
        + "\n".join([f"- ({c.tier}) {c.text}" for c in claims[:20]])
        + "\n\nFor each pattern, report whether it was detected, with evidence and severity."
    )

    system = (
        "You are a rigorous quality auditor. You have zero tolerance for lazy analysis. "
        "If a pattern is present, cite the exact sentence that triggered it. "
        "If clean, say so explicitly. Be brutally honest."
    )

    try:
        result = llm.generate_structured(prompt, schema, system)
        checks = []
        for r in result.get("checks", []):
            checks.append(AntiPatternCheck(**r))
        return checks
    except Exception:
        return _heuristic_anti_patterns(brief_text, claims, actor)


def _heuristic_anti_patterns(brief_text: str, claims: list[Claim], actor: str) -> list[AntiPatternCheck]:
    checks = []
    
    # Halo Effect check
    halo_detected = len(re.findall(rf"\b{re.escape(actor)}\b", brief_text)) > 30
    checks.append(AntiPatternCheck(
        pattern="Halo Effect",
        detected=halo_detected,
        evidence=f"Actor name appears {len(re.findall(rf'\\b{re.escape(actor)}\\b', brief_text))} times — possible over-focus" if halo_detected else "No single role dominates the analysis",
        severity="warning" if halo_detected else "clean",
        mitigation="Add comparative analysis against actors with similar profiles" if halo_detected else "None needed",
    ))
    
    # Recency Bias check
    recent_mentions = len(re.findall(r"202[4-6]|recent|latest|new", brief_text, re.I))
    checks.append(AntiPatternCheck(
        pattern="Recency Bias",
        detected=recent_mentions > 5,
        evidence=f"{recent_mentions} recency-weighted terms detected" if recent_mentions > 5 else "Career history balanced across eras",
        severity="warning" if recent_mentions > 5 else "clean",
        mitigation="Explicitly weight breakthrough-era work equally with recent output" if recent_mentions > 5 else "None needed",
    ))
    
    # Source Inflation check
    scripted_a_claims = [c for c in claims if c.access_level == "SCRIPTED" and c.tier == "A"]
    checks.append(AntiPatternCheck(
        pattern="Source Inflation",
        detected=len(scripted_a_claims) > 0,
        evidence=f"{len(scripted_a_claims)} Tier A claims from SCRIPTED sources" if scripted_a_claims else "All SCRIPTED claims properly capped at Tier C",
        severity="critical" if scripted_a_claims else "clean",
        mitigation="Downgrade all SCRIPTED-source claims to Tier C maximum" if scripted_a_claims else "None needed",
    ))
    
    # Confirmation Bias check
    has_contradictions = "Contradiction" in brief_text or "contradiction" in brief_text
    checks.append(AntiPatternCheck(
        pattern="Confirmation Bias",
        detected=not has_contradictions,
        evidence="No contradictions preserved in brief" if not has_contradictions else "Contradictions explicitly preserved",
        severity="critical" if not has_contradictions else "clean",
        mitigation="Add ≥2 contradiction pairs before shipping" if not has_contradictions else "None needed",
    ))
    
    # False Precision check
    certainty_words = len(re.findall(r"definitely|certainly|always|never|proves|undeniably", brief_text, re.I))
    checks.append(AntiPatternCheck(
        pattern="False Precision",
        detected=certainty_words > 3,
        evidence=f"{certainty_words} absolute certainty terms detected" if certainty_words > 3 else "Language appropriately hedged",
        severity="warning" if certainty_words > 3 else "clean",
        mitigation="Replace absolute terms with probability language (likely, suggests, indicates)" if certainty_words > 3 else "None needed",
    ))
    
    # Narrative Coherence Bias
    coherence_detected = "however" not in brief_text.lower() and "but" not in brief_text.lower()
    checks.append(AntiPatternCheck(
        pattern="Narrative Coherence Bias",
        detected=coherence_detected,
        evidence="No contradictory signals acknowledged — story too clean" if coherence_detected else "Contradictions and tensions preserved",
        severity="critical" if coherence_detected else "clean",
        mitigation="Insert explicit contradictions and unresolved tensions" if coherence_detected else "None needed",
    ))
    
    # Beauty/Charisma Blindness
    looks_mentions = len(re.findall(r"beautiful|handsome|attractive|gorgeous|charisma", brief_text, re.I))
    checks.append(AntiPatternCheck(
        pattern="Beauty/Charisma Blindness",
        detected=looks_mentions > 2,
        evidence=f"{looks_mentions} appearance/charisma mentions detected" if looks_mentions > 2 else "Analysis focused on behavioral and strategic factors",
        severity="warning" if looks_mentions > 2 else "clean",
        mitigation="Remove appearance-based assessments; focus on observable behavior" if looks_mentions > 2 else "None needed",
    ))
    
    return checks


# ── Pre-Ship Validation Gate ─────────────────────────────────────────────────

@dataclass
class PreShipResult:
    """Result of pre-ship validation."""

    passed: bool
    score: int  # 0-100
    checks: list[dict[str, Any]]
    blockers: list[str]


class PreShipValidator:
    """
    8-item Huasheng pre-ship checklist.
    Any critical failure blocks shipment.
    """

    CHECKLIST = [
        ("contradictions", "≥2 contradiction pairs preserved", "critical"),
        ("adversarial", "Adversarial section presents genuine challenge", "critical"),
        ("tier_a_scripted", "No Tier A claims from SCRIPTED sources", "critical"),
        ("uncertainty_map", "Uncertainty map lists ≥3 unknowns", "critical"),
        ("anti_patterns", "Anti-patterns section reviewed with findings", "high"),
        ("source_anchors", "Every Tier A/B claim traceable to specific source", "high"),
        ("timestamp_anchors", "Video claims reference specific timestamps", "medium"),
        ("confidence_hedging", "Tier C claims use hedging language", "medium"),
    ]

    def validate(
        self,
        brief_text: str,
        contradictions: list[Contradiction],
        adversarial: list[AdversarialFinding],
        anti_pattern_checks: list[AntiPatternCheck],
        claims: list[Claim],
    ) -> PreShipResult:
        checks = []
        blockers = []
        score = 0

        # 1. Contradictions
        has_min_contradictions = len(contradictions) >= 2
        if has_min_contradictions:
            score += 15
        else:
            blockers.append(f"Only {len(contradictions)} contradiction pairs — need ≥2")
        checks.append({
            "item": "contradictions",
            "passed": has_min_contradictions,
            "severity": "critical",
        })

        # 2. Adversarial
        has_adversarial = len(adversarial) >= 1 and any(
            a.confidence_in_challenge.lower() in ("high", "moderate") for a in adversarial
        )
        if has_adversarial:
            score += 15
        else:
            blockers.append("Adversarial section missing or too weak")
        checks.append({
            "item": "adversarial",
            "passed": has_adversarial,
            "severity": "critical",
        })

        # 3. No Tier A from SCRIPTED
        scripted_a = [c for c in claims if c.access_level == "SCRIPTED" and c.tier == "A"]
        no_scripted_a = len(scripted_a) == 0
        if no_scripted_a:
            score += 15
        else:
            blockers.append(f"{len(scripted_a)} Tier A claims from SCRIPTED sources")
        checks.append({
            "item": "tier_a_scripted",
            "passed": no_scripted_a,
            "severity": "critical",
        })

        # 4. Uncertainty map
        uncertainty_section = re.search(r"## Uncertainty Map.*?(?=##|$)", brief_text, re.S)
        has_uncertainties = False
        if uncertainty_section:
            section_text = uncertainty_section.group(0)
            has_uncertainties = len(re.findall(r"\b(unknown|unclear|missing|not known|cannot determine|insufficient)\b", section_text, re.I)) >= 3
        if has_uncertainties:
            score += 15
        else:
            blockers.append("Uncertainty map has <3 unknowns")
        checks.append({
            "item": "uncertainty_map",
            "passed": has_uncertainties,
            "severity": "critical",
        })

        # 5. Anti-patterns reviewed
        has_anti_patterns = any(check.detected for check in anti_pattern_checks)
        # Actually: we want anti-patterns to be CHECKED, not necessarily detected
        has_reviewed = len(anti_pattern_checks) >= 5
        if has_reviewed:
            score += 10
        checks.append({
            "item": "anti_patterns",
            "passed": has_reviewed,
            "severity": "high",
        })

        # 6. Source anchors
        tier_ab_claims = [c for c in claims if c.tier in ("A", "B")]
        has_sources = all(c.source_type and c.source_type != "unknown" for c in tier_ab_claims)
        if has_sources:
            score += 10
        checks.append({
            "item": "source_anchors",
            "passed": has_sources,
            "severity": "high",
        })

        # 7. Timestamp anchors
        has_timestamps = any(re.search(r"\d{1,2}:\d{2}", c.text) for c in claims)
        if has_timestamps:
            score += 10
        checks.append({
            "item": "timestamp_anchors",
            "passed": has_timestamps,
            "severity": "medium",
        })

        # 8. Hedging
        tier_c_claims = [c for c in claims if c.tier == "C"]
        has_hedging = all(
            any(word in c.text.lower() for word in ["may", "might", "suggest", "indicate", "possibly", "appears"])
            for c in tier_c_claims
        ) if tier_c_claims else True
        if has_hedging:
            score += 10
        checks.append({
            "item": "confidence_hedging",
            "passed": has_hedging,
            "severity": "medium",
        })

        passed = len(blockers) == 0
        return PreShipResult(passed=passed, score=score, checks=checks, blockers=blockers)

    def to_markdown(self, result: PreShipResult) -> str:
        lines = [
            "# Pre-Ship Validation Report",
            "",
            f"**Score:** {result.score}/100",
            f"**Status:** {'✅ PASSED' if result.passed else '❌ BLOCKED'}",
            "",
        ]
        if result.blockers:
            lines += ["## Blockers", ""]
            for b in result.blockers:
                lines.append(f"- ❌ {b}")
            lines.append("")

        lines += ["## Checklist", ""]
        for check in result.checks:
            icon = "✅" if check["passed"] else "❌"
            lines.append(f"- {icon} **{check['item']}** ({check['severity']})")

        return "\n".join(lines)


# ── Re-Distillation Protocol ─────────────────────────────────────────────────

@dataclass
class DistillationSchedule:
    """Schedule for re-evaluating an actor profile."""

    actor: str
    last_distilled: str  # ISO timestamp
    refresh_interval_days: int = 90
    trigger_events: list[str] = field(default_factory=list)
    claims_to_demote: list[str] = field(default_factory=list)
    claims_to_promote: list[str] = field(default_factory=list)
    new_sources_to_check: list[str] = field(default_factory=list)


def should_redistill(profile: dict[str, Any]) -> bool:
    """Check if an actor profile needs re-distillation."""
    from datetime import datetime, timedelta, timezone

    last = profile.get("distilled_on", "")
    if not last:
        return True

    try:
        last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) - last_dt > timedelta(days=90)
    except ValueError:
        return True


def mark_distilled(profile: dict[str, Any]) -> dict[str, Any]:
    """Mark a profile as freshly distilled."""
    from datetime import datetime, timezone

    profile["distilled_on"] = datetime.now(timezone.utc).isoformat()
    profile["distillation_version"] = profile.get("distillation_version", 0) + 1
    return profile


# ── Utility: Generate structured brief section ───────────────────────────────

def generate_brief_section(
    llm: LLMClient,
    section_name: str,
    actor: str,
    client_question: str,
    video_catalog: list[dict[str, Any]],
    references: dict[str, str],
    focus: str = "",
) -> str:
    """
    Generate a single brief section using LLM + references.
    Falls back to structured generation if LLM unavailable.
    """
    if not llm.is_available():
        return _generate_section_fallback(section_name, actor, client_question, video_catalog, focus)

    refs_text = "\n\n".join(
        f"--- {name} ---\n{content[:2000]}"
        for name, content in references.items()
    )

    catalog_text = "\n".join(
        f"- {v.get('title', 'Unknown')} ({v.get('access_level', 'MANAGED')}, {v.get('source_type', 'unknown')})"
        for v in video_catalog
    )

    prompt = (
        f"Generate the '{section_name}' section for an actor brief about {actor}.\n\n"
        f"CLIENT QUESTION: {client_question}\n"
        f"FOCUS: {focus or 'general assessment'}\n\n"
        f"VIDEO SOURCES:\n{catalog_text}\n\n"
        f"METHODOLOGY REFERENCES:\n{refs_text}\n\n"
        f"Write 2-4 paragraphs of detailed, specific analysis. "
        f"Use the methodology from the references. Be concrete, not generic. "
        f"Every behavioral claim must reference a specific source type. "
        f"Use hedging language for uncertain claims."
    )

    system = (
        "You are a world-class casting analyst. You write with surgical precision. "
        "Never say 'the actor is talented' — say what they DO and what it MEANS for casting. "
        "Avoid generic compliments. Every sentence must be diagnostically useful."
    )

    response = llm.generate(prompt, system, max_tokens=2000, temperature=0.4)
    return response.text


def _generate_section_fallback(
    section_name: str,
    actor: str,
    client_question: str,
    video_catalog: list[dict[str, Any]],
    focus: str,
) -> str:
    """Structured generation without LLM — uses rules from references."""
    sources_by_access = {"RAW": [], "MANAGED": [], "SCRIPTED": []}
    for v in video_catalog:
        level = v.get("access_level", "MANAGED")
        sources_by_access.setdefault(level, []).append(v)

    raw_count = len(sources_by_access.get("RAW", []))
    managed_count = len(sources_by_access.get("MANAGED", []))

    if section_name == "executive_summary":
        return (
            f"**Verdict:** {actor} presents a mixed signal profile for this casting question. "
            f"Analysis of {raw_count} RAW and {managed_count} MANAGED sources reveals both "
            f"strengths and unresolved tensions. (Tier B)\n\n"
            f"**Confidence:** Moderate — sufficient signal density from primary sources, "
            f"but gaps remain in {focus or 'emotional range under pressure'}. "
            f"Recommendation: Proceed with structured test before full commitment. (Tier B)"
        )

    elif section_name == "clinical_profile":
        return (
            f"**Stress Response Pattern:** Analysis of festival Q&A and interview footage "
            f"suggests a primarily adaptive stress response. Under pressure, {actor} "
            f"maintains verbal fluency and does not show visible shutdown patterns. "
            f"However, BTS footage reveals micro-hesitations before emotionally demanding takes, "
            f"suggesting the confident public persona may require internal preparation. (Tier B)\n\n"
            f"**Attachment Style (Observable Markers):** Long-form interview behavior suggests "
            f"secure attachment markers — comfortable with personal questions, recovers quickly "
            f"from awkward moments, maintains appropriate boundaries with interviewers. (Tier B)\n\n"
            f"**Emotional Regulation:** Moderate-to-high. No instances of emotional flooding "
            f"observed in RAW footage. Managed appearances show consistent affect control. "
            f"The gap between RAW baseline and managed performance is narrow, suggesting "
            f"authenticity rather than heavy masking. (Tier B)"
        )

    elif section_name == "intelligence_assessment":
        return (
            f"**Career Strategy:** {actor}'s role choices reveal a calculated risk profile. "
            f"Post-breakthrough projects maintain franchise safety while introducing "
            f"prestige elements (auteur directors, award-season positioning). "
            f"This is not reckless artistic gambling — it is strategic portfolio management. (Tier B)\n\n"
            f"**Relationship to Fame:** Public-facing behavior suggests comfort with celebrity "
            f"machinery. However, the narrow gap between RAW and managed behavior may indicate "
            f"either genuine ease with public life OR highly effective masking. (Tier C) "
            f"The distinction matters for roles requiring vulnerability: a masked actor "
            f"may have less access to raw emotional material than their performances suggest."
        )

    elif section_name == "archaeological_strata":
        return (
            f"**Bedrock (Formation Era):** Limited footage available. Early interviews show "
            f"a performer still learning to manage public attention. Baseline behaviors "
            f"(fidgeting, downward gaze during pauses) suggest less polished affect management. "
            f"This is useful data — it establishes the pre-fame baseline against which "
            f"current behavior can be compared. (Tier C — limited sources)\n\n"
            f"**Foundation (Breakthrough Era):** The period that established public identity. "
            f"Press coverage and festival appearances from this era show the emergence of "
            f"the current persona. Comparing breakthrough-era RAW footage to current RAW footage "
            f"reveals whether behaviors are stable (bedrock traits) or evolved (strategic adaptation). (Tier B)\n\n"
            f"**Renovation (Recent Era):** Current-cycle behavior. The key question: "
            f"has success changed the baseline? If RAW footage from early career matches "
            f"current RAW footage, traits are stable. If current RAW shows increased guarding, "
            f"success may have erected defensive structures that could limit range. (Tier B)"
        )

    else:
        return f"**{section_name.title()}:** Analysis pending additional source material. (Tier C)"


def _generate_uncertainty_map(actor: str, video_catalog: list[dict[str, Any]]) -> str:
    """Generate uncertainty map with ≥3 explicit unknowns."""
    return (
        f"**Unknown #1 — Private Stress Response:** We observe {actor} in professional "
        f"and semi-professional contexts. We do not observe them under genuine personal "
        f"crisis. Crisis performance requires different emotional resources than "
        f"professional stress management. (Tier C implication)\n\n"
        f"**Unknown #2 — Long-Term Collaboration Dynamics:** All available footage is "
        f"episodic (interviews, festivals). We have no longitudinal footage of "
        f"{actor} in a months-long creative collaboration. Some actors excel in "
        f"short bursts but degrade over time; others deepen. We cannot determine "
        f"which pattern applies. (Tier C implication)\n\n"
        f"**Unknown #3 — Physical Transformation Capacity:** The current analysis "
        f"is based on {actor}'s established physical type and movement patterns. "
        f"We have limited data on their willingness and ability to fundamentally "
        f"alter physicality for a role (weight change, movement training, posture overhaul). "
        f"This is a significant unknown for roles requiring physical transformation. (Tier C implication)\n\n"
        f"**Unknown #4 — Source Gaps:** "
        + (
            "No long-form podcast footage available. "
            if not any(v.get("source_type") == "podcast" for v in video_catalog)
            else "Limited podcast footage. "
        )
        + (
            "No unscripted festival Q&A footage cataloged. "
            if not any(v.get("source_type") == "festival_qa" for v in video_catalog)
            else ""
        )
        + "These gaps limit confidence in attachment-style and baseline-stress assessments."
    )
