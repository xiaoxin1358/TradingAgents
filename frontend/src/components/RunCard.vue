<script setup lang="ts">
import { computed } from "vue";
import type { RunInfo } from "../api/types";

const props = defineProps<{ run: RunInfo }>();

const kindMeta = computed(() => {
  switch (props.run.kind ?? "trading") {
    case "daily":
      return { icon: "📄", label: "研报阅读" };
    case "pre":
      return { icon: "🧭", label: "板块轮动" };
    default:
      return { icon: "📈", label: "交易分析" };
  }
});

const time = computed(() => {
  const d = new Date((props.run.mtime ?? 0) * 1000);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
    d.getDate(),
  ).padStart(2, "0")} ${String(d.getHours()).padStart(2, "0")}:${String(
    d.getMinutes(),
  ).padStart(2, "0")}`;
});
</script>

<template>
  <div class="run-card">
    <span class="run-icon">{{ kindMeta.icon }}</span>
    <div class="run-main">
      <div class="run-title mono">{{ run.id }}</div>
      <div class="run-sub">{{ kindMeta.label }} · {{ time }}</div>
    </div>
    <span class="dot done"></span>
  </div>
</template>

<style scoped>
.run-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  transition: background 140ms ease-out;
  border-left: 2px solid transparent;
}

.run-card:hover {
  background: var(--bg-hover);
  border-left-color: var(--accent);
}

.run-icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
}

.run-main {
  flex: 1;
  min-width: 0;
}

.run-title {
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.run-sub {
  font-size: 12px;
  color: var(--text-3);
}
</style>
