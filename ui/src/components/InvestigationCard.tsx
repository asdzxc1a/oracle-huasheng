import { useNavigate } from "react-router-dom";
import { Film, Clock, ChevronRight } from "lucide-react";
import type { Investigation } from "../types";

interface InvestigationCardProps {
  investigation: Investigation;
}

export function InvestigationCard({ investigation }: InvestigationCardProps) {
  const navigate = useNavigate();

  const statusColors: Record<string, string> = {
    created: "text-mist",
    paused_for_human: "text-amber",
    video_analysis_completed: "text-emerald",
    actor_harvester_completed: "text-emerald",
    completed: "text-emerald",
  };

  const completedCount = investigation.agents_completed.length;
  const totalAgents = Object.values(investigation.pipeline).reduce(
    (sum, stage) => sum + Object.keys(stage).length,
    0
  );

  return (
    <button
      onClick={() => navigate(`/investigation/${investigation.id}`)}
      className="investigation-card w-full text-left bg-graphite border border-slate rounded-md p-4 hover:border-ash transition-all duration-200 group"
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <Film size={16} className="text-gold shrink-0" />
          <h3 className="text-sm font-medium text-parchment">
            {investigation.actor}
          </h3>
        </div>
        <ChevronRight
          size={16}
          className="text-ash group-hover:text-parchment transition-colors shrink-0"
        />
      </div>

      <p className="text-xs text-mist mb-3 line-clamp-2">
        {investigation.client_question}
      </p>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span
            className={`text-[10px] uppercase tracking-wider font-medium ${
              statusColors[investigation.status] || "text-mist"
            }`}
          >
            {investigation.status.replace(/_/g, " ")}
          </span>
          <span className="text-[10px] text-ash">
            {completedCount}/{totalAgents} agents
          </span>
        </div>
        <div className="flex items-center gap-1 text-ash">
          <Clock size={11} />
          <span className="text-[10px]">
            {new Date(investigation.created_at).toLocaleDateString()}
          </span>
        </div>
      </div>
    </button>
  );
}
