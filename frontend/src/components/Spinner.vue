<script setup lang="ts">
defineProps<{
  size?: 'sm' | 'md' | 'lg'
  color?: string
}>()
</script>

<template>
  <div
    class="inline-block animate-spin rounded-full border-2 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]"
    :class="[
      size === 'sm' ? 'h-4 w-4 border-2' : size === 'lg' ? 'h-8 w-8 border-3' : 'h-5 w-5 border-2',
      color || 'text-indigo-600 dark:text-indigo-400'
    ]"
    role="status"
  >
    <span class="sr-only">Loading...</span>
  </div>
</template>
