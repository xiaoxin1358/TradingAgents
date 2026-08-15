<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { fetchTradingFile, fetchTradingRuns } from "../api";
import type { RunInfo } from "../api/types";
import MarkdownViewer from "../components/MarkdownViewer.vue";

const runs = ref<RunInfo[]>([]);
const activeRun = ref<string>("");
const activeFile = ref<string>("complete_report.md");
const content = ref("");
const loading = ref(false);
const error = ref("");

const stages = [
  { key: "1_analysts", label: "分析师", icon: "🔍" },
  { key: "2_research", label: "研究辩论", icon: "⚔" },
  { key: "3_trading", label: "交易", icon: "📊" },
  { key: "4_risk", label: "风险", icon: "🛡" },
  { key: "5_portfolio", label: "决策", icon: "🎯" },
];

const currentRun = computed(() =>
  runs.value.find((r) => r.id === activeRun.value),
);

const tabs = computed(() => {
  const r = currentRun.value;
  if (!r) return [];
  return r.files.map((f) => ({ path: f, label: f.split("/").pop() ?? f }));
});

function stageFiles(stageKey: string): string[] {
  return (
    currentRun.value?.files.filter((f) => f.startsWith(stageKey + "/")) ?? []
  );
}

function stageState(stageKey: string): "done" | "empty" {
  return stageFiles(stageKey).length ? "done" : "empty";
}

async function openFile(path: string) {
  if (!activeRun.value) return;
  activeFile.value = path;
  loading.value = true;
  error.value = "";
  try {
    const res = await fetchTradingFile(activeRun.value, path);
    content.value = res.content;
  } catch (e) {
    error.value = String(e);
  } finally {
    loading.value = false;
  }
}

watch(activeRun, () => {
  activeFile.value = "complete_report.md";
  openFile(activeFile.value);
});

onMounted(async () => {
  try {
    runs.value = (await fetchTradingRuns()).runs;
    if (runs.value.length) {
      activeRun.value = runs.value[0].id;
    }
  } catch (e) {
    error.value = String(e);
  }
});
</script>

<template>
  <div class="layout">
    <aside class="card run-list">
      <h3 class="card-title">运行列表</h3>
      <div
        v-for="r in runs"
        :key="r.id"
        class="run-item"
        :class="{ active: r.id === activeRun }"
        @click="activeRun = r.id"
      >
        <span class="mono">{{ r.id }}</span>
        <span class="count mono">{{ r.files.length }} 文件</span>
      </div>
      <div v-if="!runs.length" class="empty">
        <div class="icon">📂</div>
        暂无交易分析运行产物
      </div>
    </aside>

    <section class="reader">
      <div class="stepper">
        <div
          v-for="(s, i) in stages"
          :key="s.key"
          class="step"
          :class="stageState(s.key)"
          @click="stageFiles(s.key)[0] && openFile(stageFiles(s.key)[0])"
        >
          <span class="step-icon">{{ s.icon }}</span>
          <span class="step-label">{{ s.label }}</span>
          <span v-if="i < stages.length - 1" class="step-line"></span>
        </div>
      </div>

      <div class="card reader-card">
        <div class="tabs">
          <button
            v-for="t in tabs"
            :key="t.path"
            class="tab"
            :class="{ active: t.path === activeFile }"
            @click="openFile(t.path)"
          >
            {{ t.label }}
          </button>
        </div>
        <div v-if="loading" class="skeleton" style="height: 300px"></div>
        <div v-else-if="error" class="empty">{{ error }}</div>
        <div v-else-if="!activeRun" class="empty">选择一个运行查看报告</div>
        <MarkdownViewer v-else :content="content" />
      </div>
    </section>
  </div>
</template>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 16px;
  align-items: start;
}

.run-list {
  padding: 14px;
}

.run-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 9px 10px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 12.5px;
  border-left: 2px solid transparent;
  transition: background 140ms ease-out;
}

.run-item:hover {
  background: var(--bg-hover);
}

.run-item.active {
  background: var(--bg-hover);
  border-left-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
}

.count {
  color: var(--text-3);
  font-size: 11px;
}

.reader {
  min-width: 0;
}

.stepper {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  margin-bottom: 14px;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex: 1;
  position: relative;
  cursor: pointer;
}

.step-icon {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  color: var(--text-3);
  font-size: 13px;
}

.step.done .step-icon {
  background: rgb(79 140 255 / 0.14);
  border-color: var(--accent);
  color: var(--accent);
}

.step-line {
  position: absolute;
  top: 15px;
  left: calc(50% + 18px);
  width: calc(100% - 36px);
  height: 1px;
  background: var(--border);
}

.step-label {
  font-size: 11.5px;
  color: var(--text-3);
}

.step.done .step-label {
  color: var(--accent);
}

.reader-card {
  padding: 18px 22px;
  min-height: 420px;
}

.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 16px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 10px;
}

.tab {
  background: none;
  border: none;
  color: var(--text-2);
  font-size: 13px;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition:
    color 140ms ease-out,
    background 140ms ease-out;
}

.tab:hover {
  color: var(--text-1);
  background: var(--bg-hover);
}

.tab.active {
  color: var(--accent);
  font-weight: 600;
  border-bottom: 2px solid var(--accent);
  border-radius: 0;
}

@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
