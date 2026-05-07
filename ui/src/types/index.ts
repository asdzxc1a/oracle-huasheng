export interface Investigation {
  id: string;
  actor: string;
  client_question: string;
  human_initial_read: string;
  status: string;
  pipeline: Record<string, Record<string, string>>;
  agents_completed: string[];
  agents_pending: string[];
  agents_failed: string[];
  human_actions_required: string[];
  created_at: string;
  updated_at: string;
}

export interface InvestigationFile {
  path: string;
  size: number;
}

export interface InvestigationDetail {
  manifest: Investigation;
  files: InvestigationFile[];
}

export interface AgentInfo {
  name: string;
  version: string;
}

export interface JobStatus {
  job_id: string;
  status: string;
  success?: boolean;
  agent?: string;
  result?: Record<string, unknown>;
  error?: string;
}

export type PipelineStage =
  | "truth"
  | "readiness"
  | "presence"
  | "proof"
  | "deployment";
