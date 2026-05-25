<template>
  <div class="agent-card" :class="state.status">
    <div class="agent-header">
      <span class="domain-name">{{ domainLabel }}</span>
      <span class="agent-status">{{ statusLabel }}</span>
    </div>
    <div class="confidence-bar">
      <div class="confidence-fill" :style="{ width: `${(state.best_confidence || 0) * 100}%` }"></div>
    </div>
    <p class="confidence-val">Confidence: {{ ((state.best_confidence || 0) * 100).toFixed(0) }}%</p>
    <p class="iterations">Iterations: {{ state.iterations_count || 0 }}</p>
    <button
      v-if="state.status === 'complete'"
      class="chat-btn"
      @click="$emit('chat', domain)"
    >
      Chat with agent →
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ domain: String, state: Object, projectId: String })
defineEmits(['chat'])

const domainLabels = {
  finance: 'Finance', technology: 'Technology', geopolitical: 'Geopolitical',
  market_sentiment: 'Market Sentiment', risk: 'Risk', supply_chain: 'Supply Chain',
  regulatory: 'Regulatory', competitive: 'Competitive Intel',
}
const statusLabels = {
  idle: 'Idle', researching: 'Researching', iterating: 'Iterating',
  challenged: 'Being challenged', complete: 'Complete', failed: 'Failed',
}

const domainLabel = computed(() => domainLabels[props.domain] || props.domain)
const statusLabel = computed(() => statusLabels[props.state?.status] || props.state?.status)
</script>

<style scoped>
.agent-card {
  background: #12121c; border: 1px solid #1e1e2e; border-radius: 10px;
  padding: 1rem; transition: border-color 0.2s;
}
.agent-card.researching, .agent-card.iterating { border-color: #34d39944; }
.agent-card.challenged { border-color: #f59e0b44; }
.agent-card.complete { border-color: #10b98144; }
.agent-card.failed { border-color: #ef444444; }

.agent-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; }
.domain-name { font-weight: 600; color: #e8e8f0; font-size: 0.95rem; }
.agent-status { font-size: 0.72rem; color: #6b6b80; text-transform: uppercase; letter-spacing: 0.05em; }

.confidence-bar {
  height: 4px; background: #1e1e2e; border-radius: 2px; margin-bottom: 0.4rem;
}
.confidence-fill {
  height: 100%; background: #7c3aed; border-radius: 2px; transition: width 0.5s;
}

.confidence-val, .iterations { font-size: 0.8rem; color: #6b6b80; margin-bottom: 0.25rem; }

.chat-btn {
  margin-top: 0.75rem; width: 100%; padding: 0.5rem;
  background: #1c1530; color: #a78bfa; border: 1px solid #2a1f45;
  border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 600;
  transition: background 0.15s;
}
.chat-btn:hover { background: #251840; }
</style>
