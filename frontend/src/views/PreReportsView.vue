<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { fetchPreFile, fetchPreRuns } from "../api";
import type { RunInfo } from "../api/types";
import MarkdownViewer from "../components/MarkdownViewer.vue";

const runs = ref<RunInfo[]>([]);
const activeRun = ref<string>("");
const activeFile = ref<string>("complete_report.md");
const content = ref("");
const loading = ref(false);
const error = ref("");

const currentRun = computed(() => runs.value.find((r) => r.id === activeRun.value));

const tabs = computed(() =>
  currentRun.value ? currentRun.value.files.map((f) => f.split("/").pop() ?? f) : [],
);

async function openFile(name: string) {
  if (!activeRun.value) return;
  activeFile.value = name;
  loading.value = true;
  error.value = "";
  try {
    const res = await fetchPreFile(activeRun.value, name);
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
    runs.value = (await fetchPreRuns()).runs;
    if (runs.value.length) activeRun.value = runs.value[0].id;
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
        <span class="mono">{{ r.id.replace("pre_analyst_", "") }}</span>
        <span class="count mono">{{ r.files.length }} 文件</span>
      </div>
      <div v-if="!runs.length" class="empty">
        <div class="icon">🧭</div>
        暂无板块轮动运行产物
      </div>
    </aside>

    <section class="card reader-card">
      <div class="tabs">
        <button
          v-for="t in tabs"
          :key="t"
          class="tab"
          :class="{ active: t === activeFile }"
          @click="openFile(t)"
        >
          {{ t.replace(".md", "") }}
        </button>
      </div>
      <div v-if="loading" class="skeleton" style="height: 320px"></div>
      <div v-else-if="error" class="empty">{{ error }}</div>
      <div v-else-if="!activeRun" class="empty">选择一个运行查看报告</div>
      <MarkdownViewer v-else :content="content" />
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
  transition: color 140ms ease-out, background 140ms ease-out;
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
