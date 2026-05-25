<template>
  <div class="agent-card" :class="state.status">
    <div class="agent-header">
      <span class="domain-name">{{ domainLabel }}</span>
      <span class="agent-status">{{ statusLabel }}</span>
    </div>

    <!-- Confidence bar + score -->
    <div class="confidence-row">
      <div class="confidence-bar">
        <div class="confidence-fill" :style="{ width: `${overallPct}%` }"></div>
      </div>
      <span class="confidence-num" :class="confidenceClass">{{ overallPct }}%</span>
    </div>

    <div class="meta-row">
      <span>{{ state.iterations_count || 0 }} iterations</span>
    </div>

    <!-- Confidence breakdown (expandable) -->
    <div v-if="hasBreakdown" class="breakdown-section">
      <button class="breakdown-toggle" @click="breakdownOpen = !breakdownOpen">
        {{ breakdownOpen ? '▲ Hide breakdown' : '▼ Confidence breakdown' }}
      </button>
      <div v-if="breakdownOpen" class="breakdown-body">
        <div v-for="item in breakdownItems" :key="item.key" class="breakdown-item">
          <div class="breakdown-label-row">
            <span class="breakdown-label">{{ item.label }}</span>
            <span class="breakdown-val" :class="scoreClass(item.value)">{{ item.value }}%</span>
          </div>
          <div class="breakdown-bar">
            <div class="breakdown-fill" :style="{ width: `${item.value}%`, background: scoreColor(item.value) }"></div>
          </div>
          <p class="breakdown-desc">{{ item.desc }}</p>
        </div>
      </div>
    </div>

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
import { ref, computed } from 'vue'

const props = defineProps({ domain: String, state: Object, projectId: String })
defineEmits(['chat'])

const breakdownOpen = ref(false)

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

const bd = computed(() => props.state?.confidence_breakdown || {})
const hasBreakdown = computed(() =>
  props.state?.status === 'complete' && Object.keys(bd.value).length > 0 && bd.value.overall > 0
)
const overallPct = computed(() => bd.value.overall || Math.round((props.state?.best_confidence || 0) * 100))

const confidenceClass = computed(() => {
  const v = overallPct.value
  if (v >= 75) return 'high'
  if (v >= 50) return 'mid'
  return 'low'
})

const breakdownItems = computed(() => [
  {
    key: 'evidence_quality',
    label: 'Evidence Quality',
    value: bd.value.evidence_quality || 0,
    desc: 'How much of the analysis is backed by real data, numbers, and sources vs. pure reasoning.',
  },
  {
    key: 'source_diversity',
    label: 'Source Diversity',
    value: bd.value.source_diversity || 0,
    desc: 'How many independent sources confirmed the findings. Single-source conclusions score lower.',
  },
  {
    key: 'challenge_resolved',
    label: 'Challenge Resolved',
    value: bd.value.challenge_resolved || 0,
    desc: 'How well the agent addressed the challenger\'s feedback and stress-tested its own thesis.',
  },
  {
    key: 'risk_coverage',
    label: 'Risk Coverage',
    value: bd.value.risk_coverage || 0,
    desc: 'Whether key downside risks, failure modes, and counter-scenarios were identified.',
  },
])

const scoreClass = (v) => v >= 75 ? 'high' : v >= 50 ? 'mid' : 'low'
const scoreColor = (v) => v >= 75 ? '#10b981' : v >= 50 ? '#f59e0b' : '#f87171'
</script>

<style scoped>
.agent-card {
  background: #12121c; border: 1px solid #1e1e2e; border-radius: 10px;
  padding: 1rem; transition: border-color 0.2s;
}
.agent-card.researching, .agent-card.iterating { border-color: #34d39930; }
.agent-card.challenged { border-color: #f59e0b30; }
.agent-card.complete { border-color: #10b98130; }
.agent-card.failed { border-color: #ef444430; }

.agent-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;
}
.domain-name { font-weight: 600; color: #e8e8f0; font-size: 0.95rem; }
.agent-status { font-size: 0.7rem; color: #6b6b80; text-transform: uppercase; letter-spacing: 0.05em; }

.confidence-row { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.3rem; }
.confidence-bar { flex: 1; height: 5px; background: #1e1e2e; border-radius: 3px; }
.confidence-fill { height: 100%; background: #7c3aed; border-radius: 3px; transition: width 0.6s; }
.confidence-num { font-size: 0.85rem; font-weight: 700; min-width: 36px; text-align: right; }
.confidence-num.high { color: #10b981; }
.confidence-num.mid  { color: #f59e0b; }
.confidence-num.low  { color: #f87171; }

.meta-row { font-size: 0.75rem; color: #4a4a60; margin-bottom: 0.75rem; }

/* Breakdown */
.breakdown-section { margin-bottom: 0.75rem; }
.breakdown-toggle {
  width: 100%; background: none; border: 1px solid #1e1e2e; border-radius: 6px;
  color: #5555a0; font-size: 0.72rem; padding: 0.35rem 0.6rem; cursor: pointer;
  text-align: left; transition: border-color 0.15s;
}
.breakdown-toggle:hover { border-color: #7c3aed; color: #a78bfa; }

.breakdown-body { margin-top: 0.5rem; display: flex; flex-direction: column; gap: 0.6rem; }
.breakdown-item { }
.breakdown-label-row { display: flex; justify-content: space-between; margin-bottom: 0.2rem; }
.breakdown-label { font-size: 0.75rem; color: #8888a0; }
.breakdown-val { font-size: 0.75rem; font-weight: 700; }
.breakdown-val.high { color: #10b981; }
.breakdown-val.mid  { color: #f59e0b; }
.breakdown-val.low  { color: #f87171; }
.breakdown-bar { height: 3px; background: #1e1e2e; border-radius: 2px; margin-bottom: 0.25rem; }
.breakdown-fill { height: 100%; border-radius: 2px; transition: width 0.5s; }
.breakdown-desc { font-size: 0.7rem; color: #4a4a60; line-height: 1.4; }

.chat-btn {
  width: 100%; padding: 0.5rem; background: #1c1530; color: #a78bfa;
  border: 1px solid #2a1f45; border-radius: 6px; cursor: pointer;
  font-size: 0.85rem; font-weight: 600; transition: background 0.15s;
}
.chat-btn:hover { background: #251840; }
</style>
