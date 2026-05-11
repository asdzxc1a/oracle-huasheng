"""
Comparable Mapper Agent v1.0

Finds comparable actors with similar trajectories and maps their outcomes
to inform probability assessment. Use when a producer needs to understand
how similar actors performed in comparable situations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from oracle.kernel import (
    LLMClient,
    Claim,
    apply_tier_marking,
    detect_contradictions,
    run_adversarial_pass,
    enforce_anti_patterns,
    PreShipValidator,
    format_contradiction_map,
    format_adversarial_findings,
    format_tier_marking,
    format_anti_patterns,
    extract_thesis,
    summarize_evidence,
    count_tiers,
)

name = "comparable_mapper"
version = "1.0.0"


def run(investigation_id: str, instructions: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Execute the Comparable Mapper."""
    actors = instructions.get("actors", [])
    if len(actors) != 2:
        actors = context.get("actor", "Unknown").split(" vs ")
    actor_a = actors[0] if len(actors) > 0 else "Unknown"
    actor_b = actors[1] if len(actors) > 1 else "Unknown"
    question = instructions.get("question", context.get("client_question", ""))
    inv_dir = Path(context["investigation_dir"])

    llm = LLMClient()

    # Load actor profiles if available
    store = context.get("context_store")
    profile_a = store.load_actor(actor_a) if store else {}
    profile_b = store.load_actor(actor_b) if store else {}

    # Generate comparative analysis
    comparison = _generate_comparison(llm, actor_a, actor_b, question, profile_a, profile_b)

    # Generate claims for Huasheng enforcement
    claims = _generate_comparison_claims(llm, actor_a, actor_b, comparison)
    claims = apply_tier_marking(claims)

    # Huasheng enforcement
    contradictions = detect_contradictions(llm, claims, f"{actor_a} vs {actor_b}", min_pairs=2)
    main_thesis = extract_thesis(comparison)
    evidence_summary = summarize_evidence(claims, [])
    adversarial = run_adversarial_pass(llm, main_thesis, evidence_summary, f"{actor_a} vs {actor_b}")
    anti_pattern_checks = enforce_anti_patterns(llm, comparison, claims, f"{actor_a} vs {actor_b}")

    # Pre-ship validation
    validator = PreShipValidator()
    pre_ship = validator.validate(comparison, contradictions, adversarial, anti_pattern_checks, claims)

    # Write outputs
    brief_path = inv_dir / "brief.md"
    brief_path.write_text(comparison, encoding="utf-8")

    (inv_dir / "research" / "comparison.md").write_text(comparison, encoding="utf-8")
    (inv_dir / "research" / "contradiction_map.md").write_text(format_contradiction_map(contradictions), encoding="utf-8")
    (inv_dir / "research" / "adversarial_findings.md").write_text(format_adversarial_findings(adversarial), encoding="utf-8")
    (inv_dir / "research" / "tier_marking.md").write_text(format_tier_marking(claims), encoding="utf-8")
    (inv_dir / "research" / "pre-ship-validation.md").write_text(validator.to_markdown(pre_ship), encoding="utf-8")
    (inv_dir / "references" / "anti-patterns.md").write_text(format_anti_patterns(anti_pattern_checks), encoding="utf-8")

    return {
        "actor_a": actor_a,
        "actor_b": actor_b,
        "brief_path": str(brief_path),
        "claims_generated": len(claims),
        "contradictions_preserved": len(contradictions),
        "adversarial_findings": len(adversarial),
        "pre_ship_passed": pre_ship.passed,
        "pre_ship_score": pre_ship.score,
    }


def _generate_comparison(
    llm: LLMClient,
    actor_a: str,
    actor_b: str,
    question: str,
    profile_a: dict[str, Any],
    profile_b: dict[str, Any],
) -> str:
    """Generate comparative analysis brief."""
    if not llm.is_available():
        return _generate_comparison_fallback(actor_a, actor_b, question, profile_a, profile_b)

    schema = {
        "type": "object",
        "properties": {
            "comparison": {
                "type": "object",
                "properties": {
                    "verdict": {"type": "string"},
                    "actor_a_strengths": {"type": "array", "items": {"type": "string"}},
                    "actor_b_strengths": {"type": "array", "items": {"type": "string"}},
                    "actor_a_risks": {"type": "array", "items": {"type": "string"}},
                    "actor_b_risks": {"type": "array", "items": {"type": "string"}},
                    "comparable_historical_cases": {"type": "array", "items": {"type": "string"}},
                    "recommendation": {"type": "string"},
                },
                "required": ["verdict", "recommendation"],
            }
        },
        "required": ["comparison"],
    }

    filmo_a = json.dumps(profile_a.get("filmography", [])[:5], indent=2)
    filmo_b = json.dumps(profile_b.get("filmography", [])[:5], indent=2)

    prompt = (
        f"Compare actors '{actor_a}' and '{actor_b}' for this casting question:\n"
        f"{question}\n\n"
        f"{actor_a} FILMOGRAPHY:\n{filmo_a}\n\n"
        f"{actor_b} FILMOGRAPHY:\n{filmo_b}\n\n"
        f"Generate a structured comparison with verdict, strengths/risks for each, "
        f"historical comparable cases, and a clear recommendation."
    )

    system = (
        "You are a casting intelligence analyst. You compare actors objectively, "
        "using specific evidence. Never say 'both are talented' — say which is better "
        "for THIS specific question and why."
    )

    try:
        result = llm.generate_structured(prompt, schema, system, max_tokens=3000)
        comp = result.get("comparison", {})
        return _format_comparison_brief(actor_a, actor_b, comp)
    except Exception:
        return _generate_comparison_fallback(actor_a, actor_b, question, profile_a, profile_b)


def _format_comparison_brief(actor_a: str, actor_b: str, comp: dict[str, Any]) -> str:
    lines = [
        f"# Comparative Analysis — {actor_a} vs {actor_b}",
        "",
        f"**Question:** {comp.get('verdict', 'Comparison assessment')}",
        "",
        "## Verdict",
        "",
        comp.get("verdict", "No verdict generated."),
        "",
        f"## {actor_a} — Strengths",
        "",
    ]
    for s in comp.get("actor_a_strengths", []):
        lines.append(f"- {s}")
    lines += ["", f"## {actor_b} — Strengths", ""]
    for s in comp.get("actor_b_strengths", []):
        lines.append(f"- {s}")
    lines += ["", f"## {actor_a} — Risks", ""]
    for r in comp.get("actor_a_risks", []):
        lines.append(f"- {r}")
    lines += ["", f"## {actor_b} — Risks", ""]
    for r in comp.get("actor_b_risks", []):
        lines.append(f"- {r}")
    lines += ["", "## Historical Comparables", ""]
    for c in comp.get("comparable_historical_cases", []):
        lines.append(f"- {c}")
    lines += ["", "## Recommendation", "", comp.get("recommendation", "No recommendation.")]
    return "\n".join(lines)


def _generate_comparison_fallback(
    actor_a: str,
    actor_b: str,
    question: str,
    profile_a: dict[str, Any],
    profile_b: dict[str, Any],
) -> str:
    """Generate comparison without LLM."""
    stage_a = profile_a.get("career_stage", "unknown")
    stage_b = profile_b.get("career_stage", "unknown")

    return (
        f"# Comparative Analysis — {actor_a} vs {actor_b}\n\n"
        f"**Question:** {question}\n\n"
        f"## Verdict\n\n"
        f"Both actors present viable profiles for this question. {actor_a} is at the "
        f"'{stage_a}' career stage; {actor_b} is at '{stage_b}'. "
        f"Without deeper source analysis, a definitive recommendation is premature. (Tier C)\n\n"
        f"## Recommendation\n\n"
        f"Run full /assess commands on both actors individually, then compare the "
        f"resulting briefs. The comparable mapper works best when both actors have "
        f"completed video analysis pipelines."
    )


def _generate_comparison_claims(
    llm: LLMClient,
    actor_a: str,
    actor_b: str,
    comparison_text: str,
) -> list[Claim]:
    """Generate claims from comparison text."""
    claims = []
    if "strength" in comparison_text.lower():
        claims.append(Claim(
            text=f"{actor_a} and {actor_b} both have identifiable strengths for this casting question",
            source_type="comparison_analysis",
            access_level="MANAGED",
            tier="B",
            confidence=0.6,
        ))
    if "risk" in comparison_text.lower():
        claims.append(Claim(
            text=f"Both actors carry identifiable risks that should be tested before commitment",
            source_type="comparison_analysis",
            access_level="MANAGED",
            tier="B",
            confidence=0.6,
        ))
    claims.append(Claim(
        text=f"Comparative analysis without individual deep-dive has limited diagnostic value",
        source_type="methodology",
        access_level="MANAGED",
        tier="C",
        confidence=0.5,
    ))
    return claims


def validate(investigation_id: str, base_path: Path) -> bool:
    """Quality gate for comparison output."""
    from oracle.kernel import investigation_dir

    inv_dir = investigation_dir(base_path, investigation_id)
    brief = inv_dir / "brief.md"
    if not brief.exists():
        return False

    content = brief.read_text(encoding="utf-8")
    if "Verdict" not in content or "Recommendation" not in content:
        return False
    if "PLACEHOLDER" in content.upper():
        return False

    return True
