<template>
  <div class="brief-view">
    <!-- Step 1: Enter brief -->
    <div v-if="step === 'brief'" class="step">
      <h2>New Research Brief</h2>
      <p class="hint">Describe what you want to investigate. Speak naturally — agents will ask follow-up questions.</p>
      <input v-model="name" class="input" placeholder="Project name (e.g. Data Center Stack 2025)" />
      <textarea v-model="brief" class="textarea" rows="6"
        placeholder="e.g. I'm looking into investing in stocks across the data center infrastructure stack: Memory → Power → Autonomous → Quantum → Compute Commodity. I want to identify 3-5 tickers per layer with potential for 5x in 7 years..." />
      <button class="btn-primary" :disabled="!name || !brief || loading" @click="submitBrief">
        {{ loading ? 'Thinking...' : 'Get Clarifying Questions →' }}
      </button>
    </div>

    <!-- Step 2: Clarifying questions -->
    <div v-if="step === 'clarify'" class="step">
      <h2>Before the swarm starts</h2>
      <p class="hint">Answer these to help agents work from a sharper frame. Skip any you're not sure about.</p>
      <div v-for="(q, i) in questions" :key="i" class="question-block">
        <div class="q-meta">
          <span class="q-category">{{ q.category }}</span>
          <span class="q-why">{{ q.why_it_matters }}</span>
        </div>
        <label class="q-text">{{ q.question }}</label>
        <input v-model="answers[q.question]" class="input" placeholder="Your answer (or leave blank to skip)" />
      </div>
      <div class="btn-row">
        <button class="btn-secondary" @click="step = 'brief'">← Back</button>
        <button class="btn-primary" :disabled="loading" @click="submitClarifications">
          {{ loading ? 'Structuring scope...' : 'Launch Agent Swarm →' }}
        </button>
      </div>
    </div>

    <!-- Step 3: Scope preview + confirm -->
    <div v-if="step === 'confirm'" class="step">
      <h2>Scope structured</h2>
      <p class="hint">Here's what the agents will work from. You can launch now or add more context.</p>
      <div class="scope-card">
        <div class="scope-row"><b>Objective:</b> {{ scope.objective }}</div>
        <div class="scope-row"><b>Time horizon:</b> {{ scope.time_horizon }}</div>
        <div class="scope-row"><b>Success metric:</b> {{ scope.success_metric }}</div>
        <div class="scope-row" v-if="scope.layers?.length"><b>Layers:</b> {{ scope.layers.join(' → ') }}</div>
        <div class="scope-row">
          <b>Domains activating:</b>
          <span v-for="d in scope.domains_needed" :key="d" class="domain-chip">{{ d }}</span>
        </div>
        <div class="scope-row" v-if="scope.suggested_tickers?.length">
          <b>Candidate tickers:</b> {{ scope.suggested_tickers.join(', ') }}
        </div>
      </div>
      <div class="add-row">
        <input v-model="addInput" class="input" placeholder="Add more context before launching (optional)..." />
        <button class="btn-secondary" :disabled="!addInput" @click="addContext">Add</button>
      </div>
      <div class="btn-row">
        <button class="btn-secondary" @click="step = 'clarify'">← Back</button>
        <button class="btn-primary" :disabled="loading" @click="launch">
          {{ loading ? 'Launching...' : '⬡ Launch Swarm' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { projects as api } from '../api/index.js'

const router = useRouter()
const step = ref('brief')
const name = ref('')
const brief = ref('')
const questions = ref([])
const answers = reactive({})
const scope = ref({})
const addInput = ref('')
const loading = ref(false)
let projectId = null

const submitBrief = async () => {
  loading.value = true
  try {
    const res = await api.create(name.value, brief.value)
    projectId = res.data.project_id
    const qRes = await api.clarify(projectId)
    questions.value = qRes.data.questions
    step.value = 'clarify'
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const submitClarifications = async () => {
  loading.value = true
  try {
    const res = await api.submitClarifications(projectId, answers)
    scope.value = res.data.scope
    step.value = 'confirm'
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const addContext = async () => {
  if (!addInput.value) return
  const res = await api.addToBrief(projectId, addInput.value)
  scope.value = res.data.scope
  addInput.value = ''
}

const launch = async () => {
  loading.value = true
  try {
    await api.start(projectId)
    router.push(`/project/${projectId}`)
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}
</script>

<style scoped>
.brief-view { max-width: 720px; margin: 0 auto; }
.step h2 { font-size: 1.6rem; font-weight: 700; margin-bottom: 0.5rem; }
.hint { color: #6b6b80; margin-bottom: 1.5rem; line-height: 1.6; }

.input {
  width: 100%; padding: 0.75rem 1rem; background: #12121c;
  border: 1px solid #1e1e2e; border-radius: 8px; color: #e8e8f0;
  font-size: 0.95rem; margin-bottom: 1rem; outline: none;
}
.input:focus { border-color: #7c3aed; }

.textarea {
  width: 100%; padding: 0.75rem 1rem; background: #12121c;
  border: 1px solid #1e1e2e; border-radius: 8px; color: #e8e8f0;
  font-size: 0.95rem; margin-bottom: 1rem; outline: none; resize: vertical;
}
.textarea:focus { border-color: #7c3aed; }

.btn-primary {
  padding: 0.75rem 1.5rem; background: #7c3aed; color: #fff;
  border: none; border-radius: 8px; font-size: 1rem; font-weight: 600;
  cursor: pointer; transition: background 0.15s;
}
.btn-primary:hover:not(:disabled) { background: #6d28d9; }
.btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-secondary {
  padding: 0.75rem 1.5rem; background: #1e1e2e; color: #a0a0b8;
  border: 1px solid #2a2a3e; border-radius: 8px; font-size: 1rem;
  font-weight: 600; cursor: pointer;
}
.btn-row { display: flex; gap: 1rem; margin-top: 1.5rem; }

.question-block { margin-bottom: 1.5rem; }
.q-meta { display: flex; gap: 0.75rem; margin-bottom: 0.4rem; align-items: center; }
.q-category {
  font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
  background: #1c1530; color: #a78bfa; padding: 0.15rem 0.5rem; border-radius: 999px;
}
.q-why { font-size: 0.8rem; color: #5555688; }
.q-text { display: block; color: #c8c8e0; font-weight: 500; margin-bottom: 0.5rem; }

.scope-card {
  background: #12121c; border: 1px solid #1e1e2e; border-radius: 12px;
  padding: 1.5rem; margin-bottom: 1.5rem;
}
.scope-row { margin-bottom: 0.75rem; color: #c8c8e0; font-size: 0.9rem; line-height: 1.5; }
.domain-chip {
  display: inline-block; background: #1c1530; color: #a78bfa;
  padding: 0.15rem 0.5rem; border-radius: 999px; font-size: 0.75rem;
  margin: 0.2rem 0.25rem 0 0;
}

.add-row { display: flex; gap: 0.75rem; margin-bottom: 1rem; }
.add-row .input { margin-bottom: 0; }
</style>
