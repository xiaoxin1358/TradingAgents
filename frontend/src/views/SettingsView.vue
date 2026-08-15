<script setup lang="ts">
import { onMounted, ref } from "vue";
import { fetchSettings } from "../api";
import type { Settings } from "../api/types";

const data = ref<Settings | null>(null);
const error = ref("");

onMounted(async () => {
  try {
    data.value = await fetchSettings();
  } catch (e) {
    error.value = String(e);
  }
});

const copied = ref("");

async function copy(value: string, key: string) {
  try {
    await navigator.clipboard.writeText(value);
    copied.value = key;
    setTimeout(() => (copied.value = ""), 1200);
  } catch {
    /* clipboard unavailable */
  }
}
</script>

<template>
  <div>
    <div class="card notice">
      ⚠ <b>配置为只读。</b> 修改请编辑项目根目录 <code class="mono">.env</code> 后重启任务。
    </div>

    <div v-if="error" class="empty">{{ error }}</div>

    <div v-for="g in data?.groups ?? []" :key="g.label" class="card group">
      <h3 class="card-title">{{ g.label }}</h3>
      <div v-for="item in g.items" :key="item.key" class="row">
        <span class="key mono">{{ item.key }}</span>
        <span class="value mono" :class="{ blank: !item.value }">{{ item.value || "（未设置）" }}</span>
        <button v-if="item.value" class="btn" @click="copy(item.value, item.key)">
          {{ copied === item.key ? "已复制 ✓" : "复制" }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.notice {
  padding: 12px 16px;
  margin-bottom: 16px;
  background: rgb(245 158 11 / 0.08);
  border-color: rgb(245 158 11 / 0.35);
  font-size: 13px;
}

.notice code {
  background: var(--bg-elevated);
  padding: 1px 6px;
  border-radius: 4px;
}

.group {
  padding: 16px 18px;
  margin-bottom: 16px;
}

.row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 9px 0;
  border-bottom: 1px solid var(--border);
}

.row:last-child {
  border-bottom: none;
}

.key {
  width: 280px;
  color: var(--text-3);
  font-size: 12.5px;
}

.value {
  flex: 1;
  color: var(--text-1);
  font-size: 13px;
  overflow-wrap: anywhere;
}

.value.blank {
  color: var(--text-3);
}
</style>
