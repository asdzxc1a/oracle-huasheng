"""Knowledge Graph router — query and explore the knowledge graph."""

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..dependencies import get_base_path

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class SimilarActorsRequest(BaseModel):
    actor_slug: str
    n_results: int = 5


class QueryClaimsRequest(BaseModel):
    query: str
    n_results: int = 10


@router.get("/actors")
def list_actors(base_path=Depends(get_base_path)) -> list[dict[str, str]]:
    """List all actors in the knowledge graph."""
    from oracle.kernel.knowledge_graph import KnowledgeGraph
    kg = KnowledgeGraph()
    return kg.list_actors()


@router.get("/actors/{actor_slug}")
def get_actor(actor_slug: str) -> dict[str, Any]:
    """Get actor's knowledge graph."""
    from oracle.kernel.knowledge_graph import KnowledgeGraph
    kg = KnowledgeGraph()
    graph = kg.get_actor_summary(actor_slug)
    if not graph.get("claims") and not graph.get("actor"):
        raise HTTPException(status_code=404, detail="Actor not found in knowledge graph")
    return graph


@router.post("/actors/similar")
def find_similar_actors(req: SimilarActorsRequest) -> list[dict[str, Any]]:
    """Find actors similar to a given actor."""
    from oracle.kernel.knowledge_graph import KnowledgeGraph
    kg = KnowledgeGraph()
    # Get the actor's embedding
    graph = kg.export_graph(req.actor_slug)
    embedding = graph.get("actor", {}).get("embedding", [])
    if not embedding:
        return []
    return kg.find_similar_actors(embedding, n_results=req.n_results)


@router.post("/claims/search")
def search_claims(req: QueryClaimsRequest) -> list[dict[str, Any]]:
    """Search claims by semantic similarity."""
    from oracle.kernel.knowledge_graph import KnowledgeGraph
    kg = KnowledgeGraph()
    return kg.query_claims(req.query, n_results=req.n_results)


@router.get("/contradictions")
def list_contradictions() -> list[dict[str, Any]]:
    """List all contradictions across all actors."""
    from oracle.kernel.knowledge_graph import KnowledgeGraph
    kg = KnowledgeGraph()
    return kg.list_contradictions()
