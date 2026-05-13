import { useState, useEffect, useCallback } from "react";

const API = "http://localhost:8000/api";

export interface WikiPage {
  actor_slug: string;
  title: string;
  updated: number;
  content?: string;
}

export function useWikiPages() {
  const [pages, setPages] = useState<WikiPage[]>([]);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/wiki`);
      const data = await res.json();
      setPages(data);
    } catch (e) {
      console.error("Failed to load wiki pages:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { pages, loading, refresh };
}

export function useWikiPage(actorSlug: string) {
  const [page, setPage] = useState<WikiPage | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/wiki/${actorSlug}`);
      if (res.ok) {
        const data = await res.json();
        setPage(data);
      }
    } catch (e) {
      console.error("Failed to load wiki page:", e);
    } finally {
      setLoading(false);
    }
  }, [actorSlug]);

  const save = useCallback(
    async (content: string) => {
      try {
        const res = await fetch(`${API}/wiki/${actorSlug}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content }),
        });
        if (res.ok) {
          setPage((prev) => (prev ? { ...prev, content } : null));
        }
      } catch (e) {
        console.error("Failed to save wiki page:", e);
      }
    },
    [actorSlug]
  );

  useEffect(() => {
    load();
  }, [load]);

  return { page, loading, load, save };
}
