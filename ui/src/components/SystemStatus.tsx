import { CheckCircle, XCircle, Activity, Brain, Wrench } from "lucide-react";
import { useSystemStatus } from "../hooks/useSystemStatus";

function StatusDot({ ok }: { ok: boolean }) {
  return ok ? (
    <CheckCircle size={12} className="text-emerald" />
  ) : (
    <XCircle size={12} className="text-crimson" />
  );
}

export function SystemStatus() {
  const { status, loading } = useSystemStatus();

  if (loading) {
    return (
      <div className="bg-graphite border border-slate rounded-md p-4">
        <p className="text-xs text-mist">Loading system status…</p>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="bg-graphite border border-slate rounded-md p-4">
        <p className="text-xs text-crimson">API offline</p>
      </div>
    );
  }

  return (
    <div className="bg-graphite border border-slate rounded-md p-4">
      <div className="flex items-center gap-2 mb-3">
        <Activity size={14} className="text-gold" />
        <h3 className="text-xs font-semibold uppercase tracking-widest text-ash">
          System Status
        </h3>
        <span className="text-[10px] text-mist ml-auto">v{status.version}</span>
      </div>

      <div className="space-y-2">
        {/* LLM */}
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <Brain size={12} className="text-mist" />
            <span className="text-parchment">Gemini LLM</span>
          </div>
          <StatusDot ok={status.llm.available} />
        </div>
        {status.llm.available && (
          <p className="text-[10px] text-ash pl-5">
            {status.llm.text_model} / {status.llm.video_model}
          </p>
        )}

        {/* Tools */}
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <Wrench size={12} className="text-mist" />
            <span className="text-parchment">Tools</span>
          </div>
          <div className="flex items-center gap-1">
            {Object.entries(status.tools).map(([name, ok]) => (
              <span
                key={name}
                className={`text-[10px] px-1 py-0.5 rounded-sm ${
                  ok ? "bg-emerald/15 text-emerald" : "bg-crimson/15 text-crimson"
                }`}
              >
                {name.replace("_", "-")}
              </span>
            ))}
          </div>
        </div>

        {/* Knowledge Graph */}
        <div className="flex items-center justify-between text-xs">
          <span className="text-parchment">Knowledge Graph</span>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-ash">
              {status.knowledge_graph.actors} actors
            </span>
            <StatusDot ok={status.knowledge_graph.available} />
          </div>
        </div>

        {/* Agents */}
        <div className="flex items-center justify-between text-xs">
          <span className="text-parchment">Agents</span>
          <span className="text-[10px] text-ash">
            {status.agents.count} loaded
          </span>
        </div>
      </div>
    </div>
  );
}
