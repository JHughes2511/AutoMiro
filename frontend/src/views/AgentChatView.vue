<template>
  <div class="chat-view">
    <div class="chat-header">
      <router-link :to="`/project/${projectId}`" class="back">← Swarm</router-link>
      <h2>{{ domainLabel }} Agent</h2>
      <StatusBadge status="complete" />
    </div>

    <div class="messages" ref="messagesEl">
      <div class="agent-intro">
        <p>You're speaking directly with the <strong>{{ domainLabel }}</strong> research agent.
        Ask follow-up questions, challenge findings, or provide new information that may change the analysis.</p>
      </div>
      <div v-for="(msg, i) in messages" :key="i" class="msg" :class="msg.role">
        <div class="msg-body">{{ msg.content }}</div>
      </div>
      <div v-if="loading" class="msg assistant loading-msg">
        <div class="msg-body">Agent thinking...</div>
      </div>
    </div>

    <div class="input-row">
      <textarea
        v-model="input"
        class="chat-input"
        rows="2"
        placeholder="Ask the agent, challenge a finding, or add new data..."
        @keydown.enter.exact.prevent="send"
      />
      <button class="send-btn" :disabled="!input.trim() || loading" @click="send">Send</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { projects as api } from '../api/index.js'
import StatusBadge from '../components/StatusBadge.vue'

const route = useRoute()
const projectId = route.params.id
const domain = route.params.domain
const input = ref('')
const messages = ref([])
const loading = ref(false)
const messagesEl = ref(null)

const domainLabels = {
  finance: 'Finance', technology: 'Technology', geopolitical: 'Geopolitical',
  market_sentiment: 'Market Sentiment', risk: 'Risk', supply_chain: 'Supply Chain',
  regulatory: 'Regulatory', competitive: 'Competitive Intel',
}
const domainLabel = computed(() => domainLabels[domain] || domain)

const send = async () => {
  const msg = input.value.trim()
  if (!msg || loading.value) return
  messages.value.push({ role: 'user', content: msg })
  input.value = ''
  loading.value = true
  await nextTick()
  messagesEl.value?.scrollTo({ top: messagesEl.value.scrollHeight, behavior: 'smooth' })

  try {
    const res = await api.chat(projectId, domain, msg)
    messages.value.push({ role: 'assistant', content: res.data.response })
    await nextTick()
    messagesEl.value?.scrollTo({ top: messagesEl.value.scrollHeight, behavior: 'smooth' })
  } catch (e) {
    messages.value.push({ role: 'assistant', content: 'Error reaching agent. Please try again.' })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.chat-view { display: flex; flex-direction: column; height: calc(100vh - 120px); }
.chat-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; }
.back { color: #6b6b80; text-decoration: none; font-size: 0.875rem; }
.back:hover { color: #a78bfa; }
h2 { font-size: 1.3rem; font-weight: 700; flex: 1; }

.messages {
  flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 0.75rem;
  padding-bottom: 1rem;
}

.agent-intro {
  background: #12121c; border: 1px solid #1e1e2e; border-radius: 10px;
  padding: 1rem; color: #8888a0; font-size: 0.875rem; line-height: 1.5;
}

.msg { max-width: 80%; }
.msg.user { align-self: flex-end; }
.msg.assistant { align-self: flex-start; }

.msg-body {
  padding: 0.75rem 1rem; border-radius: 10px;
  font-size: 0.9rem; line-height: 1.6; white-space: pre-wrap;
}
.user .msg-body { background: #7c3aed; color: #fff; }
.assistant .msg-body { background: #12121c; border: 1px solid #1e1e2e; color: #c8c8e0; }
.loading-msg .msg-body { opacity: 0.5; animation: pulse 1.5s infinite; }
@keyframes pulse { 0%, 100% { opacity: 0.5; } 50% { opacity: 0.2; } }

.input-row { display: flex; gap: 0.75rem; padding-top: 1rem; border-top: 1px solid #1e1e2e; }
.chat-input {
  flex: 1; padding: 0.75rem 1rem; background: #12121c; border: 1px solid #1e1e2e;
  border-radius: 8px; color: #e8e8f0; font-size: 0.9rem; outline: none; resize: none;
}
.chat-input:focus { border-color: #7c3aed; }
.send-btn {
  padding: 0.75rem 1.25rem; background: #7c3aed; color: #fff; border: none;
  border-radius: 8px; font-weight: 600; cursor: pointer;
}
.send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
