import { useState, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
import { ArrowLeft, FileText, Loader2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Pipeline } from "../components/Pipeline";
import { FileTree } from "../components/FileTree";
import { BriefViewer } from "../components/BriefViewer";
import { ChatPanel } from "../components/ChatPanel";
import { useInvestigation } from "../hooks/useInvestigation";
import { useFile } from "../hooks/useFile";
import { useRunAgent } from "../hooks/useRunAgent";
import { JsonViewer } from "../components/JsonViewer";

export function InvestigationDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { detail, loading, refresh } = useInvestigation(id);
  const { runAgent, pollJob } = useRunAgent();
  const [selectedFile, setSelectedFile] = useState<string | undefined>(undefined);
  const [lastJobId, setLastJobId] = useState<string | undefined>(undefined);

  const { content: fileContent } = useFile(id, selectedFile);

  // Auto-select brief.md when investigation loads
  useEffect(() => {
    if (detail && !selectedFile) {
      const briefFile = detail.files.find((f) => f.path === "brief.md");
      if (briefFile) {
        setSelectedFile("brief.md");
      }
    }
  }, [detail, selectedFile]);

  // Poll for job completion
  useEffect(() => {
    if (!lastJobId) return;
    const interval = setInterval(async () => {
      try {
        const job = await pollJob(lastJobId);
        if (job.status !== "running") {
          setLastJobId(undefined);
          refresh();
        }
      } catch {
        setLastJobId(undefined);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [lastJobId, pollJob, refresh]);

  const handleRunAgent = useCallback(
    async (agentName: string) => {
      if (!id) return;
      try {
        const result = await runAgent(id, agentName);
        if (result.job_id) {
          setLastJobId(result.job_id);
        }
      } catch (e) {
        console.error(e);
      }
    },
    [id, runAgent]
  );

  const handleSendMessage = useCallback(
    async (message: string) => {
      if (!id) return;
      const API_BASE = import.meta.env.VITE_API_URL || "";
      await fetch(`${API_BASE}/api/investigations/${id}/human`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ instructions: message }),
      });
      refresh();
    },
    [id, refresh]
  );

  if (loading && !detail) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 size={24} className="text-gold animate-spin" />
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <p className="text-sm text-mist">Investigation not found</p>
          <button
            onClick={() => navigate("/")}
            className="mt-2 text-xs text-gold hover:underline"
          >
            ← Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const manifest = detail.manifest;
  return (
    <div className="h-full flex flex-col">
      {/* Top bar */}
      <div className="shrink-0 px-6 py-3 border-b border-slate flex items-center gap-3">
        <button
          onClick={() => navigate("/")}
          className="text-ash hover:text-parchment transition-colors"
        >
          <ArrowLeft size={16} />
        </button>
        <div>
          <h1 className="text-sm font-semibold text-parchment">
            {manifest.actor}
          </h1>
          <p className="text-[11px] text-mist">{manifest.client_question}</p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          {manifest.human_actions_required.length > 0 && (
            <span className="text-[10px] uppercase tracking-wider px-2 py-1 bg-amber/15 text-amber rounded-sm font-medium">
              Human Review
            </span>
          )}
          <span
            className={`text-[10px] uppercase tracking-wider px-2 py-1 rounded-sm font-medium ${
              manifest.status.includes("completed")
                ? "bg-emerald/15 text-emerald"
                : manifest.status.includes("paused")
                ? "bg-amber/15 text-amber"
                : "bg-gold/15 text-gold"
            }`}
          >
            {manifest.status.replace(/_/g, " ")}
          </span>
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 flex min-h-0">
        {/* Pipeline sidebar */}
        <div className="shrink-0">
          <Pipeline
            investigation={manifest}
            onRunAgent={handleRunAgent}
          />
        </div>

        {/* File tree + content */}
        <div className="flex-1 flex min-h-0">
          {/* File tree */}
          <div className="w-56 shrink-0 border-r border-slate bg-graphite">
            <FileTree
              files={detail.files}
              selectedPath={selectedFile}
              onSelect={setSelectedFile}
            />
          </div>

          {/* Content viewer */}
          <div className="flex-1 flex flex-col min-h-0 bg-obsidian">
            {/* File path bar */}
            <div className="shrink-0 px-4 py-2 border-b border-slate flex items-center gap-2">
              <FileText size={12} className="text-ash" />
              <span className="text-[11px] text-mist font-mono">
                {selectedFile || "Select a file"}
              </span>
            </div>

            {/* File content */}
            <div className="flex-1 min-h-0 overflow-hidden">
              {selectedFile && fileContent !== null ? (
                selectedFile.endsWith(".md") ? (
                  <BriefViewer content={fileContent} />
                ) : selectedFile.endsWith(".json") ? (
                  <div className="h-full overflow-y-auto px-6 py-6">
                    <JsonViewer data={JSON.parse(fileContent || "{}")} />
                  </div>
                ) : (
                  <div className="h-full overflow-y-auto px-6 py-6">
                    <pre className="text-xs text-parchment font-mono whitespace-pre-wrap">
                      {fileContent}
                    </pre>
                  </div>
                )
              ) : (
                <div className="h-full flex items-center justify-center">
                  <p className="text-xs text-ash">
                    Select a file from the tree to view
                  </p>
                </div>
              )}
            </div>

            {/* Chat panel */}
            <ChatPanel
              onSend={handleSendMessage}
              placeholder="What are your instructions for the next agent?"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
