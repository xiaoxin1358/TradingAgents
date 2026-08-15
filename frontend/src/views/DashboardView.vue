<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { fetchOverview } from "../api";
import type { Overview } from "../api/types";
import StatsCard from "../components/StatsCard.vue";
import RunCard from "../components/RunCard.vue";
import DirectionBadge from "../components/DirectionBadge.vue";

const router = useRouter();
const data = ref<Overview | null>(null);
const error = ref("");

onMounted(async () => {
  try {
    data.value = await fetchOverview();
  } catch (e) {
    error.value = String(e);
  }
});

const today = new Date();
const weekdays = ["日", "一", "二", "三", "四", "五", "六"];

function dayHeat(days: number | null): string {
  if (days === null) return "flat";
  if (days >= 7) return "warn";
  return "accent";
}
</script>

<template>
  <div v-if="!data && !error" class="grid stats-grid">
    <div v-for="i in 4" :key="i" class="skeleton" style="height: 86px"></div>
  </div>
  <div v-else-if="error" class="empty">
    <div class="icon">⚠</div>
    {{ error }}——请确认后端已启动（uvicorn webapi.main:app --port 8000）
  </div>

  <template v-else-if="data">
    <div class="page-head">
      <div>
        <h2 class="hello">研报智研 · {{ today.getFullYear() }}-{{ String(today.getMonth() + 1).padStart(2, "0") }}-{{ String(today.getDate()).padStart(2, "0") }} 星期{{ weekdays[today.getDay()] }}</h2>
      </div>
      <RouterLink to="/jobs" class="btn primary">✨ 新建任务</RouterLink>
    </div>

    <div class="grid stats-grid">
      <StatsCard icon="📄" label="报告天数" :value="data.stats.daily_days" />
      <StatsCard icon="⚔" label="矛盾总数" :value="data.stats.contradictions.total" />
      <StatsCard icon="⏳" label="未决矛盾" :value="data.stats.contradictions.open" />
      <StatsCard
        icon="✅"
        label="解决率"
        :value="data.stats.contradictions.resolve_rate.toFixed(0) + '%'"
        :sub="'最长未决 ' + data.stats.contradictions.longest_open + ' 天'"
      />
    </div>

    <div class="grid two-col">
      <section class="card">
        <h3 class="card-title">最近运行</h3>
        <RunCard v-for="r in data.recent" :key="r.id" :run="r" />
        <div v-if="!data.recent.length" class="empty">
          <div class="icon">📂</div>
          还没有任何运行产物,去任务中心发起第一个分析
        </div>
      </section>

      <section class="card">
        <h3 class="card-title">今日矛盾 Top 5</h3>
        <div
          v-for="t in data.top5"
          :key="t.id"
          class="top-row"
          @click="router.push('/contradictions')"
        >
          <div class="top-main">
            <div class="top-subject">{{ t.subject }}</div>
            <div class="top-brokers mono">{{ t.broker_a }} vs {{ t.broker_b }}</div>
          </div>
          <div class="top-right">
            <DirectionBadge :direction="t.direction_a" />
            <DirectionBadge :direction="t.direction_b" />
            <span class="badge" :class="dayHeat(t.days_open)">
              {{ t.days_open === null ? "?" : t.days_open === 0 ? "今日" : t.days_open + " 天" }}
            </span>
          </div>
        </div>
        <div v-if="!data.top5.length" class="empty">
          <div class="icon">⚔</div>
          暂无未决矛盾
        </div>
      </section>
    </div>
  </template>
</template>

<style scoped>
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.hello {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.grid {
  display: grid;
  gap: 16px;
}

.stats-grid {
  grid-template-columns: repeat(4, 1fr);
}

.two-col {
  grid-template-columns: 3fr 2fr;
  margin-top: 16px;
}

.top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  border-left: 2px solid transparent;
  transition: background 140ms ease-out;
}

.top-row:hover {
  background: var(--bg-hover);
  border-left-color: var(--accent);
}

.top-subject {
  font-size: 13.5px;
  font-weight: 600;
}

.top-brokers {
  font-size: 12px;
  color: var(--text-3);
}

.top-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .two-col {
    grid-template-columns: 1fr;
  }
}
</style>
