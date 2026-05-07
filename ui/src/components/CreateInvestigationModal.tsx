import { useState } from "react";
import { X, Film } from "lucide-react";

interface CreateInvestigationModalProps {
  onClose: () => void;
  onCreate: (actor: string, question: string, initialRead: string) => void;
}

export function CreateInvestigationModal({
  onClose,
  onCreate,
}: CreateInvestigationModalProps) {
  const [actor, setActor] = useState("");
  const [question, setQuestion] = useState("");
  const [initialRead, setInitialRead] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!actor.trim() || !question.trim()) return;
    setSubmitting(true);
    try {
      await onCreate(actor.trim(), question.trim(), initialRead.trim());
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-obsidian/80 backdrop-blur-sm">
      <div className="bg-graphite border border-slate rounded-lg w-full max-w-lg mx-4 shadow-lg animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate">
          <div className="flex items-center gap-2">
            <Film size={18} className="text-gold" />
            <h2 className="text-sm font-semibold text-parchment">
              New Investigation
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-ash hover:text-parchment transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-5 py-4 space-y-4">
          <div>
            <label className="block text-[10px] uppercase tracking-widest text-ash font-medium mb-1.5">
              Actor Name
            </label>
            <input
              type="text"
              value={actor}
              onChange={(e) => setActor(e.target.value)}
              placeholder="e.g. Zendaya"
              required
              className="w-full bg-slate border border-slate rounded-sm py-2 px-3 text-sm text-parchment placeholder:text-ash focus:outline-none focus:border-gold focus:ring-1 focus:ring-gold/30 transition-all"
            />
          </div>

          <div>
            <label className="block text-[10px] uppercase tracking-widest text-ash font-medium mb-1.5">
              Client Question
            </label>
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. Can she carry a $25M non-franchise drama lead?"
              required
              className="w-full bg-slate border border-slate rounded-sm py-2 px-3 text-sm text-parchment placeholder:text-ash focus:outline-none focus:border-gold focus:ring-1 focus:ring-gold/30 transition-all"
            />
          </div>

          <div>
            <label className="block text-[10px] uppercase tracking-widest text-ash font-medium mb-1.5">
              Your Initial Read (Optional)
            </label>
            <textarea
              value={initialRead}
              onChange={(e) => setInitialRead(e.target.value)}
              placeholder="What is your gut instinct about this actor?"
              rows={3}
              className="w-full bg-slate border border-slate rounded-sm py-2 px-3 text-sm text-parchment placeholder:text-ash focus:outline-none focus:border-gold focus:ring-1 focus:ring-gold/30 transition-all resize-none"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs text-mist hover:text-parchment transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || !actor.trim() || !question.trim()}
              className="px-5 py-2 bg-gold text-obsidian text-xs font-medium uppercase tracking-wider rounded-sm hover:brightness-110 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
            >
              {submitting ? "Creating…" : "Create Investigation"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
