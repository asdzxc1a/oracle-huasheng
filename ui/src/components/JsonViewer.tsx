import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

interface JsonViewerProps {
  data: any;
  level?: number;
}

export function JsonViewer({ data, level = 0 }: JsonViewerProps) {
  if (data === null) return <span className="text-ash">null</span>;
  if (typeof data === "boolean")
    return <span className="text-purple-400">{data ? "true" : "false"}</span>;
  if (typeof data === "number")
    return <span className="text-orange-300">{data}</span>;
  if (typeof data === "string")
    return <span className="text-green-300">"{data}"</span>;

  if (Array.isArray(data)) {
    if (data.length === 0)
      return <span className="text-ash">[]</span>;
    return <ArrayViewer items={data} level={level} />;
  }

  if (typeof data === "object") {
    const keys = Object.keys(data);
    if (keys.length === 0)
      return <span className="text-ash">{"{}"}</span>;
    return <ObjectViewer obj={data} level={level} />;
  }

  return <span>{String(data)}</span>;
}

function ArrayViewer({ items, level }: { items: any[]; level: number }) {
  const [expanded, setExpanded] = useState(level < 2);

  if (!expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="flex items-center gap-1 text-ash hover:text-parchment"
      >
        <ChevronRight size={12} />
        <span>[{items.length} items]</span>
      </button>
    );
  }

  return (
    <div>
      <button
        onClick={() => setExpanded(false)}
        className="flex items-center gap-1 text-ash hover:text-parchment"
      >
        <ChevronDown size={12} />
        <span>[</span>
      </button>
      <div className="pl-4 border-l border-graphite">
        {items.map((item, i) => (
          <div key={i} className="flex gap-2">
            <span className="text-ash">{i}:</span>
            <JsonViewer data={item} level={level + 1} />
            {i < items.length - 1 && <span className="text-ash">,</span>}
          </div>
        ))}
      </div>
      <span className="text-ash">]</span>
    </div>
  );
}

function ObjectViewer({ obj, level }: { obj: Record<string, any>; level: number }) {
  const [expanded, setExpanded] = useState(level < 2);
  const keys = Object.keys(obj);

  if (!expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="flex items-center gap-1 text-ash hover:text-parchment"
      >
        <ChevronRight size={12} />
        <span>{`{${keys.length} keys}`}</span>
      </button>
    );
  }

  return (
    <div>
      <button
        onClick={() => setExpanded(false)}
        className="flex items-center gap-1 text-ash hover:text-parchment"
      >
        <ChevronDown size={12} />
        <span>{"{"}</span>
      </button>
      <div className="pl-4 border-l border-graphite">
        {keys.map((key, i) => (
          <div key={key} className="flex gap-2">
            <span className="text-blue-300">{key}</span>
            <span className="text-ash">:</span>
            <JsonViewer data={obj[key]} level={level + 1} />
            {i < keys.length - 1 && <span className="text-ash">,</span>}
          </div>
        ))}
      </div>
      <span className="text-ash">{"}"}</span>
    </div>
  );
}
