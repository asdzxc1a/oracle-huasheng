"""
Oracle Knowledge Graph — ChromaDB-based vector graph.

Collections:
  - actors: Actor psychological profiles
  - claims: Individual diagnostic claims
  - contradictions: Preserved tension pairs
  - sources: Video sources with metadata

Each node has:
  - embedding (vector)
  - metadata (JSON)
  - document (human-readable text)
  - graph edges (stored in metadata as JSON)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings


@dataclass
class KnowledgeNode:
    id: str
    type: str  # actor, claim, contradiction, source, investigation
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None


class KnowledgeGraph:
    """
    ChromaDB-based knowledge graph for the Oracle.
    Self-hosted, no external API needed after setup.
    """

    def __init__(self, persist_dir: str | Path | None = None) -> None:
        if persist_dir is None:
            persist_dir = Path(__file__).resolve().parent.parent / "knowledge_db"
        
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        
        # Get or create collections
        self.actors = self.client.get_or_create_collection("actors")
        self.claims = self.client.get_or_create_collection("claims")
        self.contradictions = self.client.get_or_create_collection("contradictions")
        self.sources = self.client.get_or_create_collection("sources")
        self.investigations = self.client.get_or_create_collection("investigations")
    
    def add_actor(
        self,
        actor_id: str,
        name: str,
        profile_text: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add or update an actor profile."""
        meta = metadata or {}
        meta["name"] = name
        meta["type"] = "actor"
        meta["last_updated"] = meta.get("last_updated", "")
        
        self.actors.upsert(
            ids=[actor_id],
            documents=[profile_text],
            embeddings=[embedding],
            metadatas=[meta],
        )
    
    def add_claim(
        self,
        claim_id: str,
        actor_id: str,
        text: str,
        tier: str,
        source_type: str,
        access_level: str,
        confidence: float,
        embedding: list[float],
        investigation_id: str = "",
    ) -> None:
        """Add a diagnostic claim."""
        self.claims.upsert(
            ids=[claim_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[{
                "actor_id": actor_id,
                "tier": tier,
                "source_type": source_type,
                "access_level": access_level,
                "confidence": confidence,
                "investigation_id": investigation_id,
                "type": "claim",
            }],
        )
    
    def add_contradiction(
        self,
        contradiction_id: str,
        actor_id: str,
        claim_a_id: str,
        claim_b_id: str,
        claim_a_text: str,
        claim_b_text: str,
        tension: str,
        implication: str,
        investigation_id: str = "",
    ) -> None:
        """Add a preserved contradiction pair."""
        doc = f"Contradiction: {claim_a_text} vs {claim_b_text}. Tension: {tension}."
        self.contradictions.upsert(
            ids=[contradiction_id],
            documents=[doc],
            metadatas=[{
                "actor_id": actor_id,
                "claim_a_id": claim_a_id,
                "claim_b_id": claim_b_id,
                "tension": tension,
                "implication": implication,
                "investigation_id": investigation_id,
                "type": "contradiction",
            }],
        )
    
    def add_source(
        self,
        source_id: str,
        actor_id: str,
        url: str,
        title: str,
        source_type: str,
        access_level: str,
        duration: str,
        investigation_id: str = "",
    ) -> None:
        """Add a video source."""
        self.sources.upsert(
            ids=[source_id],
            documents=[f"{title}: {url}"],
            metadatas=[{
                "actor_id": actor_id,
                "url": url,
                "title": title,
                "source_type": source_type,
                "access_level": access_level,
                "duration": duration,
                "investigation_id": investigation_id,
                "type": "source",
            }],
        )
    
    def find_similar_actors(
        self,
        embedding: list[float],
        n_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Find actors with similar psychological profiles."""
        results = self.actors.query(
            query_embeddings=[embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        
        actors = []
        if results["ids"] and results["ids"][0]:
            for i, actor_id in enumerate(results["ids"][0]):
                actors.append({
                    "id": actor_id,
                    "name": results["metadatas"][0][i].get("name", actor_id),
                    "similarity": 1.0 - (results["distances"][0][i] if results["distances"] else 0),
                    "profile": results["documents"][0][i] if results["documents"] else "",
                })
        return actors
    
    def find_claims_by_type(
        self,
        query_text: str,
        n_results: int = 10,
    ) -> list[dict[str, Any]]:
        """Find claims matching a query (e.g. 'fight response')."""
        # Use basic text search since we may not have embeddings for all claims
        results = self.claims.query(
            query_texts=[query_text],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        
        claims = []
        if results["ids"] and results["ids"][0]:
            for i, claim_id in enumerate(results["ids"][0]):
                claims.append({
                    "id": claim_id,
                    "text": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                })
        return claims
    
    def get_actor_claims(self, actor_id: str) -> list[dict[str, Any]]:
        """Get all claims for an actor."""
        results = self.claims.get(
            where={"actor_id": actor_id},
            include=["documents", "metadatas"],
        )
        
        claims = []
        if results["ids"]:
            for i, claim_id in enumerate(results["ids"]):
                claims.append({
                    "id": claim_id,
                    "text": results["documents"][i] if results["documents"] else "",
                    "metadata": results["metadatas"][i] if results["metadatas"] else {},
                })
        return claims
    
    def get_actor_contradictions(self, actor_id: str) -> list[dict[str, Any]]:
        """Get all contradictions for an actor."""
        results = self.contradictions.get(
            where={"actor_id": actor_id},
            include=["documents", "metadatas"],
        )
        
        contradictions = []
        if results["ids"]:
            for i, cid in enumerate(results["ids"]):
                contradictions.append({
                    "id": cid,
                    "text": results["documents"][i] if results["documents"] else "",
                    "metadata": results["metadatas"][i] if results["metadatas"] else {},
                })
        return contradictions
    
    def export_graph(self, actor_id: str) -> dict[str, Any]:
        """Export knowledge graph for an actor as JSON."""
        claims = self.get_actor_claims(actor_id)
        contradictions = self.get_actor_contradictions(actor_id)
        
        actor_result = self.actors.get(ids=[actor_id])
        actor_doc = actor_result["documents"][0] if actor_result["documents"] else ""
        actor_meta = actor_result["metadatas"][0] if actor_result["metadatas"] else {}
        
        nodes = []
        edges = []
        
        # Actor node
        nodes.append({
            "id": actor_id,
            "type": "actor",
            "label": actor_meta.get("name", actor_id),
            "text": actor_doc[:200],
        })
        
        # Claim nodes
        for c in claims:
            nodes.append({
                "id": c["id"],
                "type": "claim",
                "label": c["text"][:60] + "...",
                "text": c["text"],
                "tier": c["metadata"].get("tier", "C"),
            })
            edges.append({"from": actor_id, "to": c["id"], "relation": "has_claim"})
        
        # Contradiction edges
        for c in contradictions:
            meta = c["metadata"]
            cid = c["id"]
            claim_a = meta.get("claim_a_id", "")
            claim_b = meta.get("claim_b_id", "")
            
            nodes.append({
                "id": cid,
                "type": "contradiction",
                "label": meta.get("tension", "Contradiction"),
                "text": c["text"],
            })
            
            if claim_a:
                edges.append({"from": claim_a, "to": cid, "relation": "contradicts"})
            if claim_b:
                edges.append({"from": claim_b, "to": cid, "relation": "contradicts"})
        
        return {"nodes": nodes, "edges": edges}
    
    def get_actor_summary(self, actor_id: str) -> dict[str, Any]:
        """Export actor summary in frontend-friendly format."""
        claims = self.get_actor_claims(actor_id)
        contradictions = self.get_actor_contradictions(actor_id)
        
        actor_result = self.actors.get(ids=[actor_id])
        actor_doc = actor_result["documents"][0] if actor_result["documents"] else ""
        actor_meta = actor_result["metadatas"][0] if actor_result["metadatas"] else {}
        
        # Get sources for this actor
        source_results = self.sources.get(
            where={"actor_id": actor_id},
            include=["documents", "metadatas"],
        )
        sources = []
        if source_results["ids"]:
            for i, sid in enumerate(source_results["ids"]):
                meta = source_results["metadatas"][i] if source_results["metadatas"] else {}
                sources.append({
                    "source_id": sid,
                    "actor_id": meta.get("actor_id", ""),
                    "url": meta.get("url", ""),
                    "title": meta.get("title", "Unknown"),
                    "source_type": meta.get("source_type", "unknown"),
                    "access_level": meta.get("access_level", "MANAGED"),
                    "duration": meta.get("duration", "unknown"),
                })
        
        return {
            "actor": {
                "actor_id": actor_id,
                "name": actor_meta.get("name", actor_id),
                "profile_text": actor_doc[:500],
                "metadata": actor_meta,
            },
            "claims": [
                {
                    "claim_id": c["id"],
                    "text": c["text"],
                    "tier": c["metadata"].get("tier", "C"),
                    "confidence": c["metadata"].get("confidence", 0.5),
                }
                for c in claims
            ],
            "contradictions": [
                {
                    "contradiction_id": c["id"],
                    "claim_a_text": c["metadata"].get("claim_a_text", ""),
                    "claim_b_text": c["metadata"].get("claim_b_text", ""),
                    "tension": c["metadata"].get("tension", ""),
                    "implication": c["metadata"].get("implication", ""),
                }
                for c in contradictions
            ],
            "sources": sources,
        }
    
    def list_actors(self) -> list[dict[str, str]]:
        """List all actors in the knowledge graph."""
        results = self.actors.get(include=["metadatas"])
        actors = []
        if results["ids"]:
            for i, actor_id in enumerate(results["ids"]):
                meta = results["metadatas"][i] if results["metadatas"] else {}
                actors.append({
                    "actor_id": actor_id,
                    "name": meta.get("name", actor_id),
                })
        return actors
    
    def list_contradictions(self) -> list[dict[str, Any]]:
        """List all contradictions across all actors."""
        results = self.contradictions.get(include=["documents", "metadatas"])
        contradictions = []
        if results["ids"]:
            for i, cid in enumerate(results["ids"]):
                meta = results["metadatas"][i] if results["metadatas"] else {}
                contradictions.append({
                    "contradiction_id": cid,
                    "actor_id": meta.get("actor_id", ""),
                    "claim_a_text": meta.get("claim_a_text", ""),
                    "claim_b_text": meta.get("claim_b_text", ""),
                    "tension": meta.get("tension", ""),
                    "implication": meta.get("implication", ""),
                })
        return contradictions
    
    def query_claims(self, query_text: str, n_results: int = 10) -> list[dict[str, Any]]:
        """Search claims by semantic similarity."""
        return self.find_claims_by_type(query_text, n_results)
