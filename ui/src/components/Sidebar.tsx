import { useNavigate, useLocation } from "react-router-dom";
import { Film, Search, User, Settings, Plus, ChevronRight, BookOpen, BookOpenText, Network } from "lucide-react";
import type { Investigation } from "../types";

interface SidebarProps {
  investigations: Investigation[];
  onCreate: () => void;
}

export function Sidebar({ investigations, onCreate }: SidebarProps) {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <aside className="w-60 h-full bg-slate border-r border-graphite flex flex-col shrink-0">
      {/* Brand */}
      <div className="px-4 py-4 border-b border-graphite">
        <div className="flex items-center gap-2 text-gold">
          <Film size={20} strokeWidth={1.5} />
          <span className="text-sm font-semibold tracking-wide">ORACLE</span>
        </div>
        <p className="text-[10px] text-mist mt-1 uppercase tracking-widest">
          Actor Intelligence
        </p>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-2">
        <button
          onClick={onCreate}
          className="mx-3 mb-3 w-[calc(100%-24px)] flex items-center justify-center gap-2 bg-gold text-obsidian py-2 px-4 text-xs font-medium uppercase tracking-wider rounded-sm hover:brightness-110 transition-all duration-150"
        >
          <Plus size={14} />
          New Investigation
        </button>

        <div className="px-3 py-2">
          <p className="text-[10px] text-ash uppercase tracking-widest mb-2 font-medium">
            Investigations
          </p>
          {investigations.length === 0 && (
            <p className="text-xs text-mist px-2 py-1">No investigations yet</p>
          )}
          {investigations.map((inv) => (
            <button
              key={inv.id}
              onClick={() => navigate(`/investigation/${inv.id}`)}
              className={`w-full text-left px-2 py-1.5 rounded-sm text-xs mb-0.5 flex items-center justify-between group transition-colors duration-150 ${
                isActive(`/investigation/${inv.id}`)
                  ? "bg-graphite text-gold border-l-2 border-gold"
                  : "text-mist hover:text-parchment hover:bg-graphite/50"
              }`}
            >
              <span className="truncate">{inv.actor}</span>
              <ChevronRight
                size={12}
                className="opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
              />
            </button>
          ))}
        </div>

        <div className="px-3 py-2 mt-2 border-t border-graphite">
          <p className="text-[10px] text-ash uppercase tracking-widest mb-2 font-medium">
            Library
          </p>
          <button
            onClick={() => navigate("/")}
            className={`w-full text-left px-2 py-1.5 rounded-sm text-xs mb-0.5 flex items-center gap-2 transition-colors duration-150 ${
              isActive("/")
                ? "bg-graphite text-gold border-l-2 border-gold"
                : "text-mist hover:text-parchment hover:bg-graphite/50"
            }`}
          >
            <Search size={13} />
            Dashboard
          </button>
          <button
            onClick={() => navigate("/actors")}
            className={`w-full text-left px-2 py-1.5 rounded-sm text-xs mb-0.5 flex items-center gap-2 transition-colors duration-150 ${
              isActive("/actors")
                ? "bg-graphite text-gold border-l-2 border-gold"
                : "text-mist hover:text-parchment hover:bg-graphite/50"
            }`}
          >
            <User size={13} />
            Actors
          </button>
          <button
            onClick={() => navigate("/wiki")}
            className={`w-full text-left px-2 py-1.5 rounded-sm text-xs mb-0.5 flex items-center gap-2 transition-colors duration-150 ${
              isActive("/wiki")
                ? "bg-graphite text-gold border-l-2 border-gold"
                : "text-mist hover:text-parchment hover:bg-graphite/50"
            }`}
          >
            <BookOpenText size={13} />
            Wiki
          </button>
          <button
            onClick={() => navigate("/knowledge")}
            className={`w-full text-left px-2 py-1.5 rounded-sm text-xs mb-0.5 flex items-center gap-2 transition-colors duration-150 ${
              isActive("/knowledge")
                ? "bg-graphite text-gold border-l-2 border-gold"
                : "text-mist hover:text-parchment hover:bg-graphite/50"
            }`}
          >
            <Network size={13} />
            Knowledge
          </button>
          <button
            onClick={() => navigate("/skills")}
            className={`w-full text-left px-2 py-1.5 rounded-sm text-xs mb-0.5 flex items-center gap-2 transition-colors duration-150 ${
              isActive("/skills")
                ? "bg-graphite text-gold border-l-2 border-gold"
                : "text-mist hover:text-parchment hover:bg-graphite/50"
            }`}
          >
            <BookOpen size={13} />
            Skills
          </button>
        </div>
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-graphite">
        <div className="flex items-center gap-2 text-mist">
          <Settings size={14} />
          <span className="text-xs">Settings</span>
        </div>
        <p className="text-[10px] text-ash mt-2">
          Dmytr can make mistakes. Verify important judgments.
        </p>
      </div>
    </aside>
  );
}
