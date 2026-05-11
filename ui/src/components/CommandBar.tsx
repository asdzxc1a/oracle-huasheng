import { useState, useRef } from "react";
import { useCommands } from "../hooks/useCommands";

interface CommandBarProps {
  onInvestigationCreated?: (id: string) => void;
}

export function CommandBar({ onInvestigationCreated }: CommandBarProps) {
  const [input, setInput] = useState("");
  const [showHelp, setShowHelp] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const { runCommand, loading } = useCommands();

  const parseCommand = (text: string) => {
    const trimmed = text.trim();
    if (!trimmed.startsWith("/")) return null;

    const parts = trimmed.slice(1).split(/\s+--\s+|\s+—\s+/);
    const prefix = parts[0].split(/\s+/)[0].toLowerCase();
    const rest = parts[0].slice(prefix.length).trim();

    if (prefix === "assess") {
      const actorQuestion = rest.split(/\s+--\s+|\s+—\s+/);
      return {
        command: "assess" as const,
        payload: {
          actor: actorQuestion[0]?.trim() || rest,
          question: actorQuestion[1]?.trim() || "General assessment",
        },
      };
    }
    if (prefix === "harvest") {
      const actorFocus = rest.split(/\s+--\s+|\s+—\s+/);
      return {
        command: "harvest" as const,
        payload: {
          actor: actorFocus[0]?.trim() || rest,
          focus_areas: actorFocus[1] ? [actorFocus[1].trim()] : [],
        },
      };
    }
    if (prefix === "compare") {
      const match = rest.match(/(.+?)\s+vs\s+(.+)/i);
      if (match) {
        return {
          command: "compare" as const,
          payload: {
            actors: [match[1].trim(), match[2].trim()],
            question: "Comparison assessment",
          },
        };
      }
    }
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const parsed = parseCommand(input);
    if (!parsed) {
      setShowHelp(true);
      return;
    }

    const result = await runCommand(parsed.command, parsed.payload);
    if (result && onInvestigationCreated) {
      onInvestigationCreated(result.investigation_id);
    }
    setInput("");
    setShowHelp(false);
  };

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="relative flex items-center">
        <span className="absolute left-3 text-parchment/50 text-lg font-mono">&gt;</span>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onFocus={() => setShowHelp(true)}
          onBlur={() => setTimeout(() => setShowHelp(false), 200)}
          placeholder="/assess Zendaya — Can she carry a drama lead?"
          className="w-full bg-obsidian border border-parchment/20 rounded-lg py-3 pl-10 pr-4 text-parchment placeholder-parchment/30 focus:outline-none focus:border-parchment/50 font-mono text-sm"
          disabled={loading}
        />
        {loading && (
          <span className="absolute right-4 text-parchment/50 text-xs animate-pulse">
            Running...
          </span>
        )}
      </form>

      {showHelp && (
        <div className="mt-2 p-3 bg-obsidian border border-parchment/10 rounded-lg text-xs text-parchment/60 font-mono">
          <div className="mb-1 font-semibold text-parchment/80">Available commands:</div>
          <div>/assess [actor] — [question]</div>
          <div>/harvest [actor] — [focus areas]</div>
          <div>/compare [actor A] vs [actor B]</div>
        </div>
      )}
    </div>
  );
}
