import { useState, useEffect } from "react";

const API = "http://localhost:8000/api";

export interface SystemStatus {
  api: string;
  version: string;
  llm: {
    available: boolean;
    provider: string;
    text_model: string;
    video_model: string;
  };
  tools: {
    yt_dlp: boolean;
    ffmpeg: boolean;
    ffprobe: boolean;
  };
  knowledge_graph: {
    available: boolean;
    actors: number;
  };
  agents: {
    count: number;
    names: string[];
  };
}

export function useSystemStatus() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetch(`${API}/status`)
      .then((r) => r.json())
      .then((data) => setStatus(data))
      .catch(() => setStatus(null))
      .finally(() => setLoading(false));
  }, []);

  return { status, loading };
}
