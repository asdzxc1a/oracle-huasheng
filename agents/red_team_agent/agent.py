"""
Red Team Agent — Adversarial audit of the Psychological Profiler's conclusions.

Reads: psychological_profile.json, brief.md
Produces: adversarial_audit.json with challenges, counter-evidence, revised confidence.
"""

from __future__ import annotations

name = "red_team_agent"
version = "1.0.0"

import json
import re
from pathlib import Path
from typing import Any


def _format_profile_for_prompt(profile: dict[str, Any]) -> str:
    lines: list[str] = []
    dims = profile.get("dimensions", {})
    for dim_name, dim_data in dims.items():
        if isinstance(dim_data, dict):
            lines.append(f"{dim_name}: score={dim_data.get('score', 'N/A')}, desc={dim_data.get('description', '')}")
        else:
            lines.append(f"{dim_name}: score={dim_data}")
    preds = profile.get("context_predictions", [])
    if preds:
        lines.append("\nPredictions:")
        for p in preds:
            lines.append(
                f"  - {p.get('context')}: stress={p.get('stress_level')}, "
                f"confidence={p.get('confidence')}, risk={p.get('risk_level')}, "
                f"prediction={p.get('prediction', '')[:100]}"
            )
    return "\n".join(lines)


async def run(
    investigation_id: str,
    instructions: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """Run adversarial audit on the psychological profiler output."""
    actor = context.get("actor", "Unknown")
    inv_dir = Path(context["investigation_dir"])
    
    profile_path = inv_dir / "psychological_profile.json"
    profile: dict[str, Any] = {}
    if profile_path.exists():
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    
    brief_path = inv_dir / "brief.md"
    brief_text = brief_path.read_text(encoding="utf-8") if brief_path.exists() else ""
    
    llm = context.get("llm_client")
    
    prompt = f"""You are a red-team adversary auditing a psychological profile of actor {actor}.

PROFILE TO AUDIT:
{_format_profile_for_prompt(profile)}

ORIGINAL BRIEF SNIPPETS:
{brief_text[:3000]}

YOUR TASK: Find flaws in the profiler's reasoning. You must identify at least 3 weaknesses:

1. **Overconfidence** — Where did the profiler claim certainty without evidence?
2. **Selection Bias** — What data was ignored or cherry-picked?
3. **Context Gaps** — What real-world contexts weren't considered?

For each challenge:
- State the exact profiler claim you're challenging
- Provide counter-evidence or counter-argument
- Rate how damaging this challenge is (1-10)
- State what additional evidence would resolve it

Also provide:
- A revised overall risk assessment (more conservative)
- A list of 3 additional scenarios that should be tested before production

Respond in strict JSON:
{{
  "challenges": [
    {{
      "profiler_claim": str,
      "flaw_type": str,
      "counter_argument": str,
      "severity": int,
      "needed_evidence": str
    }}
  ],
  "revised_risk_assessment": str,
  "additional_test_scenarios": [str],
  "overall_adversarial_score": int
}}
"""
    
    audit: dict[str, Any] = {
        "challenges": [],
        "revised_risk_assessment": "No audit performed.",
        "additional_test_scenarios": [],
        "overall_adversarial_score": 5,
    }
    
    if llm and llm.is_available():
        try:
            response = llm.generate_structured(prompt, schema=None)
            text = response if isinstance(response, str) else str(response)
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                audit = json.loads(match.group())
            else:
                audit = json.loads(text)
        except Exception as e:
            print(f"[RedTeam] LLM failed: {e}")
    
    # Ensure minimum challenges
    if not audit.get("challenges"):
        audit["challenges"] = [
            {
                "profiler_claim": "Overall profile confidence",
                "flaw_type": "Insufficient sample size",
                "counter_argument": "Profile based on limited video data; no longitudinal assessment",
                "severity": 7,
                "needed_evidence": "Minimum 10+ hours of footage across diverse contexts"
            },
            {
                "profiler_claim": "Context predictions",
                "flaw_type": "Extrapolation beyond data",
                "counter_argument": "Predictions for unseen contexts are speculative",
                "severity": 8,
                "needed_evidence": "Direct observation in predicted contexts"
            },
            {
                "profiler_claim": "Dimension scores",
                "flaw_type": "Observer bias",
                "counter_argument": "Scores may reflect analyst bias rather than actor behavior",
                "severity": 6,
                "needed_evidence": "Multiple independent raters"
            },
        ]
    
    if "revised_risk_assessment" not in audit:
        audit["revised_risk_assessment"] = "High uncertainty due to limited data."
    if "additional_test_scenarios" not in audit or not audit["additional_test_scenarios"]:
        audit["additional_test_scenarios"] = [
            "Live unscripted Q&A under time pressure",
            "Collaborative rehearsal with difficult co-star",
            "Social media crisis response simulation",
        ]
    if "overall_adversarial_score" not in audit:
        audit["overall_adversarial_score"] = 5
    
    audit_path = inv_dir / "adversarial_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    
    return {
        "success": True,
        "audit_path": str(audit_path),
        "challenges_count": len(audit["challenges"]),
        "adversarial_score": audit["overall_adversarial_score"],
    }
