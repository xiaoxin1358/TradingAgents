<script setup lang="ts">
// M2 placeholder (docs 10): job creation + SSE progress land in the next
// milestone; the backend /api/jobs does not exist yet.
</script>

<template>
  <div class="empty">
    <div class="icon">🚧</div>
    任务中心属于 M2 阶段——完成后可在页面上发起 交易分析 / 研报阅读 / 板块轮动
    并实时查看进度
    <div style="margin-top: 14px">
      <RouterLink to="/reports/daily" class="btn">先浏览已有报告</RouterLink>
    </div>
  </div>
</template>
