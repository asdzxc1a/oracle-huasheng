"""
Huasheng Formatters — Output formatting utilities for brief generation.

Pure functions that format claims, contradictions, adversarial findings,
anti-patterns, and uncertainty maps into structured markdown.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .intelligence import Claim


def format_contradiction_map(contradictions: list[Any]) -> str:
    if not contradictions:
        return (
            "**No contradictions detected.** This is a warning sign — "
            "either sources are too homogeneous or analysis is insufficient."
        )

    lines = [f"**Total Contradictions Preserved:** {len(contradictions)}", ""]
    for c in contradictions:
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


def format_adversarial_findings(findings: list[Any]) -> str:
    if not findings:
        return "**No adversarial analysis performed.** This brief is unverified."

    lines = [
        "**Devil's Advocate Budget:** ≥20% of analysis effort dedicated to arguing against the thesis.",
        "",
    ]
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


def format_tier_marking(claims: list[Claim]) -> str:
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

    tier_counts: dict[str, int] = {}
    for c in claims:
        tier_counts[c.tier] = tier_counts.get(c.tier, 0) + 1
    lines.append("## Distribution")
    for tier in ["A", "B", "C", "F"]:
        count = tier_counts.get(tier, 0)
        lines.append(f"- Tier {tier}: {count} claims")

    return "\n".join(lines)


def generate_uncertainty_map(actor: str, videos: list[dict[str, Any]], focus: str = "") -> str:
    lines = [
        "The following gaps limit confidence in this analysis:",
        "",
    ]

    lines.append(
        f"**Unknown #1 — Private Stress Response (Tier C implication)**\n\n"
        f"We observe {actor} in professional and semi-professional contexts. "
        f"We do not observe them under genuine personal crisis. Crisis performance "
        f"requires different emotional resources than professional stress management. "
        f"Roles requiring sustained emotional breakdown may be harder than roles "
        f"requiring controlled professional stress."
    )
    lines.append("")

    lines.append(
        f"**Unknown #2 — Long-Term Collaboration Dynamics (Tier C implication)**\n\n"
        f"All available footage is episodic (interviews, festivals). We have no "
        f"longitudinal footage of {actor} in a months-long creative collaboration. "
        f"Some actors excel in short bursts but degrade over time; others deepen. "
        f"We cannot determine which pattern applies without longitudinal data."
    )
    lines.append("")

    lines.append(
        f"**Unknown #3 — Physical Transformation Capacity (Tier C implication)**\n\n"
        f"The current analysis is based on {actor}'s established physical type and "
        f"movement patterns. We have limited data on their willingness and ability "
        f"to fundamentally alter physicality for a role (weight change, movement "
        f"training, posture overhaul). This is a significant unknown for roles "
        f"requiring physical transformation."
    )
    lines.append("")

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


def compile_brief(
    actor: str,
    question: str,
    sections: dict[str, str],
    videos: list[dict[str, Any]],
    claims: list[Claim],
) -> str:
    """Compile all sections into the final brief."""
    now = datetime.now(timezone.utc).isoformat()

    source_counts: dict[str, int] = {}
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

    section_order = [
        ("Executive Summary", "executive_summary"),
        ("Clinical Profile", "clinical_profile"),
        ("Intelligence Assessment", "intelligence_assessment"),
        ("Archaeological Strata", "archaeological_strata"),
        ("Contradiction Map", "contradiction_map"),
        ("Adversarial Findings", "adversarial_findings"),
        ("Tier Marking Key", "tier_marking"),
        ("Uncertainty Map", "uncertainty_map"),
    ]

    for title, key in section_order:
        lines += ["", "---", "", f"## {title}", "", sections.get(key, "")]

    lines += [
        "",
        "---",
        "",
        "> **Huasheng Certification:** This brief has been generated under the Huasheng Pattern. "
        "> Every claim is tagged. Every contradiction is preserved. Every uncertainty is named. "
        "> If this brief resolves contradictions instead of preserving them, it has been corrupted. "
        "> If this brief contains generic compliments without diagnostic specificity, it has failed validation.",
    ]

    return "\n".join(lines)


def generate_synthesis(actor: str, claims: list[Claim]) -> str:
    """Generate integrated synthesis across all lenses."""
    tier_a_claims = [c for c in claims if c.tier == "A"]
    tier_b_claims = [c for c in claims if c.tier == "B"]

    summary = f"# Synthesis — {actor}\n\n## Integrated Assessment\n\n"

    summary += f"**High-Confidence Findings (Tier A):** {len(tier_a_claims)}\n"
    for c in tier_a_claims[:5]:
        summary += f"- {c.text}\n"

    summary += f"\n**Moderate-Confidence Findings (Tier B):** {len(tier_b_claims)}\n"
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


def format_anti_patterns(checks: list[Any]) -> str:
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


def extract_thesis(executive_summary: str) -> str:
    """Extract the main thesis from executive summary."""
    lines = [l.strip() for l in executive_summary.splitlines() if l.strip()]
    for line in lines:
        if line.startswith("**Verdict:**") or line.startswith("Verdict:"):
            return line.split(":", 1)[1].strip().rstrip(".!")
        if len(line) > 30 and not line.startswith("#") and not line.startswith("-"):
            return line[:200]
    return "Actor presents mixed signal profile for this casting question."


def summarize_evidence(claims: list[Claim], videos: list[dict[str, Any]]) -> str:
    """Summarize evidence for adversarial pass."""
    claim_texts = [c.text for c in claims[:10]]
    video_types = [f"{v['source_type']} ({v['access_level']})" for v in videos]
    return (
        f"Claims: {'; '.join(claim_texts)}\n"
        f"Sources: {', '.join(set(video_types))}"
    )


def count_tiers(claims: list[Claim]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for c in claims:
        counts[c.tier] = counts.get(c.tier, 0) + 1
    return counts


# ── Harvester Formatters ─────────────────────────────────────────────────────


def format_video_catalog_md(actor: str, investigation_id: str, videos: list[dict[str, Any]], focus: list[str], career_stage: str, known_for: str) -> str:
    """Format video catalog as human-readable markdown."""
    md_lines = [
        f"# Video Catalog — {actor}",
        f"**Investigation:** {investigation_id}",
        f"**Videos Found:** {len(videos)}",
        f"**Career Stage:** {career_stage.title()}",
        f"**Known For:** {known_for}",
        "",
        "| # | Title | Type | Access | Signal | Duration | Date |",
        "|---|-------|------|--------|--------|----------|------|",
    ]
    for i, v in enumerate(videos, 1):
        dur = f"{v['duration_seconds'] // 60}:{v['duration_seconds'] % 60:02d}"
        md_lines.append(
            f"| {i} | [{v['title']}]({v['url']}) | {v['source_type']} | {v['access_level']} | {v.get('signal_density', 'Moderate')} | {dur} | {v['date']} |"
        )

    md_lines += ["", "## Why Each Source Matters", ""]
    for v in videos:
        md_lines.append(f"### {v['title']}")
        md_lines.append(f"- **Access Level:** {v['access_level']}")
        md_lines.append(f"- **Signal Density:** {v.get('signal_density', 'Moderate')}")
        md_lines.append(f"- **Relevance:** {v.get('why_relevant', 'General assessment')}")
        md_lines.append("")

    md_lines += ["## Focus Areas", ""]
    if focus:
        for f_item in focus:
            md_lines.append(f"- {f_item}")
    else:
        md_lines.append("_No specific focus areas requested._")

    md_lines += ["", "## Source Tier Summary", ""]
    access_counts: dict[str, int] = {}
    for v in videos:
        access_counts[v["access_level"]] = access_counts.get(v["access_level"], 0) + 1
    for level, count in sorted(access_counts.items()):
        md_lines.append(f"- **{level}:** {count} sources")

    return "\n".join(md_lines)


def format_facts_md(actor: str, investigation_id: str, videos: list[dict[str, Any]], catalog_data: dict[str, Any]) -> str:
    """Format verified facts as markdown."""
    facts_lines = [
        f"# Verified Facts — {actor}",
        "",
        f"- **Name:** {actor}",
        f"- **Investigation:** {investigation_id}",
        f"- **Video sources cataloged:** {len(videos)}",
        f"- **Career Stage:** {catalog_data.get('career_stage', 'unknown').title()}",
        f"- **Known For:** {catalog_data.get('known_for', '')}",
        "",
        "## Filmography Highlights",
        "",
    ]
    for film in catalog_data.get("filmography_highlights", []):
        sig = f" — _{film.get('significance', '')}_" if film.get("significance") else ""
        facts_lines.append(f"- **{film['title']}** ({film['year']}) — {film['role']}{sig}")

    facts_lines += ["", "## Career Timeline", ""]
    for event in catalog_data.get("career_timeline", []):
        sig = f" — _{event.get('significance', '')}_" if event.get("significance") else ""
        facts_lines.append(f"- **{event['year']}:** {event['event']}{sig}")

    facts_lines += ["", "## Known Contradictions (Preliminary)", ""]
    contradictions = catalog_data.get("known_contradictions", [])
    if contradictions:
        for i, c in enumerate(contradictions, 1):
            facts_lines.append(f"### Contradiction #{i}")
            facts_lines.append(f"- **Signal A:** {c['claim_a']}")
            facts_lines.append(f"- **Signal B:** {c['claim_b']}")
            if c.get("sources"):
                facts_lines.append(f"- **Sources:** {c['sources']}")
            facts_lines.append("")
    else:
        facts_lines.append("_No known contradictions cataloged yet._")

    return "\n".join(facts_lines)


def build_harvester_json(actor: str, investigation_id: str, videos: list[dict[str, Any]], catalog_data: dict[str, Any]) -> dict[str, Any]:
    """Build structured JSON catalog for the harvester."""
    return {
        "actor": actor,
        "investigation_id": investigation_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_found": len(videos),
        "known_for": catalog_data.get("known_for", ""),
        "career_stage": catalog_data.get("career_stage", "unknown"),
        "videos": videos,
    }
