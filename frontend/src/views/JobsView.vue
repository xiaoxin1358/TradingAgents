<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useJobsStore } from "../stores/jobs";
import { fetchJob } from "../api/jobs";
import type { Job, JobType } from "../api/types";

const store = useJobsStore();

const today = new Date().toISOString().slice(0, 10);
const jobType = ref<JobType>("daily");
const date = ref(today);
const ticker = ref("SPY");
const preDate = ref("");
const error = ref("");
const starting = ref(false);
const doneTip = ref("");

const logPanel = ref<HTMLElement | null>(null);

const typeCards = [
  { value: "daily" as const, icon: "📄", label: "研报阅读", desc: "5 类研报 + 矛盾分析,产出 7 份报告" },
  { value: "pre" as const, icon: "🧭", label: "板块轮动", desc: "周期/成长/防御三路预分析" },
  { value: "trading" as const, icon: "📈", label: "交易分析", desc: "多 Agent 辩论决策(待 CLI 参数化)" },
];

const running = computed(() => store.running);

const statusMeta: Record<string, { label: string; cls: string }> = {
  running: { label: "运行中", cls: "running" },
  done: { label: "成功", cls: "done" },
  failed: { label: "失败", cls: "failed" },
  cancelled: { label: "已取消", cls: "cancelled" },
  interrupted: { label: "中断", cls: "interrupted" },
};

const typeLabel: Record<string, string> = {
  daily: "研报阅读",
  pre: "板块轮动",
  trading: "交易分析",
};

function paramsSummary(job: Job): string {
  const p = job.params ?? {};
  if (job.type === "daily") return p.date ?? "?";
  if (job.type === "pre") return `${p.ticker ?? "?"}${p.date ? " · " + p.date : ""}`;
  return "—";
}

function fmtTime(ts: number | null | undefined): string {
  if (!ts) return "—";
  const d = new Date(ts * 1000);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

function duration(job: Job): string {
  if (!job.finished_at) return "—";
  const s = Math.round(job.finished_at - job.created_at);
  return `${Math.floor(s / 60)}m${String(s % 60).padStart(2, "0")}s`;
}

async function start() {
  error.value = "";
  doneTip.value = "";
  starting.value = true;
  try {
    const params: Record<string, string> =
      jobType.value === "daily"
        ? { date: date.value }
        : { ticker: ticker.value, ...(preDate.value ? { date: preDate.value } : {}) };
    await store.start(jobType.value, params);
  } catch (e) {
    error.value = String(e);
  } finally {
    starting.value = false;
  }
}

async function showLog(job: Job) {
  if (job.status === "running") {
    store.subscribe(job.id);
    return;
  }
  const fresh = await fetchJob(job.id);
  store.logJobId = job.id;
  store.logLines = fresh.log_tail ?? [];
}

watch(
  () => store.jobs,
  (jobs) => {
    const finished = jobs.find((j) => j.status === "done" && doneTip.value !== j.id);
    if (finished && running.value === null) {
      doneTip.value = finished.id;
      setTimeout(() => {
        if (doneTip.value === finished.id) doneTip.value = "";
      }, 15000);
    }
  },
  { deep: true },
);

watch(
  () => store.logLines,
  () => {
    if (logPanel.value) {
      logPanel.value.scrollTop = logPanel.value.scrollHeight;
    }
  },
  { deep: true },
);

onMounted(async () => {
  try {
    await store.load();
    if (store.running) store.subscribe(store.running.id);
  } catch (e) {
    error.value = String(e);
  }
});

onBeforeUnmount(() => store.unsubscribe());
</script>

<template>
  <div class="jobs-layout">
    <section class="card form-card">
      <h3 class="card-title">新建任务</h3>
      <div class="type-cards">
        <button
          v-for="c in typeCards"
          :key="c.value"
          class="type-card"
          :class="{ active: jobType === c.value, disabled: c.value === 'trading' }"
          :disabled="c.value === 'trading'"
          @click="jobType = c.value"
        >
          <span class="type-icon">{{ c.icon }}</span>
          <span class="type-label">{{ c.label }}</span>
          <span class="type-desc">{{ c.desc }}</span>
          <span v-if="c.value === 'trading'" class="soon">即将开放</span>
        </button>
      </div>

      <div class="form-row">
        <template v-if="jobType === 'daily'">
          <label class="field">
            <span class="field-label">日期</span>
            <input v-model="date" class="input mono" placeholder="YYYY-MM-DD" />
          </label>
        </template>
        <template v-else-if="jobType === 'pre'">
          <label class="field">
            <span class="field-label">标的</span>
            <input v-model="ticker" class="input mono" placeholder="SPY" />
          </label>
          <label class="field">
            <span class="field-label">日期(可选)</span>
            <input v-model="preDate" class="input mono" placeholder="YYYY-MM-DD" />
          </label>
        </template>
      </div>

      <div class="form-foot">
        <span v-if="error" class="err">{{ error }}</span>
        <button
          class="btn primary"
          :disabled="starting || !!running || jobType === 'trading'"
          @click="start"
        >
          {{ running ? "任务运行中…" : starting ? "启动中…" : "▶ 开始运行" }}
        </button>
      </div>
    </section>

    <section v-if="running || store.logJobId" class="card log-card">
      <div class="log-head">
        <h3 class="card-title">
          任务日志
          <span class="mono dim">#{{ store.logJobId }}</span>
          <span v-if="running" class="badge accent">
            {{ typeLabel[running.type] }} · {{ paramsSummary(running) }}
          </span>
          <span v-if="store.subscribing" class="dot running"></span>
        </h3>
        <button v-if="running" class="btn" @click="store.cancel(running.id)">取消</button>
      </div>
      <div ref="logPanel" class="log-panel mono">
        <div v-for="(line, i) in store.logLines" :key="i" class="log-line">{{ line }}</div>
        <div v-if="store.logLines.length === 0" class="dim">等待输出…</div>
      </div>
    </section>

    <section class="card hist-card">
      <h3 class="card-title">历史任务</h3>
      <table class="table">
        <thead>
          <tr>
            <th>类型</th>
            <th>参数</th>
            <th>开始</th>
            <th>结束</th>
            <th>耗时</th>
            <th>状态</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="j in store.jobs" :key="j.id">
            <td>{{ typeLabel[j.type] ?? j.type }}</td>
            <td class="mono">{{ paramsSummary(j) }}</td>
            <td class="mono dim">{{ fmtTime(j.created_at) }}</td>
            <td class="mono dim">{{ fmtTime(j.finished_at) }}</td>
            <td class="mono dim">{{ duration(j) }}</td>
            <td>
              <span class="badge" :class="statusMeta[j.status]?.cls ?? 'flat'">
                {{ statusMeta[j.status]?.label ?? j.status }}
              </span>
            </td>
            <td><button class="btn small" @click="showLog(j)">日志</button></td>
          </tr>
        </tbody>
      </table>
      <div v-if="!store.jobs.length" class="empty">
        <div class="icon">▶</div>
        还没有运行过任务
      </div>
    </section>

    <Transition name="page">
      <div v-if="doneTip" class="card done-tip">
        ✅ 任务完成!
        <RouterLink to="/reports/daily" class="btn"> 去浏览报告 </RouterLink>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.jobs-layout {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 16px;
  align-items: start;
}

.form-card {
  grid-row: span 2;
}

.hist-card {
  overflow-x: auto;
}

.type-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.type-card {
  display: grid;
  grid-template-columns: 26px 1fr;
  gap: 2px 10px;
  text-align: left;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 12px 14px;
  cursor: pointer;
  color: var(--text-1);
  position: relative;
  transition: border-color 140ms ease-out, box-shadow 140ms ease-out, transform 140ms ease-out;
}

.type-card:hover:not(.disabled) {
  transform: translateY(-1px);
}

.type-card.active {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgb(79 140 255 / 0.15);
}

.type-card.disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.type-icon {
  grid-row: span 2;
  font-size: 18px;
  align-self: center;
}

.type-label {
  font-weight: 600;
  font-size: 13.5px;
}

.type-desc {
  font-size: 12px;
  color: var(--text-3);
}

.soon {
  position: absolute;
  top: 8px;
  right: 10px;
  font-size: 10px;
  color: var(--warn);
  border: 1px solid rgb(245 158 11 / 0.4);
  border-radius: 999px;
  padding: 0 7px;
}

.form-row {
  display: flex;
  gap: 10px;
  margin-bottom: 14px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.field-label {
  font-size: 12px;
  color: var(--text-3);
}

.form-foot {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

.err {
  color: var(--up);
  font-size: 12.5px;
  flex: 1;
}

.log-card {
  overflow: hidden;
}

.log-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.log-head .card-title {
  margin-bottom: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.log-panel {
  margin-top: 12px;
  background: #07090d;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 12px 14px;
  height: 260px;
  overflow-y: auto;
  font-size: 12px;
  line-height: 1.65;
  color: #9fe3a8;
  white-space: pre-wrap;
  word-break: break-all;
}

.log-line {
  min-height: 1em;
}

.dim {
  color: var(--text-3);
}

.btn.small {
  padding: 3px 10px;
  font-size: 12px;
}

.done-tip {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  border-color: rgb(34 197 94 / 0.4);
}

.badge.running {
  background: rgb(79 140 255 / 0.14);
  color: var(--accent);
}

.badge.done {
  background: rgb(34 197 94 / 0.14);
  color: var(--down);
}

.badge.failed {
  background: rgb(239 68 68 / 0.14);
  color: var(--up);
}

.badge.cancelled,
.badge.interrupted {
  background: rgb(139 147 167 / 0.16);
  color: var(--flat);
}

@media (max-width: 900px) {
  .jobs-layout {
    grid-template-columns: 1fr;
  }
}
</style>
