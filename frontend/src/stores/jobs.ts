import { defineStore } from "pinia";
import { cancelJob, createJob, fetchJobs, subscribeJobEvents } from "../api/jobs";
import type { Job, JobType } from "../api/types";

interface State {
  jobs: Job[];
  logLines: string[];
  logJobId: string | null;
  subscribing: boolean;
}

let closeEvents: (() => void) | null = null;

export const useJobsStore = defineStore("jobs", {
  state: (): State => ({
    jobs: [],
    logLines: [],
    logJobId: null,
    subscribing: false,
  }),
  getters: {
    running(state): Job | null {
      return state.jobs.find((j) => j.status === "running") ?? null;
    },
  },
  actions: {
    async load() {
      this.jobs = (await fetchJobs()).jobs;
    },
    async start(type: JobType, params: Record<string, string>) {
      const job = await createJob(type, params);
      this.jobs = [job, ...this.jobs.filter((j) => j.id !== job.id)];
      this.subscribe(job.id); // fire-and-forget; logs stream until the job ends
      return job;
    },
    async cancel(id: string) {
      const job = await cancelJob(id);
      const i = this.jobs.findIndex((j) => j.id === id);
      if (i >= 0) this.jobs[i] = job;
      return job;
    },
    /** Subscribe to SSE for a running job; resumes on page revisit.
     *  Idempotent per job: repeat calls for the same id reuse the stream. */
    subscribe(id: string): void {
      if (this.logJobId === id && closeEvents) return;
      if (closeEvents) closeEvents();
      closeEvents = null;
      if (this.logJobId !== id) {
        this.logLines = [];
        this.logJobId = id;
      }
      this.subscribing = true;
      closeEvents = subscribeJobEvents(id, {
        onLog: (line) => {
          this.logLines.push(line);
          if (this.logLines.length > 500) this.logLines.shift(); // bounded
        },
        onStatus: (job) => {
          const i = this.jobs.findIndex((j) => j.id === job.id);
          if (i >= 0) this.jobs[i] = job;
          else this.jobs.unshift(job);
          this.subscribing = false;
        },
      });
    },
    unsubscribe() {
      if (closeEvents) {
        closeEvents();
        closeEvents = null;
      }
      this.subscribing = false;
    },
  },
});
