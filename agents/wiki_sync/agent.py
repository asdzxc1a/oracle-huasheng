"""
Wiki Sync Agent — Generates and updates actor wiki pages.

Reads: brief.md, knowledge_graph.json, psychological_profile.json
Produces: wiki/<actor-slug>.md  (editable by producers)
"""

from __future__ import annotations

name = "wiki_sync"
version = "1.0.0"

import json
from pathlib import Path
from typing import Any


def _format_claim_section(claims: list[dict[str, Any]]) -> str:
    lines = ["## Claim Inventory\n"]
    for claim in claims:
        tier = claim.get("tier", "C")
        text = claim.get("text", "").strip()
        if not text:
            continue
        tier_color = {"A": "🔴", "B": "🟡", "C": "🟢"}.get(tier, "⚪")
        lines.append(f"- {tier_color} **Tier {tier}:** {text}\n")
    return "\n".join(lines)


def _format_contradiction_section(contradictions: list[dict[str, Any]]) -> str:
    lines = ["## Contradiction Network\n"]
    if not contradictions:
        lines.append("*No contradictions detected.*\n")
        return "\n".join(lines)
    for i, c in enumerate(contradictions):
        lines.append(f"### Contradiction {i+1}\n")
        lines.append(f"- **Signal A:** {c.get('claim_a', '')}\n")
        lines.append(f"- **Signal B:** {c.get('claim_b', '')}\n")
        lines.append(f"- **Tension:** {c.get('tension', '')}\n")
        lines.append(f"- **Implication:** {c.get('implication', '')}\n")
    return "\n".join(lines)


def _format_psych_profile(profile: dict[str, Any]) -> str:
    if not profile:
        return "## Psychological Profile\n\n*No psychological profile available.*\n"
    lines = ["## Psychological Profile\n"]
    
    # Dimension scores
    dims = profile.get("dimensions", {})
    if dims:
        lines.append("### Dimensions\n")
        for dim_name, dim_data in dims.items():
            score = dim_data.get("score", "N/A") if isinstance(dim_data, dict) else dim_data
            desc = dim_data.get("description", "") if isinstance(dim_data, dict) else ""
            lines.append(f"- **{dim_name.replace('_', ' ').title()}:** {score}/10")
            if desc:
                lines.append(f" — {desc}")
            lines.append("\n")
    
    # Risk assessment
    risk = profile.get("overall_risk_assessment", "")
    if risk:
        lines.append(f"\n### Overall Risk Assessment\n\n{risk}\n")
    
    # Red flags
    flags = profile.get("red_flags", [])
    if flags:
        lines.append("\n### Red Flags\n")
        for flag in flags:
            lines.append(f"- 🚩 {flag}\n")
    
    # Recommendations
    recs = profile.get("producer_recommendations", [])
    if recs:
        lines.append("\n### Producer Recommendations\n")
        for rec in recs:
            lines.append(f"- ✅ {rec}\n")
    
    # Context predictions
    predictions = profile.get("context_predictions", [])
    if predictions:
        lines.append("\n### Contextual Behavior Predictions\n")
        lines.append("| Context | Stress Level | Confidence | Risk |\n")
        lines.append("|---|---|---|---|\n")
        for pred in predictions:
            lines.append(
                f"| {pred.get('context', '')} | "
                f"{pred.get('stress_level', 'N/A')} | "
                f"{pred.get('confidence', 'N/A')} | "
                f"{pred.get('risk_level', 'N/A')} |\n"
            )
    return "\n".join(lines)


def _format_sources(sources: list[dict[str, Any]]) -> str:
    lines = ["## Source Inventory\n"]
    lines.append("| Title | Type | Access | URL |\n")
    lines.append("|---|---|---|---|\n")
    for src in sources:
        title = src.get("title", "Unknown")[:50]
        stype = src.get("source_type", "unknown")
        access = src.get("access_level", "MANAGED")
        url = src.get("url", "")
        lines.append(f"| {title} | {stype} | {access} | [Link]({url}) |\n")
    return "\n".join(lines)


def run(
    investigation_id: str,
    instructions: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """Generate or update an actor wiki page."""
    actor = context.get("actor", "Unknown")
    inv_dir = Path(context["investigation_dir"])
    wiki_dir = Path(context.get("wiki_dir", str(Path(__file__).parent.parent.parent / "wiki")))
    wiki_dir.mkdir(parents=True, exist_ok=True)
    
    actor_slug = actor.lower().replace(" ", "-")
    wiki_path = wiki_dir / f"{actor_slug}.md"
    
    brief_path = inv_dir / "brief.md"
    brief_text = brief_path.read_text(encoding="utf-8") if brief_path.exists() else ""
    
    kg_path = inv_dir / "knowledge_graph.json"
    graph = {"claims": [], "contradictions": [], "sources": []}
    if kg_path.exists():
        graph = json.loads(kg_path.read_text(encoding="utf-8"))
    
    profile_path = inv_dir / "psychological_profile.json"
    profile = {}
    if profile_path.exists():
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    
    thesis = ""
    for line in brief_text.split("\n")[:30]:
        if line.startswith("**Thesis:**"):
            thesis = line.replace("**Thesis:**", "").strip()
            break
    
    lines = [
        f"# {actor}\n",
        f"> Last updated: investigation `{investigation_id}`\n",
        f"> **Thesis:** {thesis}\n",
        "\n---\n",
        _format_claim_section(graph.get("claims", [])),
        "\n---\n",
        _format_contradiction_section(graph.get("contradictions", [])),
        "\n---\n",
        _format_psych_profile(profile),
        "\n---\n",
        _format_sources(graph.get("sources", [])),
        "\n---\n",
        "## Producer Notes\n",
        "*Add notes here for production team...*\n",
        "\n---\n",
        f"## Raw Data\n",
        f"- [Brief]({inv_dir}/brief.md)\n",
        f"- [Knowledge Graph]({inv_dir}/knowledge_graph.json)\n",
        f"- [Psych Profile]({inv_dir}/psychological_profile.json)\n",
    ]
    
    wiki_path.write_text("\n".join(lines), encoding="utf-8")
    
    return {
        "success": True,
        "wiki_path": str(wiki_path),
        "actor_slug": actor_slug,
    }
