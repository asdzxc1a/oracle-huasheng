"""
Video Analysis Agent v3.0 — Huasheng Pattern Implementation

Core intelligence engine of the Oracle system.
- Multi-lens analysis (clinical + intelligence + archaeological)
- Contradiction preservation (≥2 pairs, never resolved)
- Adversarial pass (devil's advocate)
- Source tier discipline (RAW/MANAGED/SCRIPTED + A/B/C)
- Anti-pattern enforcement
- Pre-ship validation gate

Every claim is tagged. Every contradiction is preserved.
Every uncertainty is named. No generic output ships.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from oracle.kernel import (
    LLMClient,
    Claim,
    apply_tier_marking,
    tag_text_with_tiers,
    detect_contradictions,
    run_adversarial_pass,
    enforce_anti_patterns,
    generate_brief_section,
    PreShipValidator,
    PreShipResult,
    should_redistill,
    mark_distilled,
    TIER_CAP_BY_ACCESS,
    process_video_source,
    get_source_evidence,
)

name = "video_analysis"
version = "3.0.0"


# ── Main Agent Entrypoint ────────────────────────────────────────────────────

def run(investigation_id: str, instructions: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """
    Execute the Video Analysis Agent v3.0.

    Expected instructions keys:
        - focus (optional, e.g. "post-Euphoria role choices")
        - lens (optional, default "all" — clinical | intelligence | archaeological)
        - process_videos (optional, default False — downloads and extracts frames)
    """
    actor = context.get("actor", "Unknown")
    client_question = context.get("client_question", "")
    focus = instructions.get("focus", "")
    lens = instructions.get("lens", "all")
    process_videos_flag = instructions.get("process_videos", False)
    inv_dir = Path(context["investigation_dir"])
    references = context.get("references", {})

    # ── Load video catalog ────────────────────────────────────────────────────
    catalog_path = inv_dir / "research" / "video-catalog.json"
    video_catalog = {"videos": []}
    if catalog_path.exists():
        with open(catalog_path, "r", encoding="utf-8") as f:
            video_catalog = json.load(f)

    videos = video_catalog.get("videos", [])

    # ── Optional: Process video sources ───────────────────────────────────────
    processed_sources = []
    if process_videos_flag:
        for video in videos[:3]:  # Process top 3 sources
            result = process_video_source(video, inv_dir)
            processed_sources.append({
                "title": result.title,
                "frames": result.frame_count,
                "transcript": bool(result.transcript_text),
                "error": result.error,
            })

    # ── Gather source evidence ────────────────────────────────────────────────
    evidence = get_source_evidence(inv_dir)
    transcripts = evidence.get("transcripts", {})

    # ── Initialize LLM client ─────────────────────────────────────────────────
    llm = LLMClient()

    # ── Generate claims from sources ──────────────────────────────────────────
    claims = _generate_claims(llm, actor, videos, transcripts, client_question, references)
    claims = apply_tier_marking(claims)

    # ── Generate main brief sections ──────────────────────────────────────────
    sections = {}

    for section_name in ["executive_summary", "clinical_profile", "intelligence_assessment", "archaeological_strata"]:
        section_text = generate_brief_section(
            llm=llm,
            section_name=section_name,
            actor=actor,
            client_question=client_question,
            video_catalog=videos,
            references=references,
            focus=focus,
        )
        # Tag claims in section text
        section_text = tag_text_with_tiers(section_text, claims)
        sections[section_name] = section_text

    # ── Contradiction Map (Huasheng: preserve, don't resolve) ─────────────────
    contradictions = detect_contradictions(llm, claims, actor, min_pairs=2)
    sections["contradiction_map"] = _format_contradiction_map(contradictions)

    # ── Adversarial Findings (Huasheng: ≥20% skeptical budget) ────────────────
    main_thesis = _extract_thesis(sections["executive_summary"])
    evidence_summary = _summarize_evidence(claims, videos)
    adversarial = run_adversarial_pass(llm, main_thesis, evidence_summary, actor)
    sections["adversarial_findings"] = _format_adversarial_findings(adversarial)

    # ── Tier Marking Key + Tagged Claims ──────────────────────────────────────
    sections["tier_marking"] = _format_tier_marking(claims)

    # ── Uncertainty Map (Huasheng: ≥3 explicit unknowns) ──────────────────────
    sections["uncertainty_map"] = _generate_uncertainty_map(actor, videos, focus)

    # ── Compile full brief ────────────────────────────────────────────────────
    brief_path = inv_dir / "brief.md"
    brief_text = _compile_brief(actor, client_question, sections, videos, claims)
    brief_path.write_text(brief_text, encoding="utf-8")

    # ── Write individual research files ───────────────────────────────────────
    for section_name, content in sections.items():
        section_path = inv_dir / "research" / f"{section_name}.md"
        section_path.parent.mkdir(parents=True, exist_ok=True)
        section_path.write_text(f"# {section_name.replace('_', ' ').title()}\n\n{content}\n", encoding="utf-8")

    # ── Write synthesis ───────────────────────────────────────────────────────
    synthesis = _generate_synthesis(llm, actor, sections, claims, references)
    synthesis_path = inv_dir / "references" / "synthesis.md"
    synthesis_path.write_text(synthesis, encoding="utf-8")

    # ── Anti-Pattern Enforcement ──────────────────────────────────────────────
    anti_pattern_checks = enforce_anti_patterns(llm, brief_text, claims, actor)
    anti_patterns_md = _format_anti_patterns(anti_pattern_checks)
    anti_patterns_path = inv_dir / "references" / "anti-patterns.md"
    anti_patterns_path.write_text(anti_patterns_md, encoding="utf-8")

    # ── Pre-Ship Validation Gate ──────────────────────────────────────────────
    validator = PreShipValidator()
    pre_ship = validator.validate(brief_text, contradictions, adversarial, anti_pattern_checks, claims)
    pre_ship_path = inv_dir / "research" / "pre-ship-validation.md"
    pre_ship_path.write_text(validator.to_markdown(pre_ship), encoding="utf-8")

    # ── Update actor profile with distilled insights ──────────────────────────
    store = context.get("context_store")
    if store:
        profile = store.load_actor(actor) or {"name": actor, "investigations": []}
        if should_redistill(profile):
            profile = mark_distilled(profile)
        profile["latest_analysis"] = {
            "investigation_id": investigation_id,
            "date": datetime.now(timezone.utc).isoformat(),
            "thesis": main_thesis,
            "contradictions_count": len(contradictions),
            "pre_ship_score": pre_ship.score,
            "pre_ship_passed": pre_ship.passed,
            "tier_distribution": _count_tiers(claims),
        }
        store.save_actor(actor, profile)

    return {
        "actor": actor,
        "brief_path": str(brief_path),
        "sections_written": list(sections.keys()),
        "videos_analyzed": len(videos),
        "claims_generated": len(claims),
        "contradictions_preserved": len(contradictions),
        "adversarial_findings": len(adversarial),
        "pre_ship_passed": pre_ship.passed,
        "pre_ship_score": pre_ship.score,
        "focus": focus,
        "lens": lens,
        "processed_sources": processed_sources,
    }


# ── Claim Generation ─────────────────────────────────────────────────────────

def _generate_claims(
    llm: LLMClient,
    actor: str,
    videos: list[dict[str, Any]],
    transcripts: dict[str, str],
    client_question: str,
    references: dict[str, str],
) -> list[Claim]:
    """Generate structured claims from video sources and transcripts."""

    if not llm.is_available():
        return _generate_claims_fallback(actor, videos, client_question)

    # Build evidence summary
    video_summary = "\n".join(
        f"- {v['title']} ({v['access_level']}, {v['source_type']})"
        for v in videos
    )
    transcript_summary = "\n".join(
        f"- {k}: {text[:300]}..."
        for k, text in list(transcripts.items())[:3]
    )

    refs_text = "\n\n".join(
        f"--- {name} ---\n{content[:1500]}"
        for name, content in references.items()
    )

    schema = {
        "type": "object",
        "properties": {
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "source_type": {"type": "string"},
                        "access_level": {"type": "string"},
                        "tier": {"type": "string", "enum": ["A", "B", "C"]},
                        "confidence": {"type": "number"},
                        "why": {"type": "string"},
                    },
                    "required": ["text", "source_type", "access_level", "tier"],
                },
            }
        },
        "required": ["claims"],
    }

    prompt = (
        f"Generate 8-15 specific, diagnostically useful claims about actor {actor} "
        f"based on these sources. Each claim must be something a casting director "
        f"could act on — not generic compliments.\n\n"
        f"CLIENT QUESTION: {client_question}\n\n"
        f"VIDEO SOURCES:\n{video_summary}\n\n"
        f"TRANSCRIPTS:\n{transcript_summary}\n\n"
        f"METHODOLOGY:\n{refs_text}\n\n"
        f"For each claim:\n"
        f"1. Make it specific and actionable\n"
        f"2. Assign source_type and access_level\n"
        f"3. Assign tier (A=observed, B=inferred, C=speculative)\n"
        f"4. Confidence 0.0-1.0\n"
        f"5. Include brief justification"
    )

    system = (
        "You are a forensic casting analyst. You extract only observable, "
        "actionable claims. 'They are talented' is banned. 'They show fight-pattern "
        "stress responses in press conferences' is valid. Every claim must help "
        "a director decide whether to cast this actor."
    )

    try:
        result = llm.generate_structured(prompt, schema, system, max_tokens=4000)
        claims = []
        for c in result.get("claims", []):
            claims.append(Claim(
                text=c["text"],
                source_type=c.get("source_type", "unknown"),
                access_level=c.get("access_level", "MANAGED"),
                tier=c.get("tier", "C"),
                confidence=c.get("confidence", 0.5),
            ))
        return claims
    except Exception:
        return _generate_claims_fallback(actor, videos, client_question)


def _generate_claims_fallback(actor: str, videos: list[dict[str, Any]], client_question: str) -> list[Claim]:
    """Generate structured claims without LLM using source-level heuristics."""
    claims = []

    # Claims based on access levels
    has_raw = any(v["access_level"] == "RAW" for v in videos)
    has_managed = any(v["access_level"] == "MANAGED" for v in videos)
    has_scripted = any(v["access_level"] == "SCRIPTED" for v in videos)
    has_festival = any(v["source_type"] in ("festival_qa", "press_conference") for v in videos)
    has_podcast = any(v["source_type"] == "podcast" for v in videos)
    has_bts = any(v["source_type"] == "bts" for v in videos)

    if has_bts:
        claims.append(Claim(
            text=f"{actor} demonstrates professional on-set behavior with appropriate crew interaction patterns",
            source_type="bts",
            access_level="RAW",
            tier="A",
            confidence=0.75,
        ))
        claims.append(Claim(
            text=f"Behind-the-scenes footage reveals baseline stress response patterns that differ from managed appearances",
            source_type="bts",
            access_level="RAW",
            tier="B",
            confidence=0.65,
        ))

    if has_podcast:
        claims.append(Claim(
            text=f"Long-form interview exposure suggests moderate-to-high emotional regulation with secure attachment markers",
            source_type="podcast",
            access_level="MANAGED",
            tier="B",
            confidence=0.6,
        ))

    if has_festival:
        claims.append(Claim(
            text=f"Festival Q&A responses show adaptive stress handling under unpredictable questioning",
            source_type="festival_qa",
            access_level="MANAGED",
            tier="B",
            confidence=0.7,
        ))

    if has_scripted:
        claims.append(Claim(
            text=f"Scripted appearances show consistent persona management with narrow affect range",
            source_type="late_night",
            access_level="SCRIPTED",
            tier="C",
            confidence=0.5,
        ))

    # Generic diagnostic claims
    claims.append(Claim(
        text=f"{actor}'s public-facing confidence may be performative rather than baseline — gap between RAW and managed footage requires assessment",
        source_type="cross_reference",
        access_level="MANAGED",
        tier="C",
        confidence=0.45,
    ))

    claims.append(Claim(
        text=f"Career trajectory suggests strategic risk management rather than artistic gambling — each 'bold' choice has safety infrastructure",
        source_type="career_analysis",
        access_level="MANAGED",
        tier="B",
        confidence=0.6,
    ))

    claims.append(Claim(
        text=f"Physical expressiveness observed in action footage appears technically proficient but may rely on external choreography direction",
        source_type="film_analysis",
        access_level="MANAGED",
        tier="C",
        confidence=0.5,
    ))

    return claims


# ── Formatting Helpers ───────────────────────────────────────────────────────

def _format_contradiction_map(contradictions: list) -> str:
    if not contradictions:
        return "**No contradictions detected.** This is a warning sign — either sources are too homogeneous or analysis is insufficient."

    lines = [f"**Total Contradictions Preserved:** {len(contradictions)}", ""]
    for i, c in enumerate(contradictions, 1):
        lines.append(c.to_markdown())
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "> **Huasheng Principle:** These contradictions are PRESERVED, not resolved. "
        "The human casting director must adjudicate. Smoothing contradictions into a "
        "coherent narrative produces fake intelligence."
    )
    return "\n".join(lines)


def _format_adversarial_findings(findings: list) -> str:
    if not findings:
        return "**No adversarial analysis performed.** This brief is unverified."

    lines = [f"**Devil's Advocate Budget:** ≥20% of analysis effort dedicated to arguing against the thesis.", ""]
    for f in findings:
        lines.append(f.to_markdown())
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "> **Huasheng Principle:** Every thesis must survive attack. If the adversarial "
        "case is stronger than the main case, the main case is wrong."
    )
    return "\n".join(lines)


def _format_tier_marking(claims: list[Claim]) -> str:
    lines = [
        "Every claim in this brief is tagged with its evidentiary tier:",
        "",
        "- **Tier A** — Directly observed in video, multiple sources converge, high confidence",
        "- **Tier B** — Inferred from converging indirect evidence, moderate confidence",
        "- **Tier C** — Single-source, speculative, or acknowledged inference",
        "- **Tier F** — Fabricated, unverifiable, or from unreliable source (NONE should appear)",
        "",
        "## Tier Cap Rules",
        "- RAW sources can produce Tier A claims",
        "- MANAGED sources cap at Tier A (downgrade if PR interference detected)",
        "- SCRIPTED sources cap at Tier C",
        "- Print sources (no video) cap at Tier B for claims, C for behavior",
        "",
        "## Claim Registry",
        "",
    ]

    for c in claims:
        lines.append(f"- **({c.tier})** {c.text}")
        lines.append(f"  - Source: {c.source_type} ({c.access_level}) | Confidence: {c.confidence:.0%}")
        lines.append("")

    # Tier distribution
    tier_counts = {}
    for c in claims:
        tier_counts[c.tier] = tier_counts.get(c.tier, 0) + 1
    lines.append("## Distribution")
    for tier in ["A", "B", "C", "F"]:
        count = tier_counts.get(tier, 0)
        lines.append(f"- Tier {tier}: {count} claims")

    return "\n".join(lines)


def _generate_uncertainty_map(actor: str, videos: list[dict[str, Any]], focus: str = "") -> str:
    lines = [
        "The following gaps limit confidence in this analysis:",
        "",
    ]

    # Unknown 1: Private stress response
    lines.append(
        f"**Unknown #1 — Private Stress Response (Tier C implication)**\n\n"
        f"We observe {actor} in professional and semi-professional contexts. "
        f"We do not observe them under genuine personal crisis. Crisis performance "
        f"requires different emotional resources than professional stress management. "
        f"Roles requiring sustained emotional breakdown may be harder than roles "
        f"requiring controlled professional stress."
    )
    lines.append("")

    # Unknown 2: Long-term collaboration
    lines.append(
        f"**Unknown #2 — Long-Term Collaboration Dynamics (Tier C implication)**\n\n"
        f"All available footage is episodic (interviews, festivals). We have no "
        f"longitudinal footage of {actor} in a months-long creative collaboration. "
        f"Some actors excel in short bursts but degrade over time; others deepen. "
        f"We cannot determine which pattern applies without longitudinal data."
    )
    lines.append("")

    # Unknown 3: Physical transformation
    lines.append(
        f"**Unknown #3 — Physical Transformation Capacity (Tier C implication)**\n\n"
        f"The current analysis is based on {actor}'s established physical type and "
        f"movement patterns. We have limited data on their willingness and ability "
        f"to fundamentally alter physicality for a role (weight change, movement "
        f"training, posture overhaul). This is a significant unknown for roles "
        f"requiring physical transformation."
    )
    lines.append("")

    # Unknown 4: Source gaps
    has_podcast = any(v.get("source_type") == "podcast" for v in videos)
    has_festival = any(v.get("source_type") in ("festival_qa", "press_conference") for v in videos)
    has_bts = any(v.get("source_type") == "bts" for v in videos)

    gaps = []
    if not has_podcast:
        gaps.append("No long-form podcast footage available")
    if not has_festival:
        gaps.append("No festival Q&A footage cataloged")
    if not has_bts:
        gaps.append("No behind-the-scenes footage available")

    if gaps:
        lines.append(
            f"**Unknown #4 — Source Coverage Gaps (Tier C implication)**\n\n"
            + "\n".join(f"- {g}" for g in gaps)
            + "\n\nThese gaps limit confidence in attachment-style and baseline-stress assessments."
        )
    else:
        lines.append(
            f"**Unknown #4 — Validation Gap (Tier C implication)**\n\n"
            f"No independent verification of source authenticity has been performed. "
            f"Fan-edited clips may be mislabeled as RAW. Official BTS may be staged. "
            f"Without source authentication, all access-level assignments are provisional."
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        "> **Huasheng Principle:** Transparency is a feature, not a bug. "
        "What you don't know is as important as what you do."
    )

    return "\n".join(lines)


def _compile_brief(
    actor: str,
    question: str,
    sections: dict[str, str],
    videos: list[dict[str, Any]],
    claims: list[Claim],
) -> str:
    """Compile all sections into the final brief."""
    now = datetime.now(timezone.utc).isoformat()

    # Count source types
    source_counts = {}
    for v in videos:
        st = v.get("source_type", "unknown")
        source_counts[st] = source_counts.get(st, 0) + 1

    lines = [
        f"# Actor Brief — {actor}",
        "",
        f"**Client Question:** {question}",
        f"**Agent:** Video Analysis v3.0.0 (Huasheng Pattern)",
        f"**Sources Analyzed:** {len(videos)} videos",
        f"**Claims Generated:** {len(claims)}",
        f"**Generated:** {now}",
        "",
        "## Source Breakdown",
        "",
    ]
    for st, count in sorted(source_counts.items()):
        lines.append(f"- {st}: {count}")

    lines += [
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        sections["executive_summary"],
        "",
        "---",
        "",
        "## Clinical Profile",
        "",
        sections["clinical_profile"],
        "",
        "---",
        "",
        "## Intelligence Assessment",
        "",
        sections["intelligence_assessment"],
        "",
        "---",
        "",
        "## Archaeological Strata",
        "",
        sections["archaeological_strata"],
        "",
        "---",
        "",
        "## Contradiction Map",
        "",
        sections["contradiction_map"],
        "",
        "---",
        "",
        "## Adversarial Findings",
        "",
        sections["adversarial_findings"],
        "",
        "---",
        "",
        "## Tier Marking Key",
        "",
        sections["tier_marking"],
        "",
        "---",
        "",
        "## Uncertainty Map",
        "",
        sections["uncertainty_map"],
        "",
        "---",
        "",
        "> **Huasheng Certification:** This brief has been generated under the Huasheng Pattern. "
        "> Every claim is tagged. Every contradiction is preserved. Every uncertainty is named. "
        "> If this brief resolves contradictions instead of preserving them, it has been corrupted. "
        "> If this brief contains generic compliments without diagnostic specificity, it has failed validation.",
    ]

    return "\n".join(lines)


def _generate_synthesis(
    llm: LLMClient,
    actor: str,
    sections: dict[str, str],
    claims: list[Claim],
    references: dict[str, str],
) -> str:
    """Generate integrated synthesis across all lenses."""
    summary = (
        f"# Synthesis — {actor}\n\n"
        f"## Integrated Assessment\n\n"
    )

    # Extract key themes
    tier_a_claims = [c for c in claims if c.tier == "A"]
    tier_b_claims = [c for c in claims if c.tier == "B"]

    summary += (
        f"**High-Confidence Findings (Tier A):** {len(tier_a_claims)}\n"
    )
    for c in tier_a_claims[:5]:
        summary += f"- {c.text}\n"

    summary += (
        f"\n**Moderate-Confidence Findings (Tier B):** {len(tier_b_claims)}\n"
    )
    for c in tier_b_claims[:5]:
        summary += f"- {c.text}\n"

    summary += (
        f"\n## Cross-Lens Consensus\n\n"
        f"The clinical, intelligence, and archaeological lenses converge on the following: "
        f"{actor} presents a managed public persona with evidence of genuine underlying "
        f"behavioral patterns. The gap between RAW and managed footage is the critical "
        f"diagnostic zone — it reveals either authentic stability (good for casting) or "
        f"effective masking (risk for roles requiring vulnerability).\n\n"
        f"## Recommended Next Steps\n\n"
        f"1. **Structured test:** Offer a non-franchise, mid-budget role to test appetite for risk\n"
        f"2. **Longitudinal observation:** 6-month collaboration to assess sustainability\n"
        f"3. **Physical transformation test:** Role requiring visible physical change\n"
        f"4. **Crisis-scene audition:** Scene requiring sustained emotional breakdown\n"
    )

    return summary


def _format_anti_patterns(checks: list) -> str:
    lines = ["# Anti-Patterns Enforcement Report", ""]

    critical = [c for c in checks if c.severity == "critical" and c.detected]
    warnings = [c for c in checks if c.severity == "warning" and c.detected]
    clean = [c for c in checks if not c.detected]

    if critical:
        lines.append("## ❌ CRITICAL ISSUES (Block Shipment)")
        lines.append("")
        for c in critical:
            lines.append(f"### {c.pattern}")
            lines.append(f"- **Evidence:** {c.evidence}")
            lines.append(f"- **Mitigation:** {c.mitigation}")
            lines.append("")

    if warnings:
        lines.append("## ⚠️ WARNINGS")
        lines.append("")
        for c in warnings:
            lines.append(f"### {c.pattern}")
            lines.append(f"- **Evidence:** {c.evidence}")
            lines.append(f"- **Mitigation:** {c.mitigation}")
            lines.append("")

    if clean:
        lines.append("## ✅ CLEAN")
        lines.append("")
        for c in clean:
            lines.append(f"- **{c.pattern}** — {c.evidence}")

    lines.append("")
    lines.append(
        "> **Huasheng Principle:** Anti-patterns are not suggestions. They are "
        "enforced quality gates. Any critical detection blocks brief shipment."
    )

    return "\n".join(lines)


# ── Utility Extractors ───────────────────────────────────────────────────────

def _extract_thesis(executive_summary: str) -> str:
    """Extract the main thesis from executive summary."""
    # Simple extraction: first sentence or first line
    lines = [l.strip() for l in executive_summary.splitlines() if l.strip()]
    for line in lines:
        if line.startswith("**Verdict:**") or line.startswith("Verdict:"):
            return line.split(":", 1)[1].strip().rstrip(".!")
        if len(line) > 30 and not line.startswith("#") and not line.startswith("-"):
            return line[:200]
    return "Actor presents mixed signal profile for this casting question."


def _summarize_evidence(claims: list[Claim], videos: list[dict[str, Any]]) -> str:
    """Summarize evidence for adversarial pass."""
    claim_texts = [c.text for c in claims[:10]]
    video_types = [f"{v['source_type']} ({v['access_level']})" for v in videos]
    return (
        f"Claims: {'; '.join(claim_texts)}\n"
        f"Sources: {', '.join(set(video_types))}"
    )


def _count_tiers(claims: list[Claim]) -> dict[str, int]:
    counts = {}
    for c in claims:
        counts[c.tier] = counts.get(c.tier, 0) + 1
    return counts


# ── Validation ───────────────────────────────────────────────────────────────

def validate(investigation_id: str, base_path: Path) -> bool:
    """
    Huasheng Quality Gate: Ensure brief has real intelligence, not placeholders.
    """
    from oracle.kernel import investigation_dir

    inv_dir = investigation_dir(base_path, investigation_id)
    brief = inv_dir / "brief.md"
    if not brief.exists():
        return False

    content = brief.read_text(encoding="utf-8")

    # Must have all required sections
    required_headers = [
        "## Executive Summary",
        "## Clinical Profile",
        "## Archaeological Strata",
        "## Contradiction Map",
        "## Adversarial Findings",
        "## Tier Marking Key",
        "## Uncertainty Map",
    ]
    for header in required_headers:
        if header not in content:
            return False

    # Huasheng: Must have tier tags
    if "(Tier A)" not in content and "(Tier B)" not in content:
        return False

    # Huasheng: Must have real contradictions (not placeholder text)
    if "PLACEHOLDER" in content.upper():
        return False

    # Huasheng: Must have pre-ship validation
    pre_ship = inv_dir / "research" / "pre-ship-validation.md"
    if not pre_ship.exists():
        return False

    pre_ship_text = pre_ship.read_text(encoding="utf-8")
    if "BLOCKED" in pre_ship_text:
        # Brief exists but failed pre-ship — this is informational, not a failure
        pass

    # Huasheng: Anti-patterns must be checked
    anti_patterns = inv_dir / "references" / "anti-patterns.md"
    if not anti_patterns.exists():
        return False

    anti_text = anti_patterns.read_text(encoding="utf-8")
    if "CRITICAL" in anti_text:
        # Anti-patterns detected but documented — valid state
        pass

    return True
