<template>
  <div class="chat-view">
    <div class="chat-header">
      <router-link :to="`/project/${projectId}`" class="back">← Swarm</router-link>
      <h2>{{ domainLabel }} Agent</h2>
      <StatusBadge status="complete" />
    </div>

    <!-- Key findings panel -->
    <div class="findings-panel" :class="{ expanded: findingsOpen }">
      <button class="findings-toggle" @click="findingsOpen = !findingsOpen">
        <span>Key Findings</span>
        <span class="toggle-icon">{{ findingsOpen ? '▲' : '▼' }}</span>
      </button>
      <div v-if="findingsOpen" class="findings-body" v-html="findingsHtml"></div>
    </div>

    <!-- Messages -->
    <div class="messages" ref="messagesEl">
      <div v-if="messages.length === 0" class="empty-chat">
        Ask a follow-up question, challenge a finding, or provide new information.
      </div>
      <div v-for="(msg, i) in messages" :key="i" class="msg" :class="msg.role">
        <div class="msg-body" v-html="renderMessage(msg.content)"></div>
      </div>
      <div v-if="loading" class="msg assistant">
        <div class="msg-body thinking">
          <span></span><span></span><span></span>
        </div>
      </div>
    </div>

    <!-- Input -->
    <div class="input-area">
      <button class="clear-btn" @click="clearChat" title="Clear chat display (agent memory retained)">
        Clear
      </button>
      <textarea
        v-model="input"
        class="chat-input"
        rows="2"
        placeholder="Ask the agent, challenge a finding, or add new data... (Enter to send)"
        @keydown.enter.exact.prevent="send"
      />
      <button class="send-btn" :disabled="!input.trim() || loading" @click="send">Send</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import { projects as api } from '../api/index.js'
import StatusBadge from '../components/StatusBadge.vue'

const route = useRoute()
const projectId = route.params.id
const domain = route.params.domain
const input = ref('')
const messages = ref([])
const loading = ref(false)
const findingsOpen = ref(false)
const findings = ref('')
const messagesEl = ref(null)

const storageKey = `automiro_chat_${projectId}_${domain}`

const domainLabels = {
  finance: 'Finance', technology: 'Technology', geopolitical: 'Geopolitical',
  market_sentiment: 'Market Sentiment', risk: 'Risk', supply_chain: 'Supply Chain',
  regulatory: 'Regulatory', competitive: 'Competitive Intel',
}
const domainLabel = computed(() => domainLabels[domain] || domain)

const findingsHtml = computed(() => findings.value ? marked(findings.value) : 'No findings available yet.')

const renderMessage = (content) => marked(content || '')

const scrollToBottom = async () => {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

const saveHistory = () => {
  localStorage.setItem(storageKey, JSON.stringify(messages.value))
}

const loadHistory = () => {
  try {
    const saved = localStorage.getItem(storageKey)
    if (saved) messages.value = JSON.parse(saved)
  } catch (e) {}
}

const clearChat = () => {
  messages.value = []
  localStorage.removeItem(storageKey)
}

const send = async () => {
  const msg = input.value.trim()
  if (!msg || loading.value) return
  messages.value.push({ role: 'user', content: msg })
  input.value = ''
  loading.value = true
  saveHistory()
  await scrollToBottom()

  try {
    const res = await api.chat(projectId, domain, msg)
    messages.value.push({ role: 'assistant', content: res.data.response })
    saveHistory()
    await scrollToBottom()
  } catch (e) {
    messages.value.push({ role: 'assistant', content: 'Error reaching agent. Please try again.' })
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  loadHistory()
  try {
    const res = await api.get(projectId)
    const agentState = res.data.agent_states?.[domain]
    if (agentState?.current_findings) {
      findings.value = agentState.current_findings
    }
  } catch (e) {}
  await scrollToBottom()
})
</script>

<style scoped>
.chat-view {
  display: flex; flex-direction: column; height: calc(100vh - 120px); gap: 0.75rem;
}

.chat-header {
  display: flex; align-items: center; gap: 1rem; flex-shrink: 0;
}
.back { color: #6b6b80; text-decoration: none; font-size: 0.875rem; }
.back:hover { color: #a78bfa; }
h2 { font-size: 1.3rem; font-weight: 700; flex: 1; }

/* Findings panel */
.findings-panel {
  background: #0d0d14; border: 1px solid #1e1e2e; border-radius: 10px;
  flex-shrink: 0; overflow: hidden;
}
.findings-toggle {
  width: 100%; display: flex; justify-content: space-between; align-items: center;
  padding: 0.75rem 1rem; background: none; border: none; color: #a78bfa;
  font-size: 0.875rem; font-weight: 600; cursor: pointer; text-align: left;
}
.findings-toggle:hover { background: #12121c; }
.toggle-icon { font-size: 0.7rem; }
.findings-body {
  padding: 0 1rem 1rem; border-top: 1px solid #1e1e2e;
  max-height: 300px; overflow-y: auto; color: #c8c8e0; font-size: 0.875rem; line-height: 1.7;
}
:deep(.findings-body h1), :deep(.findings-body h2) { color: #e8e8f0; font-size: 1rem; margin: 0.75rem 0 0.3rem; }
:deep(.findings-body h3) { color: #a78bfa; font-size: 0.875rem; margin: 0.6rem 0 0.25rem; }
:deep(.findings-body strong) { color: #e8e8f0; }
:deep(.findings-body ul), :deep(.findings-body ol) { padding-left: 1.25rem; }
:deep(.findings-body li) { margin-bottom: 0.2rem; }
:deep(.findings-body table) { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
:deep(.findings-body th) { background: #1e1e2e; padding: 0.4rem 0.6rem; text-align: left; color: #a78bfa; }
:deep(.findings-body td) { padding: 0.35rem 0.6rem; border-bottom: 1px solid #1e1e2e; }
:deep(.findings-body p) { margin-bottom: 0.5rem; }

/* Messages */
.messages {
  flex: 1; overflow-y: auto; display: flex; flex-direction: column;
  gap: 0.6rem; min-height: 0;
}
.empty-chat {
  text-align: center; color: #3a3a50; font-size: 0.875rem;
  margin-top: 2rem; font-style: italic;
}

.msg { max-width: 82%; }
.msg.user { align-self: flex-end; }
.msg.assistant { align-self: flex-start; max-width: 90%; }

.msg-body {
  padding: 0.7rem 1rem; border-radius: 12px;
  font-size: 0.875rem; line-height: 1.65;
}
.user .msg-body {
  background: #5b21b6; color: #f0ecff; border-bottom-right-radius: 3px;
}
.assistant .msg-body {
  background: #12121c; border: 1px solid #1e1e2e; color: #d0d0e8;
  border-bottom-left-radius: 3px;
}

/* Markdown inside assistant messages */
:deep(.assistant .msg-body h1),
:deep(.assistant .msg-body h2) { color: #e8e8f0; font-size: 1rem; margin: 0.6rem 0 0.3rem; }
:deep(.assistant .msg-body h3) { color: #a78bfa; font-size: 0.875rem; margin: 0.5rem 0 0.2rem; }
:deep(.assistant .msg-body strong) { color: #e8e8f0; }
:deep(.assistant .msg-body ul), :deep(.assistant .msg-body ol) { padding-left: 1.2rem; margin: 0.3rem 0; }
:deep(.assistant .msg-body li) { margin-bottom: 0.2rem; }
:deep(.assistant .msg-body p) { margin-bottom: 0.4rem; }
:deep(.assistant .msg-body p:last-child) { margin-bottom: 0; }
:deep(.assistant .msg-body table) { width: 100%; border-collapse: collapse; font-size: 0.8rem; margin: 0.4rem 0; }
:deep(.assistant .msg-body th) { background: #1a1a2e; padding: 0.35rem 0.6rem; color: #a78bfa; text-align: left; }
:deep(.assistant .msg-body td) { padding: 0.3rem 0.6rem; border-bottom: 1px solid #1e1e2e; }
:deep(.assistant .msg-body code) {
  background: #1a1a2e; padding: 0.1rem 0.35rem; border-radius: 3px;
  font-family: monospace; font-size: 0.82rem; color: #c4b5fd;
}
:deep(.assistant .msg-body hr) { border: none; border-top: 1px solid #1e1e2e; margin: 0.5rem 0; }

/* Thinking dots */
.thinking { display: flex; gap: 4px; align-items: center; padding: 0.85rem 1rem; }
.thinking span {
  width: 6px; height: 6px; background: #4a4a60; border-radius: 50%;
  animation: bounce 1.2s infinite;
}
.thinking span:nth-child(2) { animation-delay: 0.2s; }
.thinking span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce { 0%, 80%, 100% { transform: translateY(0); } 40% { transform: translateY(-5px); } }

/* Input area */
.input-area {
  display: flex; gap: 0.6rem; align-items: flex-end;
  padding-top: 0.75rem; border-top: 1px solid #1e1e2e; flex-shrink: 0;
}
.chat-input {
  flex: 1; padding: 0.7rem 0.9rem; background: #12121c; border: 1px solid #1e1e2e;
  border-radius: 10px; color: #e8e8f0; font-size: 0.875rem; outline: none;
  resize: none; font-family: inherit; line-height: 1.5;
}
.chat-input:focus { border-color: #5b21b6; }
.send-btn {
  padding: 0.7rem 1.1rem; background: #7c3aed; color: #fff; border: none;
  border-radius: 10px; font-weight: 600; cursor: pointer; font-size: 0.875rem;
  white-space: nowrap;
}
.send-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.clear-btn {
  padding: 0.7rem 0.8rem; background: transparent; color: #4a4a60;
  border: 1px solid #1e1e2e; border-radius: 10px; cursor: pointer;
  font-size: 0.8rem; white-space: nowrap;
}
.clear-btn:hover { color: #f87171; border-color: #f8717140; }
</style>
