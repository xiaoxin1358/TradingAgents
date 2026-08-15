<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useContradictionStore } from "../stores/contradictions";
import DirectionBadge from "../components/DirectionBadge.vue";
import ContradictionDrawer from "../components/ContradictionDrawer.vue";

const store = useContradictionStore();
const error = ref("");

const statusChips = [
  { value: "", label: "全部" },
  { value: "open", label: "未决" },
  { value: "resolved", label: "已解决" },
];

const causeOptions = ["口径差异", "时间尺度", "框架假设", "信息时效", "立场差异", "其他"];

function dayHeat(days: number | null): string {
  if (days === null) return "flat";
  if (days >= 7) return "warn";
  if (days >= 2) return "accent";
  return "flat";
}

async function applyFilter(patch: Record<string, string | number | null | undefined>) {
  for (const [k, v] of Object.entries(patch)) store.setFilter(k as never, v);
  error.value = "";
  try {
    await store.load();
  } catch (e) {
    error.value = String(e);
  }
}

const statusLabel = computed(() => {
  const s = store.filters.status;
  if (s === "resolved") return "已解决";
  if (s === "open") return "未决";
  return "全部";
});

onMounted(async () => {
  try {
    await store.load();
  } catch (e) {
    error.value = String(e);
  }
});
</script>

<template>
  <div>
    <div class="filters card">
      <div class="chip-group">
        <button
          v-for="c in statusChips"
          :key="c.value"
          class="chip"
          :class="{ active: (store.filters.status ?? '') === c.value }"
          @click="applyFilter({ status: c.value || undefined })"
        >
          {{ c.label }}
        </button>
      </div>

      <select class="select" @change="applyFilter({ kind: ($event.target as HTMLSelectElement).value || undefined })">
        <option value="">全部类型</option>
        <option value="opinion">观点</option>
        <option value="factual">事实</option>
      </select>

      <select class="select" @change="applyFilter({ cause_type: ($event.target as HTMLSelectElement).value || undefined })">
        <option value="">全部归因</option>
        <option v-for="c in causeOptions" :key="c" :value="c">{{ c }}</option>
      </select>

      <input
        class="input"
        placeholder="🔍 对象搜索"
        @keyup.enter="applyFilter({ subject: ($event.target as HTMLInputElement).value || undefined })"
      />

      <select class="select" @change="applyFilter({ min_days: ($event.target as HTMLSelectElement).value ? Number(($event.target as HTMLSelectElement).value) : undefined })">
        <option value="">持续天数不限</option>
        <option value="1">≥ 1 天</option>
        <option value="3">≥ 3 天</option>
        <option value="7">≥ 7 天</option>
      </select>

      <span class="mono total">共 {{ store.total }} 条</span>
    </div>

    <div class="card table-card">
      <div v-if="store.loading" class="skeleton" style="height: 260px"></div>
      <div v-else-if="error" class="empty">{{ error }}</div>
      <table v-else-if="store.rows.length" class="table">
        <thead>
          <tr>
            <th>对象</th>
            <th>类型</th>
            <th>甲方</th>
            <th>乙方</th>
            <th>持续</th>
            <th>状态</th>
            <th>归因</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in store.rows" :key="r.id" @click="store.openDetail(r.id)">
            <td class="subject">{{ r.subject }}</td>
            <td class="mono muted">{{ r.kind_cn }}/{{ r.scope_cn }}/{{ r.scale_cn }}</td>
            <td>
              <DirectionBadge :direction="r.direction_a" />
              <span class="mono broker">{{ r.claim_a.broker ?? "?" }}</span>
            </td>
            <td>
              <DirectionBadge :direction="r.direction_b" />
              <span class="mono broker">{{ r.claim_b.broker ?? "?" }}</span>
            </td>
            <td>
              <span class="badge" :class="dayHeat(r.days_open)">
                {{ r.days_open === null ? "?" : r.days_open === 0 ? "今日" : r.days_open + " 天" }}
              </span>
            </td>
            <td>
              <span class="badge accent" v-if="r.status === 'open'">未决</span>
              <span class="badge down" v-else>已解决</span>
            </td>
            <td>
              <span class="tag" :class="r.insight?.cause_type || '未生成'">
                {{ r.insight?.cause_type || "未生成" }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty">
        <div class="icon">⚔</div>
        没有匹配的矛盾
      </div>
    </div>

    <ContradictionDrawer v-if="store.selected" :row="store.selected" @close="store.closeDetail()" />
  </div>
</template>

<style scoped>
.filters {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  padding: 12px 14px;
  margin-bottom: 16px;
}

.chip-group {
  display: flex;
  gap: 4px;
}

.chip {
  border: 1px solid var(--border);
  background: var(--bg-elevated);
  color: var(--text-2);
  border-radius: 999px;
  font-size: 12.5px;
  padding: 4px 13px;
  cursor: pointer;
  transition: color 140ms ease-out, border-color 140ms ease-out, background 140ms ease-out;
}

.chip:hover {
  color: var(--text-1);
}

.chip.active {
  color: var(--accent);
  border-color: var(--accent);
  background: rgb(79 140 255 / 0.1);
  font-weight: 600;
}

.total {
  margin-left: auto;
  color: var(--text-3);
  font-size: 12px;
}

.table-card {
  padding: 8px 10px;
  overflow-x: auto;
}

.subject {
  font-weight: 600;
  white-space: nowrap;
}

.broker {
  font-size: 12px;
  color: var(--text-2);
  margin-left: 6px;
}

.muted {
  color: var(--text-2);
}
</style>
