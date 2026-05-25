<template>
  <div class="swarm-view">
    <div class="swarm-header">
      <div>
        <h2>{{ project?.name || 'Loading...' }}</h2>
        <p class="brief-preview">{{ project?.brief?.slice(0, 120) }}...</p>
      </div>
      <StatusBadge :status="project?.status" />
    </div>

    <div v-if="isActive" class="live-bar">
      <span class="pulse-dot"></span>
      The Movement is running — agents researching autonomously
    </div>

    <!-- Agent grid -->
    <div class="agent-grid">
      <AgentCard
        v-for="(state, domain) in agentStates"
        :key="domain"
        :domain="domain"
        :state="state"
        :project-id="projectId"
        @chat="openChat"
      />
    </div>

    <!-- Empty state while swarm hasn't started yet -->
    <div v-if="!hasAgents && !isActive" class="waiting">
      <div class="waiting-icon">⬡</div>
      <p v-if="project?.status === 'clarifying' || project?.status === 'draft'">
        Complete the brief setup to launch the swarm.
      </p>
      <p v-else>Agents initializing...</p>
    </div>

    <!-- Navigation to vision once complete -->
    <div v-if="project?.status === 'complete'" class="vision-cta">
      <router-link :to="`/project/${projectId}/vision`" class="vision-btn">
        View Final Vision & Morning Report →
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { projects as api, agents as agentsApi } from '../api/index.js'
import StatusBadge from '../components/StatusBadge.vue'
import AgentCard from '../components/AgentCard.vue'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id
const project = ref(null)
const agentStates = ref({})
let pollInterval = null

const isActive = computed(() =>
  ['running', 'synthesizing'].includes(project.value?.status)
)
const hasAgents = computed(() => Object.keys(agentStates.value).length > 0)

const load = async () => {
  try {
    const res = await api.get(projectId)
    project.value = res.data
    agentStates.value = res.data.agent_states || {}

    // Auto-navigate to vision when complete
    if (res.data.status === 'complete') {
      clearInterval(pollInterval)
    }
  } catch (e) { console.error(e) }
}

const openChat = (domain) => router.push(`/project/${projectId}/chat/${domain}`)

onMounted(() => {
  load()
  pollInterval = setInterval(load, 4000)  // poll every 4s while running
})
onUnmounted(() => clearInterval(pollInterval))
</script>

<style scoped>
.swarm-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 1.5rem;
}
h2 { font-size: 1.5rem; font-weight: 700; }
.brief-preview { color: #6b6b80; font-size: 0.875rem; margin-top: 0.3rem; }

.live-bar {
  display: flex; align-items: center; gap: 0.6rem;
  background: #0d1f18; border: 1px solid #1a3a28; border-radius: 8px;
  padding: 0.6rem 1rem; margin-bottom: 1.5rem; color: #34d399; font-size: 0.875rem;
}
.pulse-dot {
  width: 8px; height: 8px; border-radius: 50%; background: #34d399;
  animation: pulse 1.5s infinite;
}
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

.agent-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.waiting { text-align: center; padding: 4rem; color: #6b6b80; }
.waiting-icon { font-size: 2.5rem; opacity: 0.2; margin-bottom: 1rem; }

.vision-cta { margin-top: 2rem; text-align: center; }
.vision-btn {
  display: inline-block; padding: 1rem 2rem; background: #7c3aed;
  color: #fff; border-radius: 10px; text-decoration: none; font-weight: 700;
  font-size: 1.05rem;
}
</style>
