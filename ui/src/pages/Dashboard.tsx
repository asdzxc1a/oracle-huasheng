import { Film, Plus, Activity } from "lucide-react";
import { InvestigationCard } from "../components/InvestigationCard";
import { CreateInvestigationModal } from "../components/CreateInvestigationModal";
import { useInvestigations, createInvestigation } from "../hooks/useInvestigations";
import { useState } from "react";

export function Dashboard() {
  const { investigations, loading, error, refresh } = useInvestigations();
  const [showModal, setShowModal] = useState(false);

  const handleCreate = async (actor: string, question: string, initialRead: string) => {
    await createInvestigation(actor, question, initialRead);
    refresh();
  };

  const activeCount = investigations.filter(
    (i) => i.agents_pending.length > 0 || i.human_actions_required.length > 0
  ).length;

  const completedCount = investigations.filter(
    (i) => i.agents_completed.length > 0 && i.agents_pending.length === 0
  ).length;

  return (
    <div className="h-full overflow-y-auto">
      {/* Header */}
      <div className="px-8 py-6 border-b border-slate">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-parchment tracking-tight">
              Dashboard
            </h1>
            <p className="text-xs text-mist mt-1">
              Overview of all actor assessments
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 bg-gold text-obsidian px-4 py-2 text-xs font-medium uppercase tracking-wider rounded-sm hover:brightness-110 transition-all"
          >
            <Plus size={14} />
            New Investigation
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="px-8 py-4 grid grid-cols-3 gap-4 max-w-2xl">
        <div className="bg-graphite border border-slate rounded-md p-4">
          <div className="flex items-center gap-2 mb-1">
            <Film size={14} className="text-gold" />
            <span className="text-[10px] uppercase tracking-widest text-ash font-medium">
              Total
            </span>
          </div>
          <p className="text-2xl font-semibold text-parchment">
            {investigations.length}
          </p>
        </div>
        <div className="bg-graphite border border-slate rounded-md p-4">
          <div className="flex items-center gap-2 mb-1">
            <Activity size={14} className="text-amber" />
            <span className="text-[10px] uppercase tracking-widest text-ash font-medium">
              Active
            </span>
          </div>
          <p className="text-2xl font-semibold text-parchment">{activeCount}</p>
        </div>
        <div className="bg-graphite border border-slate rounded-md p-4">
          <div className="flex items-center gap-2 mb-1">
            <Film size={14} className="text-emerald" />
            <span className="text-[10px] uppercase tracking-widest text-ash font-medium">
              Completed
            </span>
          </div>
          <p className="text-2xl font-semibold text-parchment">
            {completedCount}
          </p>
        </div>
      </div>

      {/* Investigations list */}
      <div className="px-8 py-4">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-ash mb-3">
          Recent Investigations
        </h2>

        {loading && investigations.length === 0 && (
          <div className="text-sm text-mist py-8">Loading…</div>
        )}

        {error && (
          <div className="text-sm text-crimson py-4">
            Error: {error}. Make sure the API server is running.
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          {investigations.map((inv) => (
            <InvestigationCard key={inv.id} investigation={inv} />
          ))}
        </div>

        {investigations.length === 0 && !loading && !error && (
          <div className="bg-graphite border border-slate border-dashed rounded-md p-8 text-center">
            <Film size={24} className="text-ash mx-auto mb-2" />
            <p className="text-sm text-mist">No investigations yet</p>
            <p className="text-xs text-ash mt-1">
              Create your first assessment to get started
            </p>
            <button
              onClick={() => setShowModal(true)}
              className="mt-3 text-xs text-gold hover:underline"
            >
              Create Investigation →
            </button>
          </div>
        )}
      </div>

      {showModal && (
        <CreateInvestigationModal
          onClose={() => setShowModal(false)}
          onCreate={handleCreate}
        />
      )}
    </div>
  );
}
