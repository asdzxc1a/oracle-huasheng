import { useState, useEffect } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "";

export function useFile(investigationId: string | undefined, filePath: string | undefined) {
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!investigationId || !filePath) {
      setContent(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    fetch(
      `${API_BASE}/api/investigations/${investigationId}/files/${encodeURIComponent(filePath)}`
    )
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const text = await res.text();
        if (!cancelled) setContent(text);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [investigationId, filePath]);

  return { content, loading, error };
}
