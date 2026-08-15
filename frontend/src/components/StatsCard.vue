<script setup lang="ts">
defineProps<{
  label: string;
  value: string | number;
  sub?: string;
  icon?: string;
}>();
</script>

<template>
  <div class="card hoverable stat-card">
    <div class="stat-icon" v-if="icon">{{ icon }}</div>
    <div class="stat-value mono">{{ value }}</div>
    <div class="stat-label">
      {{ label }}
      <span v-if="sub" class="stat-sub mono">{{ sub }}</span>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  padding: 16px 18px;
  position: relative;
}

.stat-icon {
  position: absolute;
  top: 14px;
  right: 16px;
  font-size: 18px;
  opacity: 0.7;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  line-height: 1.2;
}

.stat-label {
  margin-top: 4px;
  color: var(--text-2);
  font-size: 13px;
}

.stat-sub {
  color: var(--text-3);
  font-size: 12px;
}
</style>
