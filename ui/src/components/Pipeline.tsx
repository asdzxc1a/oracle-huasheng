import { Check, Circle, AlertTriangle, Pause } from "lucide-react";
import type { Investigation, PipelineStage } from "../types";

interface PipelineProps {
  investigation: Investigation;
  onRunAgent?: (agent: string) => void;
}

const STAGE_ORDER: PipelineStage[] = [
  "truth",
  "readiness",
  "presence",
  "proof",
  "deployment",
];

const STAGE_LABELS: Record<PipelineStage, string> = {
  truth: "Truth",
  readiness: "Readiness",
  presence: "Presence",
  proof: "Proof",
  deployment: "Deployment",
};

function StatusIcon({ status }: { status: string }) {
  if (status === "completed")
    return <Check size={12} className="text-emerald" />;
  if (status === "running")
    return (
      <div className="w-3 h-3 rounded-full bg-gold animate-pulse-gold" />
    );
  if (status === "failed")
    return <AlertTriangle size={12} className="text-crimson" />;
  if (status === "paused_for_human")
    return <Pause size={12} className="text-amber" />;
  return <Circle size={12} className="text-ash" />;
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: "bg-emerald/15 text-emerald",
    running: "bg-gold/15 text-gold",
    failed: "bg-crimson/15 text-crimson",
    paused_for_human: "bg-amber/15 text-amber",
    not_started: "bg-graphite text-ash",
  };
  return (
    <span
      className={`text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded-sm font-medium ${
        styles[status] || styles.not_started
      }`}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}

export function Pipeline({ investigation, onRunAgent }: PipelineProps) {
  return (
    <aside className="w-72 h-full bg-graphite border-r border-slate flex flex-col shrink-0 overflow-y-auto">
      <div className="px-4 py-4 border-b border-slate">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-mist">
          Pipeline
        </h2>
        <p className="text-[10px] text-ash mt-1">
          {investigation.actor} — {investigation.id.slice(0, 20)}…
        </p>
      </div>

      <div className="flex-1 py-2">
        {STAGE_ORDER.map((stage) => {
          const agents = investigation.pipeline[stage] || {};
          const agentEntries = Object.entries(agents);
          if (agentEntries.length === 0) return null;

          return (
            <div key={stage} className="mb-3">
              <div className="px-4 py-1.5">
                <span className="text-[10px] uppercase tracking-widest text-ash font-medium">
                  {STAGE_LABELS[stage]}
                </span>
              </div>
              {agentEntries.map(([agent, status]) => (
                <div
                  key={agent}
                  className="px-4 py-2 flex items-center justify-between group hover:bg-slate/50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <StatusIcon status={status} />
                    <span className="text-xs text-parchment capitalize">
                      {agent.replace(/_/g, " ")}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={status} />
                    {status === "not_started" && onRunAgent && (
                      <button
                        onClick={() => onRunAgent(agent)}
                        className="opacity-0 group-hover:opacity-100 text-[10px] text-gold hover:underline transition-opacity"
                      >
                        Run
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          );
        })}
      </div>

      {/* Human actions */}
      {investigation.human_actions_required.length > 0 && (
        <div className="mx-3 mb-3 p-3 bg-amber/10 border border-amber/30 rounded-md">
          <div className="flex items-center gap-2 mb-2">
            <Pause size={14} className="text-amber" />
            <span className="text-xs font-medium text-amber">
              Human Review Required
            </span>
          </div>
          {investigation.human_actions_required.map((action) => (
            <p key={action} className="text-[11px] text-parchment mb-1">
              {action.replace(/_/g, " ")}
            </p>
          ))}
        </div>
      )}

      {/* Completed agents */}
      {investigation.agents_completed.length > 0 && (
        <div className="px-4 py-2 border-t border-slate">
          <p className="text-[10px] text-ash uppercase tracking-wider mb-1">
            Completed
          </p>
          <p className="text-xs text-mist">
            {investigation.agents_completed.length} agent
            {investigation.agents_completed.length > 1 ? "s" : ""}
          </p>
        </div>
      )}
    </aside>
  );
}
