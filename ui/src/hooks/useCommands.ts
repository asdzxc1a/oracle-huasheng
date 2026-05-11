import { useState, useCallback } from "react";
import type { CommandResult } from "../types";

const API_BASE = import.meta.env.VITE_API_URL || "";

export function useCommands() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<CommandResult | null>(null);

  const runCommand = useCallback(
    async (
      command: "assess" | "harvest" | "compare",
      payload: Record<string, unknown>
    ): Promise<CommandResult | null> => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_BASE}/api/commands/${command}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: CommandResult = await res.json();
        setLastResult(data);
        return data;
      } catch (e) {
        setError(e instanceof Error ? e.message : "Command failed");
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return { runCommand, loading, error, lastResult };
}
