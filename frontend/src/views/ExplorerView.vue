<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api, type FeedbackRecord } from '../services/api'
import Spinner from '../components/Spinner.vue'
import EmptyState from '../components/EmptyState.vue'

const loading = ref(false)
const error = ref('')
const items = ref<FeedbackRecord[]>([])
const totalCount = ref(0)

const department = ref('')
const category = ref('')
const sentiment = ref('')
const limit = ref(20)
const offset = ref(0)

const departments = ['CSE', 'ECE', 'MECH', 'CIVIL', 'IT', 'AI_DS', 'MBA']
const categories = ['FACULTY', 'HOSTEL', 'CANTEEN', 'INFRASTRUCTURE', 'EXAMS', 'LIBRARY', 'LABS', 'GENERAL']
const sentiments = ['POSITIVE', 'NEGATIVE', 'NEUTRAL']

async function loadFeedback(resetOffset = false) {
  if (resetOffset) {
    offset.value = 0
  }
  loading.value = true
  error.value = ''
  try {
    const res = await api.getFeedback({
      department: department.value || undefined,
      category: category.value || undefined,
      sentiment: sentiment.value || undefined,
      limit: limit.value,
      offset: offset.value,
    })
    items.value = res.items
    totalCount.value = res.count
  } catch (err: any) {
    error.value = err.message || 'Failed to query feedback records'
  } finally {
    loading.value = false
  }
}

function nextPage() {
  offset.value += limit.value
  loadFeedback()
}

function prevPage() {
  if (offset.value >= limit.value) {
    offset.value -= limit.value
    loadFeedback()
  }
}

function clearFilters() {
  department.value = ''
  category.value = ''
  sentiment.value = ''
  offset.value = 0
  loadFeedback()
}

onMounted(() => {
  loadFeedback()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Curated Feedback Explorer
        </h1>
        <p class="text-sm text-slate-500 dark:text-slate-400">
          Search sanitized student voices securely stored in partitioned Parquet lake
        </p>
      </div>
      <div class="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-300">
        <span>🔒 Zero PII (Amazon Comprehend Redacted)</span>
      </div>
    </div>

    <!-- Filters Bar -->
    <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <div>
          <label class="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
            Department
          </label>
          <select
            v-model="department"
            @change="loadFeedback(true)"
            class="block w-full rounded-xl border border-slate-300 px-3 py-2 text-xs text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
          >
            <option value="">All Departments</option>
            <option v-for="dept in departments" :key="dept" :value="dept">{{ dept }}</option>
          </select>
        </div>

        <div>
          <label class="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
            Category
          </label>
          <select
            v-model="category"
            @change="loadFeedback(true)"
            class="block w-full rounded-xl border border-slate-300 px-3 py-2 text-xs text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
          >
            <option value="">All Categories</option>
            <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
          </select>
        </div>

        <div>
          <label class="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
            Sentiment
          </label>
          <select
            v-model="sentiment"
            @change="loadFeedback(true)"
            class="block w-full rounded-xl border border-slate-300 px-3 py-2 text-xs text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
          >
            <option value="">All Sentiments</option>
            <option v-for="s in sentiments" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>

        <div class="flex items-end gap-2">
          <button
            type="button"
            @click="loadFeedback(false)"
            :disabled="loading"
            class="flex-1 rounded-xl bg-indigo-600 px-3 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50"
          >
            Filter
          </button>
          <button
            type="button"
            @click="clearFilters"
            class="rounded-xl border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-400 dark:hover:bg-slate-800"
          >
            Reset
          </button>
        </div>
      </div>
    </div>

    <!-- Error Banner -->
    <div v-if="error" class="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
      {{ error }}
    </div>

    <!-- Feedback Table -->
    <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div v-if="loading" class="flex items-center justify-center py-16">
        <Spinner size="lg" />
      </div>

      <div v-else-if="items.length === 0" class="py-12">
        <EmptyState title="No feedback matching your filters" description="Try selecting different departments or sentiments" />
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-left text-xs text-slate-700 dark:text-slate-300">
          <thead class="border-b border-slate-200 bg-slate-50 text-[11px] font-semibold uppercase tracking-wider text-slate-600 dark:border-slate-800 dark:bg-slate-950/40 dark:text-slate-400">
            <tr>
              <th scope="col" class="px-4 py-3">ID / Month</th>
              <th scope="col" class="px-4 py-3">Department</th>
              <th scope="col" class="px-4 py-3">Category</th>
              <th scope="col" class="px-4 py-3">Sentiment</th>
              <th scope="col" class="px-6 py-3">Masked Student Feedback</th>
              <th scope="col" class="px-4 py-3 text-center">PII Status</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800/60 font-sans">
            <tr
              v-for="item in items"
              :key="item.feedback_id"
              class="hover:bg-slate-50/80 transition-colors dark:hover:bg-slate-800/40"
            >
              <td class="px-4 py-3 whitespace-nowrap">
                <span class="font-mono text-slate-900 dark:text-slate-100 font-medium">
                  {{ item.feedback_id }}
                </span>
                <p class="text-[10px] text-slate-400">{{ item.month || '2026-06' }}</p>
              </td>
              <td class="px-4 py-3 whitespace-nowrap">
                <span class="rounded bg-slate-100 px-2 py-0.5 font-medium text-slate-800 dark:bg-slate-800 dark:text-slate-300">
                  {{ item.department }}
                </span>
              </td>
              <td class="px-4 py-3 whitespace-nowrap">
                <span class="font-medium text-slate-700 dark:text-slate-300">
                  {{ item.category }}
                </span>
              </td>
              <td class="px-4 py-3 whitespace-nowrap">
                <span
                  class="rounded-full px-2 py-0.5 text-[10px] font-semibold"
                  :class="{
                    'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/70 dark:text-emerald-300': item.sentiment === 'POSITIVE',
                    'bg-rose-100 text-rose-800 dark:bg-rose-950/70 dark:text-rose-300': item.sentiment === 'NEGATIVE',
                    'bg-amber-100 text-amber-800 dark:bg-amber-950/70 dark:text-amber-300': item.sentiment === 'NEUTRAL',
                  }"
                >
                  {{ item.sentiment }}
                </span>
              </td>
              <td class="px-6 py-3 min-w-[280px]">
                <p class="text-xs text-slate-800 dark:text-slate-200 line-clamp-2">
                  {{ item.feedback_text }}
                </p>
              </td>
              <td class="px-4 py-3 text-center whitespace-nowrap">
                <span class="inline-flex items-center gap-1 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-mono text-slate-700 dark:bg-slate-800 dark:text-slate-400">
                  <span>🛡️</span>
                  <span>Masked</span>
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="flex items-center justify-between border-t border-slate-200 px-4 py-3 dark:border-slate-800">
        <div class="text-xs text-slate-500 dark:text-slate-400">
          Showing <span class="font-medium">{{ offset + 1 }}</span> to
          <span class="font-medium">{{ offset + items.length }}</span> (Page {{ Math.floor(offset / limit) + 1 }})
        </div>
        <div class="flex items-center gap-2">
          <button
            type="button"
            @click="prevPage"
            :disabled="offset === 0 || loading"
            class="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-40 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Previous
          </button>
          <button
            type="button"
            @click="nextPage"
            :disabled="items.length < limit || loading"
            class="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-40 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
