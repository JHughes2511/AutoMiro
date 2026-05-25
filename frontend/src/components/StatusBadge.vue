<template>
  <span class="badge" :class="status">{{ label }}</span>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ status: String })
const labels = {
  draft: 'Draft', clarifying: 'Clarifying', running: 'Running',
  synthesizing: 'Synthesizing', complete: 'Complete', failed: 'Failed',
}
const label = computed(() => labels[props.status] || props.status)
</script>

<style scoped>
.badge {
  font-size: 0.7rem; font-weight: 700; padding: 0.2rem 0.55rem;
  border-radius: 999px; text-transform: uppercase; letter-spacing: 0.05em;
}
.draft      { background: #1e1e2e; color: #6b6b80; }
.clarifying { background: #1c1530; color: #a78bfa; }
.running    { background: #12251a; color: #34d399; animation: pulse 2s infinite; }
.synthesizing { background: #1a1530; color: #818cf8; animation: pulse 1.5s infinite; }
.complete   { background: #12251a; color: #10b981; }
.failed     { background: #251212; color: #f87171; }

@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
</style>
