import { get, enc } from "./http";
import type {
  ContradictionList,
  ContradictionRow,
  ContradictionStats,
  DailyMeta,
  FileContent,
  MemoryInfo,
  Overview,
  RunInfo,
  Settings,
} from "./types";

// ── overview ──

export const fetchOverview = () => get<Overview>("/api/overview");

// ── daily reports ──

export const fetchDates = () => get<{ dates: string[] }>("/api/dates");

export const fetchDailyMeta = (day: string) =>
  get<DailyMeta>(`/api/reports/${enc(day)}`);

export const fetchDailyFile = (day: string, name: string) =>
  get<FileContent>(`/api/reports/${enc(day)}/${enc(name)}`);

// ── run trees ──

export const fetchTradingRuns = () => get<{ runs: RunInfo[] }>("/api/trading-runs");

export const fetchTradingFile = (run: string, path: string) =>
  get<FileContent>(`/api/trading-runs/${enc(run)}/${path.split("/").map(enc).join("/")}`);

export const fetchPreRuns = () => get<{ runs: RunInfo[] }>("/api/pre-runs");

export const fetchPreFile = (run: string, path: string) =>
  get<FileContent>(`/api/pre-runs/${enc(run)}/${path.split("/").map(enc).join("/")}`);

// ── contradictions ──

export interface ContradictionFilters {
  status?: string;
  kind?: string;
  scope?: string;
  scale?: string;
  subject?: string;
  cause_type?: string;
  min_days?: number | null;
}

export function fetchContradictions(
  filters: ContradictionFilters,
  limit = 100,
  offset = 0,
): Promise<ContradictionList> {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(filters)) {
    if (v !== undefined && v !== null && v !== "") q.set(k, String(v));
  }
  q.set("limit", String(limit));
  q.set("offset", String(offset));
  return get<ContradictionList>(`/api/contradictions?${q.toString()}`);
}

export const fetchContradictionDetail = (id: string) =>
  get<ContradictionRow>(`/api/contradictions/${enc(id)}`);

export const fetchContradictionStats = () =>
  get<ContradictionStats>("/api/contradictions/stats");

// ── memory / settings ──

export const fetchMemory = () => get<MemoryInfo>("/api/memory");

export const fetchSettings = () => get<Settings>("/api/settings");
