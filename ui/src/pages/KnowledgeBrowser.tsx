import { useState } from "react";
import { Network, AlertTriangle, CheckCircle, FileText } from "lucide-react";
import { useKnowledgeActors, useKnowledgeGraph } from "../hooks/useKnowledge";

export function KnowledgeBrowser() {
  const { actors, loading: actorsLoading } = useKnowledgeActors();
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <div className="h-full flex flex-col bg-obsidian text-parchment">
      {/* Header */}
      <div className="px-6 py-4 border-b border-graphite flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Network size={20} className="text-gold" />
          <div>
            <h1 className="text-lg font-semibold">Knowledge Graph</h1>
            <p className="text-xs text-mist">
              Claims, contradictions, and source network
            </p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Actor list */}
        <div className="w-64 border-r border-graphite overflow-y-auto">
          {actorsLoading && <p className="text-xs text-mist p-4">Loading...</p>}
          {actors.length === 0 && !actorsLoading && (
            <p className="text-xs text-mist p-4">No actors in graph</p>
          )}
          {actors.map((actor) => (
            <button
              key={actor.actor_id}
              onClick={() => setSelected(actor.actor_id)}
              className={`w-full text-left px-4 py-2.5 border-b border-graphite/50 text-xs transition-colors ${
                selected === actor.actor_id
                  ? "bg-graphite text-gold"
                  : "text-mist hover:text-parchment hover:bg-graphite/30"
              }`}
            >
              {actor.name}
            </button>
          ))}
        </div>

        {/* Graph view */}
        <div className="flex-1 overflow-y-auto p-6">
          {selected ? (
            <ActorGraph actorSlug={selected} />
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-mist">
              <Network size={48} className="mb-4 opacity-30" />
              <p className="text-sm">Select an actor to explore their knowledge graph</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ActorGraph({ actorSlug }: { actorSlug: string }) {
  const { graph, loading } = useKnowledgeGraph(actorSlug);

  if (loading) return <p className="text-mist text-sm">Loading...</p>;
  if (!graph) return <p className="text-mist text-sm">No data</p>;

  const claims = graph.claims || [];
  const contradictions = graph.contradictions || [];
  const sources = graph.sources || [];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Actor header */}
      {graph.actor && (
        <div className="border border-graphite rounded-sm p-4 bg-slate/30">
          <h2 className="text-lg font-semibold text-gold">{graph.actor.name}</h2>
          <p className="text-xs text-mist mt-1">{graph.actor.profile_text}</p>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <StatCard icon={<CheckCircle size={16} />} label="Claims" value={claims.length} />
        <StatCard icon={<AlertTriangle size={16} />} label="Contradictions" value={contradictions.length} />
        <StatCard icon={<FileText size={16} />} label="Sources" value={sources.length} />
      </div>

      {/* Claims */}
      {claims.length > 0 && (
        <div className="border border-graphite rounded-sm">
          <div className="px-4 py-2 border-b border-graphite bg-slate/20">
            <h3 className="text-sm font-medium">Claims</h3>
          </div>
          <div className="divide-y divide-graphite/50">
            {claims.map((claim) => (
              <div key={claim.claim_id} className="px-4 py-2 text-xs">
                <div className="flex items-center gap-2">
                  <TierBadge tier={claim.tier} />
                  <span className="text-parchment">{claim.text}</span>
                </div>
                <p className="text-ash mt-0.5">Confidence: {claim.confidence}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Contradictions */}
      {contradictions.length > 0 && (
        <div className="border border-graphite rounded-sm">
          <div className="px-4 py-2 border-b border-graphite bg-slate/20">
            <h3 className="text-sm font-medium">Contradictions</h3>
          </div>
          <div className="divide-y divide-graphite/50">
            {contradictions.map((c) => (
              <div key={c.contradiction_id} className="px-4 py-3 text-xs">
                <div className="grid grid-cols-2 gap-4 mb-2">
                  <div className="bg-slate/20 p-2 rounded-sm">
                    <p className="text-ash mb-0.5">Signal A</p>
                    <p className="text-parchment">{c.claim_a_text}</p>
                  </div>
                  <div className="bg-slate/20 p-2 rounded-sm">
                    <p className="text-ash mb-0.5">Signal B</p>
                    <p className="text-parchment">{c.claim_b_text}</p>
                  </div>
                </div>
                <p className="text-mist">
                  <span className="text-ash">Tension:</span> {c.tension}
                </p>
                <p className="text-mist mt-0.5">
                  <span className="text-ash">Implication:</span> {c.implication}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
}) {
  return (
    <div className="border border-graphite rounded-sm p-3 flex items-center gap-3 bg-slate/20">
      <div className="text-gold">{icon}</div>
      <div>
        <p className="text-lg font-semibold">{value}</p>
        <p className="text-[10px] text-ash uppercase">{label}</p>
      </div>
    </div>
  );
}

function TierBadge({ tier }: { tier: string }) {
  const colors: Record<string, string> = {
    A: "bg-red-900/40 text-red-300 border-red-800",
    B: "bg-yellow-900/40 text-yellow-300 border-yellow-800",
    C: "bg-green-900/40 text-green-300 border-green-800",
  };
  return (
    <span
      className={`px-1.5 py-0.5 text-[10px] font-bold border rounded-sm ${
        colors[tier] || colors.C
      }`}
    >
      {tier}
    </span>
  );
}
