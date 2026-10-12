<script setup lang="ts">
defineProps<{
  title: string
  value: string | number
  subtitle?: string
  change?: string
  trend?: 'up' | 'down' | 'neutral'
  icon?: string
}>()
</script>

<template>
  <div class="relative overflow-hidden rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200/80 transition-all hover:shadow-md dark:bg-slate-800/80 dark:ring-slate-700/80 backdrop-blur-sm">
    <div class="flex items-center justify-between">
      <p class="text-sm font-medium tracking-wide text-slate-500 dark:text-slate-400">
        {{ title }}
      </p>
      <div v-if="icon" class="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400">
        <span class="text-lg">{{ icon }}</span>
      </div>
    </div>
    <div class="mt-4 flex items-baseline gap-2">
      <span class="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
        {{ value }}
      </span>
      <span v-if="change" class="text-xs font-medium" :class="[
        trend === 'up' ? 'text-emerald-600 dark:text-emerald-400' :
        trend === 'down' ? 'text-rose-600 dark:text-rose-400' :
        'text-slate-500 dark:text-slate-400'
      ]">
        {{ change }}
      </span>
    </div>
    <p v-if="subtitle" class="mt-1 text-xs text-slate-400 dark:text-slate-500">
      {{ subtitle }}
    </p>
  </div>
</template>
