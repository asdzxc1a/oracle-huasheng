import { useState } from "react";
import { BookOpen, Search, FileText } from "lucide-react";
import { useWikiPages, useWikiPage } from "../hooks/useWiki";
import ReactMarkdown from "react-markdown";

export function WikiBrowser() {
  const { pages, loading } = useWikiPages();
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<string | null>(null);


  const filtered = pages.filter((p) =>
    p.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="h-full flex flex-col bg-obsidian text-parchment">
      {/* Header */}
      <div className="px-6 py-4 border-b border-graphite flex items-center justify-between">
        <div className="flex items-center gap-3">
          <BookOpen size={20} className="text-gold" />
          <div>
            <h1 className="text-lg font-semibold">Actor Wiki</h1>
            <p className="text-xs text-mist">
              Living documents editable by producers
            </p>
          </div>
        </div>
        <div className="relative">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ash" />
          <input
            type="text"
            placeholder="Search actors..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-slate border border-graphite rounded-sm pl-8 pr-3 py-1.5 text-xs w-56 focus:outline-none focus:border-gold transition-colors"
          />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Page list */}
        <div className="w-64 border-r border-graphite overflow-y-auto">
          {loading && (
            <p className="text-xs text-mist p-4">Loading...</p>
          )}
          {filtered.length === 0 && !loading && (
            <p className="text-xs text-mist p-4">No wiki pages yet</p>
          )}
          {filtered.map((page) => (
            <button
              key={page.actor_slug}
              onClick={() => setSelected(page.actor_slug)}
              className={`w-full text-left px-4 py-2.5 border-b border-graphite/50 text-xs transition-colors ${
                selected === page.actor_slug
                  ? "bg-graphite text-gold"
                  : "text-mist hover:text-parchment hover:bg-graphite/30"
              }`}
            >
              <div className="flex items-center gap-2">
                <FileText size={12} />
                <span className="font-medium truncate">{page.title}</span>
              </div>
              <p className="text-[10px] text-ash mt-0.5">
                Updated {new Date(page.updated * 1000).toLocaleDateString()}
              </p>
            </button>
          ))}
        </div>

        {/* Preview */}
        <div className="flex-1 overflow-y-auto p-6">
          {selected ? (
            <WikiPreview actorSlug={selected} />
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-mist">
              <BookOpen size={48} className="mb-4 opacity-30" />
              <p className="text-sm">Select an actor to view their wiki</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function WikiPreview({ actorSlug }: { actorSlug: string }) {
  const { page, loading } = useWikiPage(actorSlug);

  if (loading) return <p className="text-mist text-sm">Loading...</p>;
  if (!page) return <p className="text-mist text-sm">Page not found</p>;

  return (
    <div className="max-w-3xl mx-auto">
      <h2 className="text-xl font-semibold mb-4">{page.title}</h2>
      <div className="prose prose-invert prose-sm max-w-none">
        <ReactMarkdown>{page.content || "No content"}</ReactMarkdown>
      </div>
    </div>
  );
}
