<script setup lang="ts">
import type { PipelineStep } from '../services/api'
import Spinner from './Spinner.vue'

const props = defineProps<{
  steps: PipelineStep[]
  status: string
}>()

const standardSteps = [
  { id: 'MaskPII', label: 'Mask PII Entities', desc: 'Comprehend PII redaction & sentiment scoring' },
  { id: 'GlueClean', label: 'ML Classification', desc: 'TF-IDF & Logistic Regression partitioning' },
  { id: 'StartCrawler', label: 'Catalog Sync', desc: 'Glue Data Catalog partition schema update' },
  { id: 'EmbedFeedback', label: 'Bedrock Embeddings', desc: 'Titan Text Embeddings V2 256-d vectors' },
  { id: 'SignManifest', label: 'KMS Manifest Sign', desc: 'Asymmetric RSA_2048 digital signature' },
]

function getStepStatus(stepId: string): 'pending' | 'running' | 'completed' | 'failed' {
  if (props.status === 'FAILED') {
    const found = props.steps.find((s) => s.name === stepId)
    if (found && found.status === 'FAILED') return 'failed'
  }
  
  const stepIdx = props.steps.findIndex((s) => s.name === stepId)
  if (stepIdx !== -1) {
    const step = props.steps[stepIdx]
    if (step.status === 'SUCCEEDED' || step.status === 'COMPLETED') return 'completed'
    if (step.status === 'RUNNING' || step.status === 'IN_PROGRESS') return 'running'
    if (step.status === 'FAILED') return 'failed'
  }

  // If overall pipeline is SUCCEEDED, any step before or completed is completed
  if (props.status === 'SUCCEEDED') return 'completed'

  return 'pending'
}
</script>

<template>
  <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h4 class="text-base font-semibold text-slate-900 dark:text-white">
          Pipeline Execution Progress
        </h4>
        <p class="text-xs text-slate-500 dark:text-slate-400">
          Automated Step Functions state machine orchestration
        </p>
      </div>
      <div class="flex items-center gap-2">
        <span
          class="rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wider"
          :class="{
            'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/70 dark:text-emerald-300': status === 'SUCCEEDED',
            'bg-indigo-100 text-indigo-800 dark:bg-indigo-950/70 dark:text-indigo-300': status === 'RUNNING',
            'bg-rose-100 text-rose-800 dark:bg-rose-950/70 dark:text-rose-300': status === 'FAILED',
            'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300': status === 'PENDING' || !status,
          }"
        >
          {{ status || 'IDLE' }}
        </span>
      </div>
    </div>

    <div class="space-y-4">
      <div
        v-for="(step, idx) in standardSteps"
        :key="step.id"
        class="flex items-start gap-4 rounded-xl p-3 transition-colors"
        :class="{
          'bg-emerald-50/50 dark:bg-emerald-950/20': getStepStatus(step.id) === 'completed',
          'bg-indigo-50/60 dark:bg-indigo-950/30 ring-1 ring-indigo-200 dark:ring-indigo-800': getStepStatus(step.id) === 'running',
          'bg-rose-50/60 dark:bg-rose-950/30': getStepStatus(step.id) === 'failed',
          'opacity-60': getStepStatus(step.id) === 'pending'
        }"
      >
        <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full font-semibold text-xs transition-all"
          :class="{
            'bg-emerald-600 text-white': getStepStatus(step.id) === 'completed',
            'bg-indigo-600 text-white': getStepStatus(step.id) === 'running',
            'bg-rose-600 text-white': getStepStatus(step.id) === 'failed',
            'bg-slate-200 text-slate-600 dark:bg-slate-800 dark:text-slate-400': getStepStatus(step.id) === 'pending',
          }"
        >
          <span v-if="getStepStatus(step.id) === 'completed'">✓</span>
          <Spinner v-else-if="getStepStatus(step.id) === 'running'" size="sm" color="text-white" />
          <span v-else-if="getStepStatus(step.id) === 'failed'">✕</span>
          <span v-else>{{ idx + 1 }}</span>
        </div>

        <div class="flex-1">
          <div class="flex items-center justify-between">
            <p class="text-sm font-medium text-slate-900 dark:text-white">
              {{ step.label }}
            </p>
            <span class="text-xs font-mono capitalize" :class="{
              'text-emerald-600 dark:text-emerald-400 font-semibold': getStepStatus(step.id) === 'completed',
              'text-indigo-600 dark:text-indigo-400 font-semibold': getStepStatus(step.id) === 'running',
              'text-rose-600 dark:text-rose-400 font-semibold': getStepStatus(step.id) === 'failed',
              'text-slate-400': getStepStatus(step.id) === 'pending',
            }">
              {{ getStepStatus(step.id) }}
            </span>
          </div>
          <p class="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            {{ step.desc }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
