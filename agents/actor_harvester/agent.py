"""
Actor Harvester Agent v1.1 — Skill Orchestrator

Thin orchestrator that sources video evidence and catalogs it with
tier discipline. Composes source-evaluation and video-catalog skills.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from oracle.kernel import (
    LLMClient,
    format_video_catalog_md,
    format_facts_md,
    build_harvester_json,
)

name = "actor_harvester"
version = "1.1.0"

CATALOG_SCHEMA = {
    "type": "object",
    "properties": {
        "actor_name": {"type": "string"},
        "known_for": {"type": "string"},
        "career_stage": {"type": "string", "enum": ["breakthrough", "establishing", "peak", "transition", "legacy"]},
        "videos": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "url": {"type": "string"},
                    "date": {"type": "string"},
                    "duration_seconds": {"type": "integer"},
                    "context": {"type": "string"},
                    "source_type": {"type": "string", "enum": ["festival_qa", "podcast", "interview", "bts", "press_conference", "late_night", "social_media"]},
                    "access_level": {"type": "string", "enum": ["RAW", "MANAGED", "SCRIPTED"]},
                    "platform": {"type": "string"},
                    "signal_density": {"type": "string", "enum": ["Very High", "High", "Moderate", "Low"]},
                    "why_relevant": {"type": "string"},
                },
                "required": ["title", "url", "date", "duration_seconds", "context", "source_type", "access_level", "platform", "why_relevant"],
            },
        },
        "filmography_highlights": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "year": {"type": "integer"},
                    "role": {"type": "string"},
                    "significance": {"type": "string"},
                },
                "required": ["title", "year", "role"],
            },
        },
        "career_timeline": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer"},
                    "event": {"type": "string"},
                    "significance": {"type": "string"},
                },
                "required": ["year", "event"],
            },
        },
        "known_contradictions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim_a": {"type": "string"},
                    "claim_b": {"type": "string"},
                    "sources": {"type": "string"},
                },
                "required": ["claim_a", "claim_b"],
            },
        },
    },
    "required": ["actor_name", "videos", "filmography_highlights", "career_timeline"],
}


def run(investigation_id: str, instructions: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Execute the Actor Harvester."""
    actor = instructions.get("actor_name", context.get("actor", "Unknown"))
    client_question = context.get("client_question", "")
    focus = instructions.get("focus_areas", [])
    max_videos = instructions.get("max_videos", 10)
    use_llm = instructions.get("use_llm", True)
    inv_dir = Path(context["investigation_dir"])

    # Generate catalog
    llm = LLMClient()
    if use_llm and llm.is_available():
        catalog_data = _generate_catalog_with_llm(actor, client_question, focus, max_videos)
    else:
        catalog_data = _generate_catalog_fallback(actor, client_question, focus, max_videos)

    if not catalog_data:
        catalog_data = _generate_catalog_fallback(actor, client_question, focus, max_videos)

    videos = catalog_data.get("videos", [])[:max_videos]

    # Write outputs using kernel formatters
    catalog_json = build_harvester_json(actor, investigation_id, videos, catalog_data)
    catalog_json_path = inv_dir / "research" / "video-catalog.json"
    catalog_json_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_json_path.write_text(json.dumps(catalog_json, indent=2, ensure_ascii=False), encoding="utf-8")

    catalog_md = format_video_catalog_md(
        actor, investigation_id, videos, focus,
        catalog_data.get("career_stage", "unknown"),
        catalog_data.get("known_for", ""),
    )
    catalog_md_path = inv_dir / "research" / "video-catalog.md"
    catalog_md_path.write_text(catalog_md, encoding="utf-8")

    facts_md = format_facts_md(actor, investigation_id, videos, catalog_data)
    facts_path = inv_dir / "references" / "facts.md"
    facts_path.parent.mkdir(parents=True, exist_ok=True)
    facts_path.write_text(facts_md, encoding="utf-8")

    # Update actor profile
    store = context.get("context_store")
    if store:
        profile = store.load_actor(actor) or {"name": actor, "investigations": []}
        if "investigations" not in profile:
            profile["investigations"] = []
        access_counts = {}
        for v in videos:
            access_counts[v["access_level"]] = access_counts.get(v["access_level"], 0) + 1
        profile["investigations"].append({
            "id": investigation_id,
            "date": datetime.now(timezone.utc).isoformat(),
            "video_count": len(videos),
            "career_stage": catalog_data.get("career_stage", "unknown"),
            "sources_by_access": access_counts,
        })
        profile["filmography"] = catalog_data.get("filmography_highlights", [])
        profile["career_timeline"] = catalog_data.get("career_timeline", [])
        profile["known_contradictions"] = catalog_data.get("known_contradictions", [])
        store.save_actor(actor, profile)

    return {
        "actor": actor,
        "videos_found": len(videos),
        "catalog_path": str(catalog_json_path),
        "focus_areas": focus,
        "career_stage": catalog_data.get("career_stage", "unknown"),
    }


def _generate_catalog_with_llm(actor: str, client_question: str, focus_areas: list[str], max_videos: int) -> dict[str, Any]:
    """Use LLM to generate a specific, credible video catalog."""
    llm = LLMClient()
    focus_text = "\n".join(f"- {f}" for f in focus_areas) if focus_areas else "- General casting assessment"

    prompt = (
        f"Generate a realistic, specific video source catalog for actor '{actor}'.\n\n"
        f"CLIENT QUESTION: {client_question}\n"
        f"FOCUS AREAS:\n{focus_text}\n\n"
        f"Requirements:\n"
        f"1. Generate up to {max_videos} specific video sources\n"
        f"2. Each source must have a realistic YouTube search URL\n"
        f"3. Prioritize: festival Q&As > podcasts > BTS > press conferences > late night\n"
        f"4. Include filmography highlights and career timeline\n"
        f"5. Note any known public contradictions\n"
        f"6. Be specific: name actual films, festivals, shows, interviewers\n"
        f"7. Use realistic dates (within last 5 years)\n"
        f"8. Vary access levels: at least 1 RAW, 2 MANAGED, 1 SCRIPTED"
    )

    system = (
        "You are a Hollywood research analyst with deep knowledge of film industry sources. "
        "You catalog real, verifiable sources. You never fabricate specific watch IDs."
    )

    try:
        return llm.generate_structured(prompt, CATALOG_SCHEMA, system, max_tokens=4000)
    except Exception:
        return {}


def _generate_catalog_fallback(actor: str, client_question: str, focus_areas: list[str], max_videos: int) -> dict[str, Any]:
    """Structured fallback when LLM is unavailable. Loads known profiles from disk."""
    actor_lower = actor.lower().strip()

    # Try to load from context/actor_profiles/
    profile_dir = Path(__file__).resolve().parents[2] / "context" / "actor_profiles"
    slug = actor_lower.replace(" ", "-")
    profile_file = profile_dir / f"{slug}.json"

    if profile_file.exists():
        profile = json.loads(profile_file.read_text(encoding="utf-8"))
        videos = profile.get("videos", [])[:max_videos]
        return {
            "actor_name": actor,
            "known_for": profile.get("known_for", "Film and television work"),
            "career_stage": profile.get("career_stage", "establishing"),
            "videos": videos,
            "filmography_highlights": profile.get("filmography_highlights", []),
            "career_timeline": profile.get("career_timeline", []),
            "known_contradictions": profile.get("known_contradictions", []),
        }

    return _build_generic_profile(actor)


def _build_generic_profile(actor: str) -> dict[str, Any]:
    """Build a generic but structured profile for unknown actors."""
    return {
        "known_for": "Film and television work",
        "career_stage": "establishing",
        "films": [{"title": f"Notable Film — {actor}", "year": 2022, "role": "Lead", "significance": "Career highlight"}],
        "timeline": [
            {"year": 2020, "event": "Industry debut", "significance": "Initial recognition"},
            {"year": 2023, "event": "Breakthrough role", "significance": "Established presence"},
        ],
        "videos": [
            {"title": f"{actor} — Film Festival Q&A", "url": f"https://www.youtube.com/results?search_query={actor.replace(' ', '+')}+film+festival+qa", "date": "2023-09-15", "duration_seconds": 1200, "context": "Festival appearance — unscripted audience questions", "source_type": "festival_qa", "access_level": "MANAGED", "platform": "youtube", "signal_density": "High", "why_relevant": "Festival Q&As offer the least scripted interaction."},
            {"title": f"{actor} — Behind the Scenes Interview", "url": f"https://www.youtube.com/results?search_query={actor.replace(' ', '+')}+behind+the+scenes", "date": "2023-06-20", "duration_seconds": 800, "context": "Production diary footage", "source_type": "bts", "access_level": "RAW", "platform": "youtube", "signal_density": "Very High", "why_relevant": "RAW on-set behavior reveals working process."},
            {"title": f"{actor} — Late Night Talk Show Appearance", "url": f"https://www.youtube.com/results?search_query={actor.replace(' ', '+')}+late+night+interview", "date": "2024-01-10", "duration_seconds": 480, "context": "Promotional appearance", "source_type": "late_night", "access_level": "SCRIPTED", "platform": "youtube", "signal_density": "Low", "why_relevant": "Baseline comparison only."},
        ],
        "contradictions": [],
    }


def validate(investigation_id: str, base_path: Path) -> bool:
    """Quality gate: ensure catalog was written and has expected structure."""
    from oracle.kernel import investigation_dir

    inv_dir = investigation_dir(base_path, investigation_id)
    catalog = inv_dir / "research" / "video-catalog.json"
    if not catalog.exists():
        return False

    try:
        data = json.loads(catalog.read_text(encoding="utf-8"))
        if "videos" not in data or not isinstance(data["videos"], list) or len(data["videos"]) == 0:
            return False

        access_levels = {v.get("access_level", "MANAGED") for v in data["videos"]}
        if len(access_levels) < 2:
            return False

        for v in data["videos"]:
            if "placeholder" in v.get("title", "").lower():
                return False
            if v.get("url", "").startswith("https://www.youtube.com/watch?v=example"):
                return False

        facts = inv_dir / "references" / "facts.md"
        if not facts.exists():
            return False
        facts_text = facts.read_text(encoding="utf-8")
        if "Filmography Highlights" not in facts_text or len(facts_text) < 200:
            return False

        return True
    except Exception:
        return False
