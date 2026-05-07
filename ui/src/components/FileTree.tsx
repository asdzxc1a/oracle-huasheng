import { FileText, Folder, ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";
import type { InvestigationFile } from "../types";

interface FileTreeProps {
  files: InvestigationFile[];
  selectedPath: string | null | undefined;
  onSelect: (path: string) => void;
}

interface TreeNode {
  name: string;
  path: string;
  children: TreeNode[];
  isFile: boolean;
}

function buildTree(files: InvestigationFile[]): TreeNode[] {
  const root: TreeNode[] = [];
  const map = new Map<string, TreeNode>();

  for (const file of files) {
    const parts = file.path.split("/");
    let currentPath = "";
    let currentLevel = root;

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      currentPath = currentPath ? `${currentPath}/${part}` : part;
      const isFile = i === parts.length - 1;

      let node = map.get(currentPath);
      if (!node) {
        node = { name: part, path: currentPath, children: [], isFile };
        map.set(currentPath, node);
        currentLevel.push(node);
        currentLevel.sort((a, b) => {
          if (a.isFile === b.isFile) return a.name.localeCompare(b.name);
          return a.isFile ? 1 : -1;
        });
      }
      currentLevel = node.children;
    }
  }

  return root;
}

function TreeItem({
  node,
  selectedPath,
  onSelect,
  depth = 0,
}: {
  node: TreeNode;
  selectedPath: string | null | undefined;
  onSelect: (path: string) => void;
  depth?: number;
}) {
  const [expanded, setExpanded] = useState(depth < 2);
  const isSelected = selectedPath === node.path;

  if (node.isFile) {
    return (
      <button
        onClick={() => onSelect(node.path)}
        className={`w-full text-left flex items-center gap-1.5 py-1 px-2 text-xs rounded-sm transition-colors duration-150 ${
          isSelected
            ? "bg-gold/15 text-gold"
            : "text-mist hover:text-parchment hover:bg-slate/50"
        }`}
        style={{ paddingLeft: `${8 + depth * 12}px` }}
      >
        <FileText size={12} className="shrink-0" />
        <span className="truncate">{node.name}</span>
      </button>
    );
  }

  return (
    <div>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left flex items-center gap-1 py-1 px-2 text-xs text-ash hover:text-parchment transition-colors"
        style={{ paddingLeft: `${8 + depth * 12}px` }}
      >
        {expanded ? (
          <ChevronDown size={12} className="shrink-0" />
        ) : (
          <ChevronRight size={12} className="shrink-0" />
        )}
        <Folder size={12} className="shrink-0" />
        <span className="truncate font-medium">{node.name}</span>
      </button>
      {expanded && (
        <div>
          {node.children.map((child) => (
            <TreeItem
              key={child.path}
              node={child}
              selectedPath={selectedPath}
              onSelect={onSelect}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function FileTree({ files, selectedPath, onSelect }: FileTreeProps) {
  const tree = buildTree(files);

  return (
    <div className="h-full overflow-y-auto">
      <div className="px-3 py-2 border-b border-slate">
        <span className="text-[10px] uppercase tracking-widest text-ash font-medium">
          Files
        </span>
      </div>
      <div className="py-1">
        {tree.map((node) => (
          <TreeItem
            key={node.path}
            node={node}
            selectedPath={selectedPath}
            onSelect={onSelect}
          />
        ))}
      </div>
    </div>
  );
}
