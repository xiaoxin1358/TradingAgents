<script setup lang="ts">
import { onMounted, ref } from "vue";
import { fetchMemory } from "../api";
import type { MemoryInfo } from "../api/types";
import MarkdownViewer from "../components/MarkdownViewer.vue";

const mem = ref<MemoryInfo | null>(null);
const error = ref("");

onMounted(async () => {
  try {
    mem.value = await fetchMemory();
  } catch (e) {
    error.value = String(e);
  }
});

function ago(mtime: number | null): string {
  if (!mtime) return "—";
  const mins = Math.round((Date.now() / 1000 - mtime) / 60);
  if (mins < 1) return "刚刚";
  if (mins < 60) return `${mins} 分钟前`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours} 小时前`;
  return `${Math.round(hours / 24)} 天前`;
}
</script>

<template>
  <div>
    <div class="card head">
      <div>
        <div class="path mono">{{ mem?.path ?? "…" }}</div>
        <div class="updated">最后更新 {{ ago(mem?.mtime ?? null) }}</div>
      </div>
    </div>
    <div class="card reader-card">
      <div v-if="error" class="empty">{{ error }}</div>
      <div v-else-if="mem && !mem.exists" class="empty">
        <div class="icon">🗂</div>
        决策记忆尚未生成——运行一次交易分析后自动创建
      </div>
      <MarkdownViewer v-else-if="mem" :content="mem.content" />
    </div>
  </div>
</template>

<style scoped>
.head {
  padding: 12px 16px;
  margin-bottom: 16px;
}

.path {
  font-size: 12.5px;
  color: var(--text-2);
}

.updated {
  font-size: 12px;
  color: var(--text-3);
  margin-top: 2px;
}

.reader-card {
  padding: 18px 22px;
  min-height: 360px;
}
</style>
