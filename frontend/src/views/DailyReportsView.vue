<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { fetchDates, fetchDailyFile, fetchDailyMeta } from "../api";
import type { DailyMeta } from "../api/types";
import MarkdownViewer from "../components/MarkdownViewer.vue";

const dates = ref<string[]>([]);
const activeDate = ref("");
const meta = ref<DailyMeta | null>(null);
const activeFile = ref("final_summary.md");
const content = ref("");
const loading = ref(false);
const error = ref("");

const tabs = computed(() => meta.value?.files ?? []);

async function openFile(name: string) {
  activeFile.value = name;
  loading.value = true;
  error.value = "";
  try {
    const res = await fetchDailyFile(activeDate.value, name);
    content.value = res.content;
  } catch (e) {
    error.value = String(e);
  } finally {
    loading.value = false;
  }
}

watch(activeDate, async () => {
  meta.value = null;
  if (!activeDate.value) return;
  try {
    meta.value = await fetchDailyMeta(activeDate.value);
    // docs 5.3: 综合总结（final_summary.md）默认选中
    const preferred =
      meta.value.files.find((f) => f.name === "final_summary.md" && f.exists) ??
      meta.value.files.find((f) => f.exists);
    if (preferred) await openFile(preferred.name);
  } catch (e) {
    error.value = String(e);
  }
});

onMounted(async () => {
  try {
    dates.value = (await fetchDates()).dates;
    if (dates.value.length) activeDate.value = dates.value[0];
  } catch (e) {
    error.value = String(e);
  }
});

function shift(delta: number) {
  const i = dates.value.indexOf(activeDate.value);
  const next = dates.value[i + delta];
  if (next) activeDate.value = next;
}
</script>

<template>
  <div>
    <div class="date-bar">
      <button class="btn" :disabled="!dates.length" @click="shift(1)">◀</button>
      <select v-model="activeDate" class="select mono">
        <option v-for="d in dates" :key="d" :value="d">{{ d }}</option>
      </select>
      <button class="btn" :disabled="!dates.length" @click="shift(-1)">
        ▶
      </button>
      <button
        class="btn"
        :disabled="!dates.length || dates[0] === activeDate"
        @click="activeDate = dates[0]"
      >
        回到最新
      </button>
      <span class="mono count"
        >{{ meta ? meta.files.filter((f) => f.exists).length : 0 }}/7</span
      >
    </div>

    <div class="card reader-card">
      <div class="tabs">
        <button
          v-for="t in tabs"
          :key="t.name"
          class="tab"
          :class="{ active: t.name === activeFile, disabled: !t.exists }"
          :disabled="!t.exists"
          @click="openFile(t.name)"
        >
          {{ t.label }}<span v-if="!t.exists" class="no-mark">无</span>
        </button>
      </div>
      <div v-if="loading" class="skeleton" style="height: 320px"></div>
      <div v-else-if="error" class="empty">{{ error }}</div>
      <div v-else-if="!activeDate" class="empty">
        <div class="icon">📂</div>
        暂无研报阅读产物,去任务中心发起一次
      </div>
      <MarkdownViewer v-else :content="content" />
    </div>
  </div>
</template>

<style scoped>
.date-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.count {
  margin-left: auto;
  color: var(--text-3);
  font-size: 12px;
}

.reader-card {
  padding: 18px 22px;
  min-height: 440px;
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

.tab:hover:not(.disabled) {
  color: var(--text-1);
  background: var(--bg-hover);
}

.tab.active {
  color: var(--accent);
  font-weight: 600;
  border-bottom: 2px solid var(--accent);
  border-radius: 0;
}

.tab.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.no-mark {
  margin-left: 4px;
  font-size: 10px;
  color: var(--text-3);
}
</style>
