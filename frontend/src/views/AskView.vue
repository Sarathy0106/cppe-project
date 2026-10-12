<script setup lang="ts">
import { ref, nextTick } from 'vue'
import {
  api,
  type ChatSource,
  type AgentStep,
} from '../services/api'
import SourceChip from '../components/SourceChip.vue'
import Spinner from '../components/Spinner.vue'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  mode: 'rag' | 'agent'
  sources?: ChatSource[]
  steps?: AgentStep[]
  timestamp: string
}

const activeMode = ref<'rag' | 'agent'>('rag')
const inputQuestion = ref('')
const loading = ref(false)
const selectedSource = ref<ChatSource | null>(null)
const chatContainer = ref<HTMLDivElement | null>(null)

const messages = ref<Message[]>([
  {
    id: 'intro',
    role: 'assistant',
    content: 'Welcome to CampusVoice AI. I can answer questions grounded strictly in curated student feedback using Titan Embeddings & Claude Haiku 4.5. How can I help you today?',
    mode: 'rag',
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  },
])

const suggestions = [
  'What are the main hostel complaints?',
  'Which department has the most negative feedback and why?',
  'Summarize student feedback on canteen food quality',
  'What are students saying about lab facilities and WiFi?',
]

async function scrollToBottom() {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

async function sendQuestion(text?: string) {
  const query = text || inputQuestion.value
  if (!query || !query.trim() || loading.value) return

  const userMsg: Message = {
    id: String(Date.now()),
    role: 'user',
    content: query.trim(),
    mode: activeMode.value,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  }

  messages.value.push(userMsg)
  inputQuestion.value = ''
  loading.value = true
  await scrollToBottom()

  try {
    if (activeMode.value === 'rag') {
      const res = await api.askChat(query.trim())
      messages.value.push({
        id: String(Date.now() + 1),
        role: 'assistant',
        content: res.answer,
        sources: res.sources,
        mode: 'rag',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      })
    } else {
      const res = await api.askAgent(query.trim())
      messages.value.push({
        id: String(Date.now() + 1),
        role: 'assistant',
        content: res.answer,
        steps: res.steps,
        mode: 'agent',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      })
    }
  } catch (err: any) {
    messages.value.push({
      id: String(Date.now() + 1),
      role: 'assistant',
      content: `⚠️ Error: ${err.message || 'Failed to process inquiry with Bedrock.'}`,
      mode: activeMode.value,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

function handleSourceClick(source: ChatSource) {
  selectedSource.value = source
}
</script>

<template>
  <div class="flex h-[calc(100vh-8rem)] flex-col rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 overflow-hidden">
    <!-- Top Bar: Mode Toggle & Header -->
    <div class="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/40">
      <div class="flex items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400">
          <span class="text-xl">🤖</span>
        </div>
        <div>
          <h2 class="text-sm font-semibold text-slate-900 dark:text-white">
            CampusVoice GenAI Intelligence
          </h2>
          <p class="text-xs text-slate-500 dark:text-slate-400">
            Powered by Amazon Bedrock (Titan V2 Embeddings + Claude Haiku 4.5)
          </p>
        </div>
      </div>

      <!-- Mode Selector -->
      <div class="flex items-center rounded-xl bg-slate-200/80 p-1 dark:bg-slate-800">
        <button
          type="button"
          @click="activeMode = 'rag'"
          class="rounded-lg px-3 py-1.5 text-xs font-semibold transition-all"
          :class="activeMode === 'rag'
            ? 'bg-white text-indigo-600 shadow-sm dark:bg-slate-700 dark:text-white'
            : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'"
        >
          📖 RAG Q&A
        </button>
        <button
          type="button"
          @click="activeMode = 'agent'"
          class="rounded-lg px-3 py-1.5 text-xs font-semibold transition-all"
          :class="activeMode === 'agent'
            ? 'bg-white text-indigo-600 shadow-sm dark:bg-slate-700 dark:text-white'
            : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'"
        >
          🧠 ReAct Agent
        </button>
      </div>
    </div>

    <!-- Suggested Question Chips -->
    <div class="border-b border-slate-100 bg-slate-50/30 px-6 py-2.5 dark:border-slate-800/80">
      <div class="flex items-center gap-2 overflow-x-auto scrollbar-none">
        <span class="text-[11px] font-semibold text-slate-400 shrink-0">💡 Suggested:</span>
        <button
          v-for="sug in suggestions"
          :key="sug"
          type="button"
          @click="sendQuestion(sug)"
          class="shrink-0 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-600 transition-colors hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:border-indigo-600 dark:hover:bg-indigo-950/60"
        >
          {{ sug }}
        </button>
      </div>
    </div>

    <!-- Chat Messages Scroll Area -->
    <div ref="chatContainer" class="flex-1 space-y-6 overflow-y-auto p-6">
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="flex flex-col gap-2"
        :class="msg.role === 'user' ? 'items-end' : 'items-start'"
      >
        <div class="flex items-center gap-2 text-[11px] text-slate-400">
          <span>{{ msg.role === 'user' ? 'You' : msg.mode === 'rag' ? 'RAG Assistant' : 'ReAct Autonomous Agent' }}</span>
          <span>·</span>
          <span>{{ msg.timestamp }}</span>
        </div>

        <!-- Bubble -->
        <div
          class="max-w-2xl rounded-2xl px-4 py-3 text-sm leading-relaxed"
          :class="msg.role === 'user'
            ? 'bg-indigo-600 text-white rounded-tr-none'
            : 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-slate-100 rounded-tl-none border border-slate-200/60 dark:border-slate-700/60'"
        >
          <p class="whitespace-pre-wrap">{{ msg.content }}</p>

          <!-- Agent Reasoning Steps -->
          <div v-if="msg.steps && msg.steps.length" class="mt-4 border-t border-slate-200/70 dark:border-slate-700/70 pt-3">
            <details class="group">
              <summary class="cursor-pointer text-xs font-semibold text-indigo-600 dark:text-indigo-400 flex items-center gap-1.5 list-none">
                <span>🔍 View Agent Reasoning Trail ({{ msg.steps.length }} Steps)</span>
                <span class="group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div class="mt-2 space-y-2">
                <div
                  v-for="(step, sIdx) in msg.steps"
                  :key="sIdx"
                  class="rounded-xl border border-slate-200 bg-white/80 p-2.5 text-xs font-mono dark:border-slate-700 dark:bg-slate-900/80"
                >
                  <div class="flex items-center justify-between text-indigo-700 dark:text-indigo-300 font-semibold">
                    <span>Step {{ sIdx + 1 }}: {{ step.tool }}()</span>
                  </div>
                  <div class="mt-1 text-slate-600 dark:text-slate-400">
                    Input: {{ JSON.stringify(step.input) }}
                  </div>
                  <div class="mt-1 text-emerald-700 dark:text-emerald-400">
                    Output: {{ step.output_summary }}
                  </div>
                </div>
              </div>
            </details>
          </div>

          <!-- RAG Grounding Sources -->
          <div v-if="msg.sources && msg.sources.length" class="mt-4 border-t border-slate-200/70 dark:border-slate-700/70 pt-3">
            <p class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-2">
              Cited Curated Excerpts:
            </p>
            <div class="flex flex-wrap gap-1.5">
              <SourceChip
                v-for="(source, srcIdx) in msg.sources"
                :key="srcIdx"
                :source="source"
                :index="srcIdx"
                @click="handleSourceClick"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Thinking Indicator -->
      <div v-if="loading" class="flex items-center gap-3 text-xs text-slate-500">
        <Spinner size="sm" />
        <span class="animate-pulse">Synthesizing response from Amazon Bedrock...</span>
      </div>
    </div>

    <!-- Input Box -->
    <div class="border-t border-slate-200 p-4 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/40">
      <form @submit.prevent="() => sendQuestion()" class="flex items-center gap-3">
        <input
          v-model="inputQuestion"
          type="text"
          :placeholder="activeMode === 'rag' ? 'Ask a question grounded in student feedback (e.g. hostel issues)...' : 'Ask the agent to investigate departments, compute trends, or synthesize complaints...'"
          :disabled="loading"
          class="flex-1 rounded-xl border border-slate-300 px-4 py-2.5 text-sm text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
        />
        <button
          type="submit"
          :disabled="!inputQuestion.trim() || loading"
          class="flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-40"
        >
          <span>Send</span>
          <span>✈️</span>
        </button>
      </form>
    </div>

    <!-- Source Detail Modal -->
    <div
      v-if="selectedSource"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4"
      @click.self="selectedSource = null"
    >
      <div class="max-w-md w-full rounded-2xl bg-white p-6 shadow-xl dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <span class="rounded bg-indigo-100 px-2 py-0.5 text-xs font-semibold text-indigo-700 dark:bg-indigo-900/60 dark:text-indigo-300">
              {{ selectedSource.department }}
            </span>
            <span class="text-xs font-medium text-slate-500">{{ selectedSource.category }}</span>
          </div>
          <button
            type="button"
            @click="selectedSource = null"
            class="text-slate-400 hover:text-slate-600 text-lg"
          >
            ✕
          </button>
        </div>

        <p class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
          Sanitized Student Excerpt
        </p>
        <p class="text-sm text-slate-800 dark:text-slate-200 leading-relaxed bg-slate-50 dark:bg-slate-900/50 p-3 rounded-xl border border-slate-100 dark:border-slate-700/60">
          "{{ selectedSource.text }}"
        </p>

        <div class="mt-4 flex items-center justify-between text-xs text-slate-500">
          <span>Vector Similarity: {{ (selectedSource.score * 100).toFixed(1) }}%</span>
          <span class="font-semibold" :class="{
            'text-emerald-600': selectedSource.sentiment === 'POSITIVE',
            'text-rose-600': selectedSource.sentiment === 'NEGATIVE',
            'text-amber-600': selectedSource.sentiment === 'NEUTRAL',
          }">
            {{ selectedSource.sentiment }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
