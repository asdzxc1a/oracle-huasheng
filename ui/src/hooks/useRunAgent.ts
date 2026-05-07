import { useState } from "react";
import type { JobStatus } from "../types";

const API_BASE = import.meta.env.VITE_API_URL || "";

export function useRunAgent() {
  const [running, setRunning] = useState<Record<string, boolean>>({});

  const runAgent = async (
    investigationId: string,
    agentName: string,
    instructions?: Record<string, unknown>
  ): Promise<JobStatus> => {
    const key = `${investigationId}-${agentName}`;
    setRunning((prev) => ({ ...prev, [key]: true }));
    try {
      const res = await fetch(
        `${API_BASE}/api/investigations/${investigationId}/agents/${agentName}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ instructions: instructions || {} }),
        }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    } finally {
      setRunning((prev) => ({ ...prev, [key]: false }));
    }
  };

  const isRunning = (investigationId: string, agentName: string) =>
    running[`${investigationId}-${agentName}`] || false;

  const pollJob = async (jobId: string): Promise<JobStatus> => {
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  };

  return { runAgent, isRunning, pollJob };
}
