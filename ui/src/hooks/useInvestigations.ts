import { useState, useEffect, useCallback } from "react";
import type { Investigation } from "../types";

const API_BASE = import.meta.env.VITE_API_URL || "";

export function useInvestigations() {
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchInvestigations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/investigations`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setInvestigations(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchInvestigations();
    const interval = setInterval(fetchInvestigations, 5000);
    return () => clearInterval(interval);
  }, [fetchInvestigations]);

  return { investigations, loading, error, refresh: fetchInvestigations };
}

export async function createInvestigation(
  actor: string,
  question: string,
  initialRead: string = ""
): Promise<Investigation> {
  const res = await fetch(`${API_BASE}/api/investigations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      actor,
      client_question: question,
      human_initial_read: initialRead,
    }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
