<template>
  <div class="vision-view">
    <div class="vision-header">
      <router-link :to="`/project/${projectId}`" class="back">← Swarm</router-link>
      <h2>{{ project?.name }}</h2>
      <div class="confidence-overall">
        Overall Confidence: <strong>{{ overallPct }}%</strong>
      </div>
    </div>

    <!-- Morning Report -->
    <section class="section">
      <h3>Morning Report</h3>
      <div class="report-body" v-html="reportHtml"></div>
    </section>

    <!-- Top Picks by Layer -->
    <section class="section" v-if="topPicks && Object.keys(topPicks).length">
      <h3>Top Picks by Layer</h3>
      <div v-for="(picks, layer) in topPicks" :key="layer" class="layer-block">
        <h4 class="layer-name">{{ layer }}</h4>
        <div class="ticker-grid">
          <TickerCard v-for="t in picks" :key="t.ticker" :ticker="t" />
        </div>
      </div>
    </section>

    <!-- Plausibility Ranking -->
    <section class="section" v-if="plausibilityRanking?.length">
      <h3>Outcome Plausibility Ranking</h3>
      <div v-for="(outcome, i) in plausibilityRanking" :key="i" class="outcome-row">
        <div class="outcome-rank">#{{ i + 1 }}</div>
        <div class="outcome-body">
          <div class="outcome-desc">{{ outcome.outcome }}</div>
          <div class="outcome-meta">
            <span class="plausibility-bar-wrap">
              <span class="plausibility-bar" :style="{ width: outcome.plausibility_score + '%' }"></span>
            </span>
            <span class="plausibility-num">{{ outcome.plausibility_score }}</span>
            <span class="strength" :class="outcome.evidence_strength">{{ outcome.evidence_strength }}</span>
            <span class="domains-list">{{ outcome.supporting_domains?.join(', ') }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Key Convergences -->
    <section class="section two-col" v-if="convergences?.length || tensions?.length">
      <div>
        <h3>Convergences</h3>
        <ul class="bullet-list">
          <li v-for="(c, i) in convergences" :key="i">{{ c }}</li>
        </ul>
      </div>
      <div>
        <h3>Tensions to Watch</h3>
        <ul class="bullet-list tensions">
          <li v-for="(t, i) in tensions" :key="i">{{ t }}</li>
        </ul>
      </div>
    </section>

    <!-- Add more context -->
    <section class="section">
      <h3>Start Next Round</h3>
      <p class="hint">Add feedback, new information, or things agents missed. This feeds the next research round.</p>
      <div class="add-row">
        <textarea v-model="feedbackInput" class="textarea" rows="3"
          placeholder="e.g. The geopolitical agent missed TSMC's role in memory supply chain..." />
        <button class="btn-primary" :disabled="!feedbackInput || loading" @click="addFeedback">
          {{ loading ? 'Adding...' : 'Add & Re-run' }}
        </button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { marked } from 'marked'
import { projects as api, output as outputApi } from '../api/index.js'
import TickerCard from '../components/TickerCard.vue'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id
const project = ref(null)
const vision = ref({})
const feedbackInput = ref('')
const loading = ref(false)

const reportHtml = computed(() =>
  project.value?.morning_report ? marked(project.value.morning_report) : ''
)
const topPicks = computed(() => vision.value?.top_picks_by_layer || {})
const plausibilityRanking = computed(() => vision.value?.plausibility_ranking || [])
const convergences = computed(() => vision.value?.key_convergences || [])
const tensions = computed(() => vision.value?.key_tensions || [])
const overallPct = computed(() =>
  Math.round((vision.value?.overall_confidence || 0) * 100)
)

const addFeedback = async () => {
  if (!feedbackInput.value) return
  loading.value = true
  try {
    await api.addToBrief(projectId, feedbackInput.value)
    await api.start(projectId)
    router.push(`/project/${projectId}`)
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

onMounted(async () => {
  const [pRes, vRes] = await Promise.all([
    api.get(projectId),
    outputApi.vision(projectId),
  ])
  project.value = pRes.data
  vision.value = vRes.data.vision || {}
})
</script>

<style scoped>
.vision-header {
  display: flex; align-items: center; gap: 1.5rem; margin-bottom: 2rem; flex-wrap: wrap;
}
.back { color: #6b6b80; text-decoration: none; font-size: 0.875rem; }
.back:hover { color: #a78bfa; }
h2 { font-size: 1.5rem; font-weight: 700; flex: 1; }
.confidence-overall { color: #34d399; font-size: 0.9rem; }

.section { margin-bottom: 2.5rem; }
h3 { font-size: 1.1rem; font-weight: 700; margin-bottom: 1rem; color: #a78bfa; }
.report-body {
  background: #12121c; border: 1px solid #1e1e2e; border-radius: 10px;
  padding: 1.5rem; line-height: 1.7; color: #c8c8e0;
}
:deep(.report-body h1), :deep(.report-body h2) { color: #e8e8f0; margin: 1rem 0 0.5rem; }
:deep(.report-body h3) { color: #a78bfa; margin: 0.75rem 0 0.4rem; }
:deep(.report-body ul) { padding-left: 1.2rem; }
:deep(.report-body li) { margin-bottom: 0.3rem; }

.layer-block { margin-bottom: 1.5rem; }
h4.layer-name { color: #818cf8; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.75rem; }
.ticker-grid { display: flex; flex-wrap: wrap; gap: 0.75rem; }

.outcome-row {
  display: flex; gap: 1rem; background: #12121c; border: 1px solid #1e1e2e;
  border-radius: 8px; padding: 0.9rem; margin-bottom: 0.75rem;
}
.outcome-rank { font-size: 1.5rem; font-weight: 700; color: #3a3a50; min-width: 2rem; }
.outcome-desc { color: #c8c8e0; margin-bottom: 0.5rem; font-size: 0.9rem; }
.outcome-meta { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
.plausibility-bar-wrap { width: 80px; height: 4px; background: #1e1e2e; border-radius: 2px; }
.plausibility-bar { display: block; height: 100%; background: #7c3aed; border-radius: 2px; }
.plausibility-num { font-size: 0.8rem; color: #a78bfa; font-weight: 700; }
.strength { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; padding: 0.1rem 0.4rem; border-radius: 4px; }
.strength.strong { background: #12251a; color: #34d399; }
.strength.moderate { background: #1a1a12; color: #fbbf24; }
.strength.weak { background: #251212; color: #f87171; }
.domains-list { font-size: 0.75rem; color: #5555688; }

.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
.bullet-list { list-style: none; padding: 0; }
.bullet-list li {
  padding: 0.5rem 0.75rem; background: #12121c; border-left: 2px solid #7c3aed;
  margin-bottom: 0.5rem; border-radius: 0 6px 6px 0; font-size: 0.875rem; color: #c8c8e0;
}
.tensions li { border-left-color: #f59e0b; }

.hint { color: #6b6b80; font-size: 0.875rem; margin-bottom: 0.75rem; }
.textarea {
  width: 100%; padding: 0.75rem 1rem; background: #12121c; border: 1px solid #1e1e2e;
  border-radius: 8px; color: #e8e8f0; font-size: 0.9rem; outline: none; resize: vertical;
}
.textarea:focus { border-color: #7c3aed; }
.add-row { display: flex; flex-direction: column; gap: 0.75rem; }
.btn-primary {
  align-self: flex-start; padding: 0.65rem 1.25rem; background: #7c3aed; color: #fff;
  border: none; border-radius: 8px; font-weight: 600; cursor: pointer;
}
.btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
