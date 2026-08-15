import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "dashboard",
      component: () => import("../views/DashboardView.vue"),
      meta: { title: "仪表盘" },
    },
    {
      path: "/reports/trading",
      name: "trading",
      component: () => import("../views/TradingReportsView.vue"),
      meta: { title: "交易分析" },
    },
    {
      path: "/reports/daily",
      name: "daily",
      component: () => import("../views/DailyReportsView.vue"),
      meta: { title: "研报阅读" },
    },
    {
      path: "/reports/pre",
      name: "pre",
      component: () => import("../views/PreReportsView.vue"),
      meta: { title: "板块轮动" },
    },
    {
      path: "/contradictions",
      name: "contradictions",
      component: () => import("../views/ContradictionsView.vue"),
      meta: { title: "矛盾追踪" },
    },
    {
      path: "/jobs",
      name: "jobs",
      component: () => import("../views/JobsView.vue"),
      meta: { title: "任务中心" },
    },
    {
      path: "/memory",
      name: "memory",
      component: () => import("../views/MemoryView.vue"),
      meta: { title: "决策日志" },
    },
    {
      path: "/settings",
      name: "settings",
      component: () => import("../views/SettingsView.vue"),
      meta: { title: "设置" },
    },
  ],
});

export default router;
