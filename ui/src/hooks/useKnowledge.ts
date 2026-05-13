import { useState, useEffect, useCallback } from "react";

const API = "http://localhost:8000/api";

export interface ActorNode {
  actor_id: string;
  name: string;
  profile_text: string;
  metadata: Record<string, unknown>;
}

export interface ClaimNode {
  claim_id: string;
  text: string;
  tier: string;
  confidence: number;
}

export interface ContradictionEdge {
  contradiction_id: string;
  claim_a_text: string;
  claim_b_text: string;
  tension: string;
  implication: string;
}

export interface KnowledgeGraph {
  actor?: ActorNode;
  claims: ClaimNode[];
  contradictions: ContradictionEdge[];
  sources: Record<string, unknown>[];
}

export function useKnowledgeGraph(actorSlug: string) {
  const [graph, setGraph] = useState<KnowledgeGraph | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/knowledge/actors/${actorSlug}`);
      if (res.ok) {
        const data = await res.json();
        setGraph(data);
      }
    } catch (e) {
      console.error("Failed to load knowledge graph:", e);
    } finally {
      setLoading(false);
    }
  }, [actorSlug]);

  useEffect(() => {
    load();
  }, [load]);

  return { graph, loading, load };
}

export function useKnowledgeActors() {
  const [actors, setActors] = useState<{ actor_id: string; name: string }[]>([]);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/knowledge/actors`);
      const data = await res.json();
      setActors(data);
    } catch (e) {
      console.error("Failed to load actors:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { actors, loading, refresh };
}
