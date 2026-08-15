import { get, enc } from "./http";
import type { Job, JobType } from "./types";

export const fetchJobs = () => get<{ jobs: Job[] }>("/api/jobs");

export const fetchJob = (id: string) => get<Job>(`/api/jobs/${enc(id)}`);

export async function createJob(type: JobType, params: Record<string, string>): Promise<Job> {
  const res = await fetch("/api/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ type, params }),
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* keep status text */
    }
    throw new Error(detail);
  }
  return (await res.json()) as Job;
}

export async function cancelJob(id: string): Promise<Job> {
  const res = await fetch(`/api/jobs/${enc(id)}/cancel`, { method: "POST" });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return (await res.json()) as Job;
}

/**
 * Subscribe to a job's SSE stream. Returns a close function.
 * onLog: log line; onStatus: final job object.
 * NOTE: EventSource auto-reconnects when the stream ends; we close it in
 * onStatus (terminal state) so a finished job's log isn't replayed forever.
 */
export function subscribeJobEvents(
  id: string,
  handlers: { onLog?: (line: string) => void; onStatus?: (job: Job) => void },
): () => void {
  const es = new EventSource(`/api/jobs/${enc(id)}/events`);
  let closed = false;
  const close = () => {
    closed = true;
    es.close();
  };
  es.addEventListener("log", (ev: MessageEvent) => {
    try {
      handlers.onLog?.(String(JSON.parse(ev.data).line ?? ""));
    } catch {
      /* malformed frame */
    }
  });
  es.addEventListener("status", (ev: MessageEvent) => {
    try {
      handlers.onStatus?.(JSON.parse(ev.data) as Job);
    } catch {
      /* malformed frame */
    }
    close(); // terminal: stop auto-reconnect replaying the log
  });
  es.onerror = () => {
    if (closed) return;
  };
  return close;
}
