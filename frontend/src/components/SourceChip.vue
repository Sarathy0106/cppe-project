<script setup lang="ts">
import type { ChatSource } from '../services/api'

defineProps<{
  source: ChatSource
  index: number
}>()

const emit = defineEmits<{
  (e: 'click', source: ChatSource): void
}>()
</script>

<template>
  <button
    type="button"
    @click="emit('click', source)"
    class="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs text-slate-700 transition-all hover:border-indigo-300 hover:bg-indigo-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:border-indigo-500/50 dark:hover:bg-indigo-950/40 text-left"
  >
    <span class="flex h-4 w-4 items-center justify-center rounded-full bg-indigo-100 text-[10px] font-bold text-indigo-700 dark:bg-indigo-900/60 dark:text-indigo-300">
      {{ index + 1 }}
    </span>
    <span class="font-medium text-slate-900 dark:text-slate-100">
      {{ source.department }}
    </span>
    <span class="text-slate-400">·</span>
    <span class="truncate max-w-[100px]">{{ source.category }}</span>
    <span
      class="rounded px-1.5 py-0.2 text-[10px] font-medium"
      :class="{
        'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300': source.sentiment === 'POSITIVE',
        'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300': source.sentiment === 'NEGATIVE',
        'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300': source.sentiment === 'NEUTRAL',
      }"
    >
      {{ source.sentiment }}
    </span>
    <span class="text-[10px] text-slate-400 font-mono">
      {{ (source.score * 100).toFixed(0) }}%
    </span>
  </button>
</template>
