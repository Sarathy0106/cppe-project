<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
} from 'chart.js'
import { Bar, Doughnut, Line } from 'vue-chartjs'
import KpiCard from '../components/KpiCard.vue'
import Spinner from '../components/Spinner.vue'
import EmptyState from '../components/EmptyState.vue'
import {
  api,
  type KpiData,
  type SentimentByDeptItem,
  type CategoryCountItem,
  type MonthlyTrendItem,
} from '../services/api'

ChartJS.register(
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement
)

const loading = ref(true)
const error = ref('')

const kpis = ref<KpiData | null>(null)
const sentimentByDept = ref<SentimentByDeptItem[]>([])
const categoryCounts = ref<CategoryCountItem[]>([])
const monthlyTrend = ref<MonthlyTrendItem[]>([])

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const [kpiRes, deptRes, catRes, trendRes] = await Promise.all([
      api.getKpis(),
      api.getSentimentByDept(),
      api.getCategoryCounts(),
      api.getMonthlyTrend(),
    ])
    kpis.value = kpiRes
    sentimentByDept.value = deptRes
    categoryCounts.value = catRes
    monthlyTrend.value = trendRes
  } catch (err: any) {
    error.value = err.message || 'Failed to load dashboard statistics'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})

// --- Stacked Bar Chart: Sentiment by Department ---
const barChartData = computed(() => {
  const labels = sentimentByDept.value.map((d) => d.department)
  const positive = sentimentByDept.value.map((d) => d.positive)
  const neutral = sentimentByDept.value.map((d) => d.neutral)
  const negative = sentimentByDept.value.map((d) => d.negative)

  return {
    labels,
    datasets: [
      {
        label: 'Positive',
        backgroundColor: '#10b981',
        data: positive,
        borderRadius: 4,
      },
      {
        label: 'Neutral',
        backgroundColor: '#f59e0b',
        data: neutral,
        borderRadius: 4,
      },
      {
        label: 'Negative',
        backgroundColor: '#f43f5e',
        data: negative,
        borderRadius: 4,
      },
    ],
  }
})

const barChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    x: { stacked: true },
    y: { stacked: true, beginAtZero: true },
  },
  plugins: {
    legend: { position: 'top' as const },
  },
}

// --- Doughnut Chart: Category Distribution ---
const doughnutChartData = computed(() => {
  const labels = categoryCounts.value.map((c) => c.category)
  const data = categoryCounts.value.map((c) => c.count)

  return {
    labels,
    datasets: [
      {
        data,
        backgroundColor: [
          '#6366f1',
          '#8b5cf6',
          '#ec4899',
          '#06b6d4',
          '#14b8a6',
          '#f97316',
          '#84cc16',
        ],
      },
    ],
  }
})

const doughnutChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom' as const },
  },
}

// --- Line Chart: Monthly Trend ---
const lineChartData = computed(() => {
  const labels = monthlyTrend.value.map((m) => m.month)
  const totals = monthlyTrend.value.map((m) => m.total)
  const negShare = monthlyTrend.value.map((m) => m.negative_share)

  return {
    labels,
    datasets: [
      {
        label: 'Total Volume',
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        data: totals,
        tension: 0.3,
        yAxisID: 'y',
      },
      {
        label: 'Negative Share (%)',
        borderColor: '#f43f5e',
        backgroundColor: 'rgba(244, 63, 94, 0.1)',
        data: negShare,
        tension: 0.3,
        yAxisID: 'y1',
      },
    ],
  }
})

const lineChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    y: {
      type: 'linear' as const,
      display: true,
      position: 'left' as const,
      beginAtZero: true,
    },
    y1: {
      type: 'linear' as const,
      display: true,
      position: 'right' as const,
      grid: { drawOnChartArea: false },
      beginAtZero: true,
      max: 100,
    },
  },
}
</script>

<template>
  <div class="space-y-8">
    <!-- Header -->
    <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Executive Feedback Intelligence
        </h1>
        <p class="text-sm text-slate-500 dark:text-slate-400">
          Real-time aggregated metrics from Athena Curated Data Lake & Comprehend AI
        </p>
      </div>
      <button
        type="button"
        @click="loadData"
        :disabled="loading"
        class="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm transition-all hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 disabled:opacity-50"
      >
        <Spinner v-if="loading" size="sm" />
        <span>🔄 Refresh Metrics</span>
      </button>
    </div>

    <!-- Error Banner -->
    <div v-if="error" class="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
      <div class="flex items-center gap-2 font-semibold">
        <span>⚠️ Error</span>
      </div>
      <p class="mt-1">{{ error }}</p>
    </div>

    <!-- Loading Skeleton -->
    <div v-if="loading && !kpis" class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
      <div v-for="i in 4" :key="i" class="h-32 animate-pulse rounded-2xl bg-slate-200 dark:bg-slate-800" />
    </div>

    <!-- KPI Grid -->
    <div v-else-if="kpis" class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
      <KpiCard
        title="Total Student Feedback"
        :value="kpis.total_feedback"
        subtitle="Across all terms & branches"
        icon="📝"
      />
      <KpiCard
        title="Positive Sentiment"
        :value="`${kpis.pct_positive}%`"
        subtitle="Satisfied student responses"
        trend="up"
        icon="😊"
      />
      <KpiCard
        title="Negative Sentiment"
        :value="`${kpis.pct_negative}%`"
        subtitle="Critical complaints & issues"
        trend="down"
        icon="⚠️"
      />
      <KpiCard
        title="Academic Departments"
        :value="kpis.num_departments"
        subtitle="Reporting units active"
        icon="🏛️"
      />
    </div>

    <!-- Charts Section -->
    <div class="grid grid-cols-1 gap-8 lg:grid-cols-2">
      <!-- Stacked Bar: Sentiment by Dept -->
      <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h3 class="text-base font-semibold text-slate-900 dark:text-white">
          Sentiment by Department
        </h3>
        <p class="text-xs text-slate-500 dark:text-slate-400 mb-4">
          Breakdown of Positive, Neutral, and Negative sentiments
        </p>
        <div class="h-72">
          <Bar v-if="sentimentByDept.length" :data="barChartData" :options="barChartOptions" />
          <EmptyState v-else title="No department data" />
        </div>
      </div>

      <!-- Doughnut: Category Distribution -->
      <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h3 class="text-base font-semibold text-slate-900 dark:text-white">
          Category Distribution
        </h3>
        <p class="text-xs text-slate-500 dark:text-slate-400 mb-4">
          Proportion of feedback by institutional category
        </p>
        <div class="h-72">
          <Doughnut v-if="categoryCounts.length" :data="doughnutChartData" :options="doughnutChartOptions" />
          <EmptyState v-else title="No category data" />
        </div>
      </div>

      <!-- Line: Monthly Trend (Full Width) -->
      <div class="lg:col-span-2 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h3 class="text-base font-semibold text-slate-900 dark:text-white">
          Monthly Feedback Volume & Complaint Share
        </h3>
        <p class="text-xs text-slate-500 dark:text-slate-400 mb-4">
          Historical trend analysis across partition intervals
        </p>
        <div class="h-80">
          <Line v-if="monthlyTrend.length" :data="lineChartData" :options="lineChartOptions" />
          <EmptyState v-else title="No trend data" />
        </div>
      </div>
    </div>
  </div>
</template>
