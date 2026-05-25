<template>
  <router-link :to="dest" class="card">
    <div class="card-header">
      <span class="name">{{ project.name }}</span>
      <StatusBadge :status="project.status" />
    </div>
    <p class="brief">{{ truncate(project.brief, 120) }}</p>
    <div class="card-footer">
      <span class="domains">{{ domainCount }} domains</span>
      <span class="round">Round {{ project.round_number }}</span>
      <span class="date">{{ timeAgo(project.updated_at) }}</span>
    </div>
  </router-link>
</template>

<script setup>
import { computed } from 'vue'
import StatusBadge from './StatusBadge.vue'

const props = defineProps({ project: Object })

const dest = computed(() =>
  props.project.status === 'complete'
    ? `/project/${props.project.project_id}/vision`
    : `/project/${props.project.project_id}`
)

const domainCount = computed(() =>
  Object.keys(props.project.agent_states || {}).length ||
  (props.project.scope?.domains_needed?.length ?? 0)
)

const truncate = (str, n) => str?.length > n ? str.slice(0, n) + '...' : str

const timeAgo = (ts) => {
  if (!ts) return ''
  const diff = Date.now() / 1000 - ts
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}
</script>

<style scoped>
.card {
  display: block; background: #12121c; border: 1px solid #1e1e2e;
  border-radius: 12px; padding: 1.25rem; text-decoration: none;
  transition: border-color 0.15s, transform 0.1s;
}
.card:hover { border-color: #7c3aed; transform: translateY(-1px); }

.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.6rem; }
.name { font-weight: 600; color: #e8e8f0; font-size: 1rem; }

.brief { color: #8888a0; font-size: 0.875rem; line-height: 1.5; margin-bottom: 1rem; }

.card-footer { display: flex; gap: 1rem; font-size: 0.75rem; color: #5555668; }
.domains, .round, .date { color: #5555688; }
.date { margin-left: auto; }
</style>
