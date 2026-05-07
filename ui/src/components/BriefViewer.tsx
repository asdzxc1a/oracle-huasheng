import ReactMarkdown from "react-markdown";

interface BriefViewerProps {
  content: string;
}

export function BriefViewer({ content }: BriefViewerProps) {
  return (
    <div className="h-full overflow-y-auto px-6 py-6">
      <div className="w-full markdown-body">
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
    </div>
  );
}
