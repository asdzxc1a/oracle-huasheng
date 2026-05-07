import { useState } from "react";
import { Send, Mic } from "lucide-react";

interface ChatPanelProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatPanel({
  onSend,
  disabled = false,
  placeholder = "What are your instructions for the next agent?",
}: ChatPanelProps) {
  const [message, setMessage] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || disabled) return;
    onSend(message.trim());
    setMessage("");
  };

  return (
    <div className="border-t border-slate bg-graphite px-4 py-3">
      <form onSubmit={handleSubmit} className="flex items-end gap-2">
        <div className="flex-1 relative">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder={placeholder}
            disabled={disabled}
            className="w-full bg-slate border border-slate rounded-sm py-2.5 px-3 pr-10 text-sm text-parchment placeholder:text-ash focus:outline-none focus:border-gold focus:ring-1 focus:ring-gold/30 transition-all duration-150 disabled:opacity-50"
          />
          <button
            type="button"
            className="absolute right-2 top-1/2 -translate-y-1/2 text-ash hover:text-parchment transition-colors"
          >
            <Mic size={16} />
          </button>
        </div>
        <button
          type="submit"
          disabled={disabled || !message.trim()}
          className="bg-gold text-obsidian p-2.5 rounded-sm hover:brightness-110 transition-all duration-150 disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <Send size={16} />
        </button>
      </form>
      <p className="text-[10px] text-ash mt-2">
        Dmytr can make mistakes. Verify important judgments.
      </p>
    </div>
  );
}
