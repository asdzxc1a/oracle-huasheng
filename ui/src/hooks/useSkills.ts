import { useState, useEffect, useCallback } from "react";
import type { Skill } from "../types";

const API_BASE = import.meta.env.VITE_API_URL || "";

export function useSkills() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSkills = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/skills`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: Skill[] = await res.json();
      setSkills(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load skills");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSkills();
  }, [fetchSkills]);

  return { skills, loading, error, refresh: fetchSkills };
}

export async function fetchSkillBody(name: string): Promise<{ name: string; description: string; body: string; has_scripts: boolean; has_references: boolean; has_assets: boolean }> {
  const res = await fetch(`${API_BASE}/api/skills/${encodeURIComponent(name)}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
