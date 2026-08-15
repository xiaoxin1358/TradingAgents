<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const title = computed(() => String(route.meta.title ?? "TradingAgents"));

const nav = [
  { to: "/", label: "仪表盘", icon: "◫" },
  { to: "/reports/trading", label: "交易分析", icon: "📈" },
  { to: "/reports/daily", label: "研报阅读", icon: "📄" },
  { to: "/reports/pre", label: "板块轮动", icon: "🧭" },
  { to: "/contradictions", label: "矛盾追踪", icon: "⚔" },
  { to: "/jobs", label: "任务中心", icon: "▶" },
  { to: "/memory", label: "决策日志", icon: "🗂" },
  { to: "/settings", label: "设置", icon: "⚙" },
];
</script>

<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark">TA</span>
        <div class="brand-text">
          <b>TradingAgents</b>
          <small>研报智研</small>
        </div>
      </div>
      <nav class="nav">
        <RouterLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          :class="{ active: route.path === item.to }"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
        </RouterLink>
      </nav>
      <div class="sidebar-foot mono">v0.1 · M1 只读</div>
    </aside>

    <div class="main">
      <header class="topbar">
        <h1 class="topbar-title">{{ title }}</h1>
        <div class="topbar-right">
          <span class="dot done"></span>
          <span class="mono topbar-status">API 在线</span>
        </div>
      </header>
      <div class="content">
        <Transition name="page" appear>
          <div :key="route.path" class="route-page">
            <RouterView />
          </div>
        </Transition>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sidebar {
  width: 200px;
  flex-shrink: 0;
  background: var(--bg-surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 16px 10px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 8px 18px;
}

.brand-mark {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--accent), #2f63c8);
  color: #fff;
  font-weight: 700;
  font-size: 13px;
  display: grid;
  place-items: center;
}

.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}

.brand-text b {
  font-size: 13px;
}

.brand-text small {
  color: var(--text-3);
  font-size: 11px;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  color: var(--text-2);
  font-size: 13px;
  transition: background 140ms ease-out, color 140ms ease-out;
  border-left: 2px solid transparent;
}

.nav-item:hover {
  background: var(--bg-hover);
  color: var(--text-1);
}

.nav-item.active {
  background: var(--bg-hover);
  color: var(--accent);
  border-left-color: var(--accent);
  font-weight: 600;
}

.nav-icon {
  width: 20px;
  text-align: center;
}

.sidebar-foot {
  margin-top: auto;
  padding: 10px 12px 2px;
  color: var(--text-3);
  font-size: 11px;
}

.topbar {
  height: 56px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-base);
}

.topbar-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.topbar-status {
  color: var(--text-3);
  font-size: 12px;
}

@media (max-width: 768px) {
  .sidebar {
    width: 56px;
    padding: 12px 6px;
  }

  .brand-text,
  .nav-label,
  .sidebar-foot {
    display: none;
  }

  .nav-item {
    justify-content: center;
    padding: 10px 0;
  }
}
</style>
