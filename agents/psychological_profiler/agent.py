"""
Deep Psychological Profiler Agent.

Reads: brief.md, video-analysis observations, contradiction network
Produces: psychological_profile.json with 5-dimension scoring + contextual predictions.
"""

from __future__ import annotations

name = "psychological_profiler"
version = "1.0.0"

import json
import re
from pathlib import Path
from typing import Any


PROFILE_SCHEMA: dict[str, Any] = {
    "stress_response": {
        "low_score": "Disassociates or numbs under pressure; flat affect",
        "mid_score": "Controlled response; situational adaptation",
        "high_score": "Escalates tension; visible anxiety or defensiveness",
    },
    "attachment_style": {
        "low_score": "Dismissive-avoidant; avoids emotional intimacy",
        "mid_score": "Balanced; healthy boundaries",
        "high_score": "Anxious-preoccupied; seeks external validation",
    },
    "narcissistic_defense": {
        "low_score": "No defense; genuine humility",
        "mid_score": "Occasional self-protection; mild grandiosity",
        "high_score": "Strong defensive walls; fragile ego",
    },
    "temporal_stability": {
        "low_score": "Inconsistent; depends heavily on environment",
        "mid_score": "Moderate; some fluctuation across contexts",
        "high_score": "Highly consistent; stable across time",
    },
    "contextual_adaptability": {
        "low_score": "Rigid; one mode across all contexts",
        "mid_score": "Adaptive; adjusts tone but keeps core",
        "high_score": "Highly malleable; chameleon-like shifts",
    },
}

DIMENSIONS = list(PROFILE_SCHEMA.keys())


def _extract_observations_from_brief(brief_text: str) -> list[str]:
    """Pull behavioral observations from brief markdown."""
    observations: list[str] = []
    # Look for behavioral signal blocks
    for line in brief_text.split("\n"):
        line = line.strip()
        if line.startswith("**B") and ("Signal" in line or "signal" in line):
            observations.append(line)
        elif "body language" in line.lower() or "micro-expression" in line.lower():
            observations.append(line)
    return observations[:50]


def _extract_contradictions_for_prompt(contradictions: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for i, c in enumerate(contradictions[:5]):
        lines.append(
            f"{i+1}. A: \"{c.get('claim_a', '')}\" vs B: \"{c.get('claim_b', '')}\" — "
            f"Tension: {c.get('tension', '')}"
        )
    return "\n".join(lines) or "None detected."


async def run(
    investigation_id: str,
    instructions: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """Generate deep psychological profile."""
    actor = context.get("actor", "Unknown")
    inv_dir = Path(context["investigation_dir"])
    llm = context.get("llm_client")
    
    brief_path = inv_dir / "brief.md"
    brief_text = brief_path.read_text(encoding="utf-8") if brief_path.exists() else ""
    
    kg_path = inv_dir / "knowledge_graph.json"
    graph = {"contradictions": []}
    if kg_path.exists():
        graph = json.loads(kg_path.read_text(encoding="utf-8"))
    
    observations = _extract_observations_from_brief(brief_text)
    contra_text = _extract_contradictions_for_prompt(graph.get("contradictions", []))
    
    # Build the profiling prompt
    prompt = f"""You are a forensic psychologist analyzing a celebrity actor for a film producer.

ACTOR: {actor}

BEHAVIORAL OBSERVATIONS FROM VIDEO ANALYSIS:
{"\n".join(observations[:30]) or "No direct observations available."}

CONTRADICTIONS DETECTED:
{contra_text}

TASK: Produce a 5-dimension psychological profile AND predict behavior in 4 unseen contexts.

DIMENSIONS (score 1-10, where 1 = low/maladaptive, 5 = neutral, 10 = high/adaptive):
1. Stress Response — Does anxiety escalate or flatten under pressure?
2. Attachment Style — Is validation sought externally or internally?
3. Narcissistic Defense — How thick are the ego walls?
4. Temporal Stability — Consistent across time or context-dependent?
5. Contextual Adaptability — Rigid identity or chameleon-like?

UNSEEN CONTEXT PREDICTIONS (predict behavior in each):
A. Hostile press conference (aggressive journalists)
B. Action stunt (high physical risk, controlled environment)
C. Intimate drama scene (emotional vulnerability required)
D. Fan convention (intense adoration, screaming fans)

For each prediction: stress_level (1-10), confidence (1-10), risk_level (LOW/MEDIUM/HIGH), 2-sentence prediction.

Respond in strict JSON matching this schema:
{{
  "dimensions": {{
    "stress_response": {{"score": int, "description": str}},
    "attachment_style": {{"score": int, "description": str}},
    "narcissistic_defense": {{"score": int, "description": str}},
    "temporal_stability": {{"score": int, "description": str}},
    "contextual_adaptability": {{"score": int, "description": str}}
  }},
  "context_predictions": [
    {{"context": str, "stress_level": int, "confidence": int, "risk_level": str, "prediction": str}}
  ],
  "overall_risk_assessment": str,
  "red_flags": [str],
  "producer_recommendations": [str]
}}
"""
    
    profile: dict[str, Any] = {}
    if llm and llm.is_available():
        try:
            response = llm.generate_structured(prompt, schema=None)
            # Try to parse JSON from the response
            text = response if isinstance(response, str) else str(response)
            # Extract JSON block
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                profile = json.loads(match.group())
            else:
                profile = json.loads(text)
        except Exception as e:
            print(f"[Profiler] LLM failed: {e}")
            profile = {}
    
    # Validate and fill defaults
    if "dimensions" not in profile:
        profile["dimensions"] = {
            dim: {"score": 5, "description": "Insufficient data"}
            for dim in DIMENSIONS
        }
    for dim in DIMENSIONS:
        if dim not in profile["dimensions"]:
            profile["dimensions"][dim] = {"score": 5, "description": "Insufficient data"}
        else:
            if not isinstance(profile["dimensions"][dim], dict):
                profile["dimensions"][dim] = {
                    "score": int(profile["dimensions"][dim]),
                    "description": "Score only"
                }
    
    if "context_predictions" not in profile or not profile["context_predictions"]:
        profile["context_predictions"] = [
            {
                "context": "Hostile press conference",
                "stress_level": 5,
                "confidence": 5,
                "risk_level": "MEDIUM",
                "prediction": "Insufficient data for reliable prediction."
            },
            {
                "context": "Action stunt",
                "stress_level": 5,
                "confidence": 5,
                "risk_level": "MEDIUM",
                "prediction": "Insufficient data for reliable prediction."
            },
            {
                "context": "Intimate drama scene",
                "stress_level": 5,
                "confidence": 5,
                "risk_level": "MEDIUM",
                "prediction": "Insufficient data for reliable prediction."
            },
            {
                "context": "Fan convention",
                "stress_level": 5,
                "confidence": 5,
                "risk_level": "MEDIUM",
                "prediction": "Insufficient data for reliable prediction."
            },
        ]
    
    if "overall_risk_assessment" not in profile:
        profile["overall_risk_assessment"] = "Insufficient data for risk assessment."
    if "red_flags" not in profile:
        profile["red_flags"] = []
    if "producer_recommendations" not in profile:
        profile["producer_recommendations"] = []
    
    profile_path = inv_dir / "psychological_profile.json"
    profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    
    return {
        "success": True,
        "profile_path": str(profile_path),
        "dimensions": {k: v.get("score", 5) for k, v in profile["dimensions"].items()},
        "predictions_count": len(profile.get("context_predictions", [])),
    }
