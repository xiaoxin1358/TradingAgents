// API response types (docs 2.3 + 6).

export interface DailyFileMeta {
  name: string;
  label: string;
  exists: boolean;
  size: number;
}

export interface DailyMeta {
  date: string;
  files: DailyFileMeta[];
}

export interface RunInfo {
  id: string;
  files: string[];
  mtime: number;
  kind?: "daily" | "trading" | "pre";
}

export interface Claim {
  broker?: string;
  subject?: string;
  direction?: number;
  quote?: string;
}

export interface Insight {
  cause_type?: string;
  cause?: string;
  analysis?: string;
  watch?: string;
  tilt?: string;
}

export interface ContradictionRow {
  id: string;
  subject: string;
  kind: string;
  scope: string;
  scale: string;
  claim_a: Claim;
  claim_b: Claim;
  status: string;
  winner?: string | null;
  resolved_by?: string | null;
  resolved_date?: string | null;
  first_seen: string;
  last_seen: string;
  insight: Insight | null;
  direction_a: string;
  direction_b: string;
  kind_cn: string;
  scope_cn: string;
  scale_cn: string;
  days_open: number | null;
}

export interface ContradictionList {
  rows: ContradictionRow[];
  total: number;
}

export interface ContradictionStats {
  total: number;
  open: number;
  resolved: number;
  resolve_rate: number;
  kind_dist: Record<string, number>;
  cause_dist: Record<string, number>;
  longest_open: number;
}

export interface Top5Row {
  id: string;
  subject: string;
  direction_a: string;
  direction_b: string;
  broker_a: string;
  broker_b: string;
  days_open: number | null;
  cause_type: string;
}

export interface Overview {
  stats: {
    daily_days: number;
    trading_runs: number;
    contradictions: ContradictionStats;
  };
  recent: RunInfo[];
  top5: Top5Row[];
}

export interface MemoryInfo {
  exists: boolean;
  path: string;
  content: string;
  mtime: number | null;
}

export interface Settings {
  groups: { label: string; items: { key: string; value: string }[] }[];
}

export interface FileContent {
  name?: string;
  path?: string;
  content: string;
}

// ── jobs (M2) ──

export type JobType = "daily" | "pre" | "trading" | "spider";
export type JobStatus =
  | "running"
  | "done"
  | "failed"
  | "cancelled"
  | "interrupted";

export interface Job {
  id: string;
  type: JobType;
  params: Record<string, string>;
  status: JobStatus;
  pid?: number | null;
  created_at: number;
  finished_at?: number | null;
  exit_code?: number | null;
  log_file: string;
  log_tail?: string[];
}

export interface JobEvent {
  line?: string;
  status?: string;
  error?: string;
}
