<script setup lang="ts">
import { computed } from "vue";

// 看多=红 / 中性=灰 / 看空=绿 (docs 5.0.2, A-share habit).
const props = defineProps<{ direction: string }>();

const cls = computed(() => {
  if (props.direction === "看多") return "up";
  if (props.direction === "看空") return "down";
  return "flat";
});
</script>

<template>
  <span class="badge" :class="cls">{{ direction || "?" }}</span>
</template>
