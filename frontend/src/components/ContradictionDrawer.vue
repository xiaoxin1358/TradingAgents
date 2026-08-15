<script setup lang="ts">
import { computed } from "vue";
import type { ContradictionRow } from "../api/types";
import DirectionBadge from "./DirectionBadge.vue";

const props = defineProps<{ row: ContradictionRow }>();
const emit = defineEmits<{ (e: "close"): void }>();

const lifeWidth = computed(() => {
  const days = props.row.days_open ?? 0;
  return `${Math.min(Math.max(days * 9, 4), 100)}%`;
});

function text(d: string | undefined | null): string {
  return d || "未生成";
}
</script>

<template>
  <div class="mask" @click.self="emit('close')">
    <aside class="drawer card">
      <header class="drawer-head">
        <h2 class="drawer-title">{{ row.subject }}</h2>
        <button class="btn" @click="emit('close')">✕</button>
      </header>

      <div class="vs">
        <div class="claim" :class="row.direction_a === '看多' ? 'side-up' : row.direction_a === '看空' ? 'side-down' : ''">
          <div class="claim-head">
            <span class="mono claim-broker">{{ text(row.claim_a.broker) }}</span>
            <DirectionBadge :direction="row.direction_a" />
          </div>
          <blockquote class="claim-quote">{{ text(row.claim_a.quote) }}</blockquote>
        </div>
        <div class="vs-mark mono">VS</div>
        <div class="claim" :class="row.direction_b === '看多' ? 'side-up' : row.direction_b === '看空' ? 'side-down' : ''">
          <div class="claim-head">
            <span class="mono claim-broker">{{ text(row.claim_b.broker) }}</span>
            <DirectionBadge :direction="row.direction_b" />
          </div>
          <blockquote class="claim-quote">{{ text(row.claim_b.quote) }}</blockquote>
        </div>
      </div>

      <section class="insight">
        <h3 class="section-title">
          洞察
          <span class="tag" :class="row.insight?.cause_type || '未生成'">
            {{ text(row.insight?.cause_type) }}
          </span>
        </h3>
        <div class="kv"><span>成因</span><p>{{ text(row.insight?.cause) }}</p></div>
        <div class="kv"><span>点评</span><p>{{ text(row.insight?.analysis) }}</p></div>
        <div class="kv"><span>验证</span><p>{{ text(row.insight?.watch) }}</p></div>
        <div class="kv"><span>倾向</span><p>{{ text(row.insight?.tilt) }}</p></div>
      </section>

      <section class="life">
        <h3 class="section-title">生命周期</h3>
        <div class="life-bar">
          <span class="dot done"></span>
          <div class="life-line">
            <div class="life-fill" :style="{ width: lifeWidth }"></div>
          </div>
          <span class="dot done"></span>
        </div>
        <div class="life-meta mono">
          <span>首次 {{ row.first_seen }}</span>
          <span>持续 {{ row.days_open ?? "?" }} 天</span>
          <span>最近 {{ row.last_seen }}</span>
        </div>
        <p class="life-state">
          状态：<span class="badge accent">{{ row.status === "open" ? "未决" : "已解决" }}</span>
          <span v-if="row.winner" class="mono"> · 胜方 {{ row.winner }} · {{ row.resolved_by }} · {{ row.resolved_date }}</span>
        </p>
      </section>
    </aside>
  </div>
</template>

<style scoped>
.mask {
  position: fixed;
  inset: 0;
  background: rgb(0 0 0 / 0.5);
  display: flex;
  justify-content: flex-end;
  z-index: 50;
}

.drawer {
  width: 480px;
  max-width: 94vw;
  height: 100%;
  border-radius: 0;
  overflow-y: auto;
  padding: 20px 22px;
  animation: slideIn 180ms ease-out;
}

@keyframes slideIn {
  from { transform: translateX(30px); opacity: 0; }
  to { transform: none; opacity: 1; }
}

.drawer-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.drawer-title {
  font-size: 17px;
  margin: 0;
}

.vs {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 8px;
  align-items: stretch;
}

.claim {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.claim.side-up { border-left: 3px solid var(--up); }
.claim.side-down { border-left: 3px solid var(--down); }

.claim-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.claim-broker {
  font-size: 12.5px;
  color: var(--text-2);
}

.claim-quote {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-1);
}

.vs-mark {
  align-self: center;
  color: var(--text-3);
  font-size: 11px;
}

.section-title {
  font-size: 13px;
  margin: 18px 0 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.kv {
  display: flex;
  gap: 10px;
  margin: 6px 0;
  font-size: 13px;
}

.kv span {
  flex-shrink: 0;
  width: 34px;
  color: var(--text-3);
}

.kv p {
  margin: 0;
  color: var(--text-2);
}

.life-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 8px 0;
}

.life-line {
  flex: 1;
  height: 4px;
  border-radius: 999px;
  background: var(--bg-elevated);
  overflow: hidden;
}

.life-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--accent), var(--warn));
}

.life-meta {
  display: flex;
  justify-content: space-between;
  color: var(--text-3);
  font-size: 12px;
}

.life-state {
  margin-top: 8px;
  font-size: 13px;
  color: var(--text-2);
}
</style>
