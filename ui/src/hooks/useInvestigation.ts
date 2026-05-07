import { useState, useEffect, useCallback } from "react";
import type { InvestigationDetail } from "../types";

const API_BASE = import.meta.env.VITE_API_URL || "";

export function useInvestigation(id: string | undefined) {
  const [detail, setDetail] = useState<InvestigationDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDetail = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/investigations/${id}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setDetail(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchDetail();
    const interval = setInterval(fetchDetail, 3000);
    return () => clearInterval(interval);
  }, [fetchDetail]);

  return { detail, loading, error, refresh: fetchDetail };
}
