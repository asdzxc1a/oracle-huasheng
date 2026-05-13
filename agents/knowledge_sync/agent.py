"""
Knowledge Sync Agent — Extracts structured data from briefs and stores in ChromaDB.

Runs after Video Analysis completes.
Reads: brief.md, research/*.md, video-catalog.json
Produces: Knowledge graph nodes in ChromaDB + knowledge_graph.json
"""

from __future__ import annotations

name = "knowledge_sync"
version = "1.0.0"

import json
import re
from pathlib import Path
from typing import Any

from oracle.kernel.knowledge_graph import KnowledgeGraph


def _extract_claims_from_brief(brief_text: str) -> list[dict[str, Any]]:
    """Extract tier-marked claims from the brief."""
    claims = []
    claim_pattern = re.compile(r"\*\*\(([ABC])\)\*\*\s+(.+?)(?:\n|$)")
    for match in claim_pattern.finditer(brief_text):
        tier = match.group(1)
        text = match.group(2).strip()
        text = re.sub(r"\(Tier\s+[A-Z]\)", "", text).strip()
        if text:
            claims.append({"tier": tier, "text": text})
    return claims


def _extract_contradictions_from_brief(brief_text: str) -> list[dict[str, Any]]:
    """Extract contradictions from the brief."""
    contradictions = []
    sections = brief_text.split("### Contradiction:")
    for section in sections[1:]:
        lines = section.split("\n")
        if not lines:
            continue
        claim_a = ""
        claim_b = ""
        tension = ""
        implication = ""
        for line in lines:
            if line.strip().startswith("- **Signal A:**"):
                claim_a = line.split("Signal A:**")[-1].strip()
            elif line.strip().startswith("- **Signal B:**"):
                claim_b = line.split("Signal B:**")[-1].strip()
            elif line.strip().startswith("- **Tension:**"):
                tension = line.split("Tension:**")[-1].strip()
            elif line.strip().startswith("- **Implication:**"):
                implication = line.split("Implication:**")[-1].strip()
        if claim_a and claim_b:
            contradictions.append({
                "claim_a": claim_a,
                "claim_b": claim_b,
                "tension": tension,
                "implication": implication,
            })
    return contradictions


def _extract_thesis(brief_text: str) -> str:
    """Extract main thesis from executive summary."""
    match = re.search(r"## Executive Summary(.*?)## ", brief_text, re.DOTALL)
    if match:
        return match.group(1).strip()[:500]
    return ""


def run(
    investigation_id: str,
    instructions: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """Sync investigation data into the knowledge graph."""
    actor = context.get("actor", "Unknown")
    inv_dir = Path(context["investigation_dir"])
    llm_client = context.get("llm_client")
    
    brief_path = inv_dir / "brief.md"
    brief_text = brief_path.read_text(encoding="utf-8") if brief_path.exists() else ""
    
    catalog_path = inv_dir / "research" / "video-catalog.json"
    catalog = {"videos": []}
    if catalog_path.exists():
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    
    kg = KnowledgeGraph()
    
    profile_text = _extract_thesis(brief_text) or f"Actor: {actor}"
    embedding = []
    if llm_client and llm_client.is_available():
        try:
            embedding = llm_client.embed_text(profile_text)
        except Exception:
            pass
    
    actor_slug = actor.lower().replace(" ", "-")
    
    kg.add_actor(
        actor_id=actor_slug,
        name=actor,
        profile_text=profile_text,
        embedding=embedding or [0.0] * 768,
        metadata={
            "last_investigation": investigation_id,
            "question": context.get("client_question", ""),
            "thesis": profile_text,
        },
    )
    
    claims = _extract_claims_from_brief(brief_text)
    for i, claim in enumerate(claims):
        claim_id = f"{actor_slug}_claim_{investigation_id}_{i}"
        claim_embedding = []
        if llm_client and llm_client.is_available():
            try:
                claim_embedding = llm_client.embed_text(claim["text"])
            except Exception:
                pass
        
        kg.add_claim(
            claim_id=claim_id,
            actor_id=actor_slug,
            text=claim["text"],
            tier=claim["tier"],
            source_type="unknown",
            access_level="MANAGED",
            confidence=0.5,
            embedding=claim_embedding or [0.0] * 768,
            investigation_id=investigation_id,
        )
    
    contradictions = _extract_contradictions_from_brief(brief_text)
    for i, contra in enumerate(contradictions):
        contra_id = f"{actor_slug}_contra_{investigation_id}_{i}"
        kg.add_contradiction(
            contradiction_id=contra_id,
            actor_id=actor_slug,
            claim_a_id=f"{actor_slug}_claim_{investigation_id}_0",
            claim_b_id=f"{actor_slug}_claim_{investigation_id}_1",
            claim_a_text=contra["claim_a"],
            claim_b_text=contra["claim_b"],
            tension=contra["tension"],
            implication=contra["implication"],
            investigation_id=investigation_id,
        )
    
    for i, video in enumerate(catalog.get("videos", [])):
        source_id = f"{actor_slug}_source_{investigation_id}_{i}"
        kg.add_source(
            source_id=source_id,
            actor_id=actor_slug,
            url=video.get("url", ""),
            title=video.get("title", "Unknown"),
            source_type=video.get("source_type", "unknown"),
            access_level=video.get("access_level", "MANAGED"),
            duration=str(video.get("duration", "unknown")),
            investigation_id=investigation_id,
        )
    
    graph = kg.export_graph(actor_slug)
    graph_path = inv_dir / "knowledge_graph.json"
    graph_path.write_text(json.dumps(graph, indent=2), encoding="utf-8")
    
    similar = kg.find_similar_actors(embedding or [0.0] * 768, n_results=5)
    
    return {
        "success": True,
        "actor_id": actor_slug,
        "claims_stored": len(claims),
        "contradictions_stored": len(contradictions),
        "sources_stored": len(catalog.get("videos", [])),
        "similar_actors": similar,
        "graph_path": str(graph_path),
    }
