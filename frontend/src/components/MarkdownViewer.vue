<script setup lang="ts">
import MarkdownIt from "markdown-it";
import { computed } from "vue";

// Full-site markdown reading style (docs 8.1).
const props = defineProps<{ content: string }>();

const md = new MarkdownIt({ html: true, linkify: true, breaks: false });
const html = computed(() => md.render(props.content));
</script>

<template>
  <div class="md" v-html="html"></div>
</template>

<style scoped>
.md {
  max-width: 720px;
  margin: 0 auto;
  line-height: 1.7;
  color: var(--text-1);
  font-size: 14px;
}

.md :deep(h1) { font-size: 22px; margin: 8px 0 14px; }
.md :deep(h2) {
  font-size: 18px;
  margin: 26px 0 12px;
  padding-top: 18px;
  border-top: 1px solid var(--border);
}
.md :deep(h3) { font-size: 15px; margin: 20px 0 8px; }
.md :deep(p) { margin: 0.9em 0; }
.md :deep(ul), .md :deep(ol) { padding-left: 1.4em; }
.md :deep(li) { margin: 3px 0; }

.md :deep(table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  margin: 12px 0;
}

.md :deep(th) {
  text-align: left;
  font-weight: 600;
  padding: 8px 10px;
  border-bottom: 2px solid var(--border);
}

.md :deep(td) {
  padding: 7px 10px;
  border-bottom: 1px solid var(--border);
}

.md :deep(tr:nth-child(even)) {
  background: rgb(255 255 255 / 0.02);
}

.md :deep(blockquote) {
  margin: 10px 0;
  padding: 8px 14px;
  border-left: 3px solid var(--accent);
  background: var(--bg-hover);
  color: var(--text-2);
}

.md :deep(code) {
  font-family: var(--font-mono);
  font-size: 12.5px;
  background: var(--bg-elevated);
  padding: 1px 5px;
  border-radius: 4px;
}

.md :deep(pre) {
  background: var(--bg-base);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 12px;
  overflow-x: auto;
}

.md :deep(pre code) {
  background: none;
  padding: 0;
}

.md :deep(details) {
  margin: 6px 0;
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  background: var(--bg-elevated);
  font-size: 13px;
}

.md :deep(summary) {
  cursor: pointer;
  color: var(--accent);
  user-select: none;
}

.md :deep(details[open]) {
  animation: fadeIn 120ms ease-out;
}

@keyframes fadeIn {
  from { opacity: 0.4; }
  to { opacity: 1; }
}
</style>
