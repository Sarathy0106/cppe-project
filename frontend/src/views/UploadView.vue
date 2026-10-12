<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { api, type PipelineStep } from '../services/api'
import PipelineStepper from '../components/PipelineStepper.vue'
import Spinner from '../components/Spinner.vue'

const router = useRouter()
const authStore = useAuthStore()

const file = ref<File | null>(null)
const isDragging = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const errorMessage = ref('')

const activeBatchId = ref('')
const pipelineStatus = ref('')
const pipelineSteps = ref<PipelineStep[]>([])
let pollTimer: any = null

function handleFileDrop(e: DragEvent) {
  isDragging.value = false
  const dropped = e.dataTransfer?.files[0]
  if (dropped) validateAndSelectFile(dropped)
}

function handleFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files && target.files[0]) {
    validateAndSelectFile(target.files[0])
  }
}

function validateAndSelectFile(f: File) {
  errorMessage.value = ''
  if (!f.name.endsWith('.csv')) {
    errorMessage.value = 'Invalid file type. Please upload a .csv file.'
    return
  }
  if (f.size > 50 * 1024 * 1024) {
    errorMessage.value = 'File is too large. Maximum allowed size is 50 MB.'
    return
  }
  file.value = f
}

async function startUpload() {
  if (!file.value) return

  uploading.value = true
  uploadProgress.value = 0
  errorMessage.value = ''
  pipelineStatus.value = 'INITIATING'
  pipelineSteps.value = []

  try {
    // 1. Get presigned upload URL from Admin API
    const { upload_url, batch_id } = await api.getUploadUrl(file.value.name)
    activeBatchId.value = batch_id

    // 2. Direct S3 PUT upload with progress
    await api.uploadCsvToS3(upload_url, file.value, (pct) => {
      uploadProgress.value = pct
    })

    uploading.value = false
    pipelineStatus.value = 'RUNNING'

    // 3. Poll pipeline execution status
    startPolling(batch_id)
  } catch (err: any) {
    uploading.value = false
    errorMessage.value = err.message || 'Upload failed.'
    pipelineStatus.value = 'FAILED'
  }
}

function startPolling(batchId: string) {
  stopPolling()
  pollTimer = setInterval(async () => {
    try {
      const res = await api.getPipelineStatus(batchId)
      pipelineStatus.value = res.status
      if (res.steps) {
        pipelineSteps.value = res.steps
      }

      if (res.status === 'SUCCEEDED' || res.status === 'FAILED') {
        stopPolling()
      }
    } catch {
      // Continue polling until terminal status or timeout
    }
  }, 4000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <div class="space-y-8">
    <!-- Non-admin guard banner -->
    <div v-if="!authStore.isAdmin" class="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-center dark:border-amber-900/60 dark:bg-amber-950/40">
      <div class="text-3xl mb-2">🔒</div>
      <h3 class="text-base font-semibold text-amber-900 dark:text-amber-200">
        Admin Access Required
      </h3>
      <p class="mt-1 text-xs text-amber-700 dark:text-amber-300">
        You are signed in as a Viewer. Only users in the <code>Admin</code> Cognito group can upload raw datasets and trigger the Step Functions pipeline.
      </p>
    </div>

    <template v-else>
      <!-- Header -->
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Data Ingestion & Pipeline Orchestration
        </h1>
        <p class="text-sm text-slate-500 dark:text-slate-400">
          Upload raw student-feedback CSV to trigger the automated serverless lakehouse pipeline
        </p>
      </div>

      <!-- Drag & Drop Upload Card -->
      <div class="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="handleFileDrop"
          class="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-10 transition-colors"
          :class="isDragging
            ? 'border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/20'
            : 'border-slate-300 hover:border-slate-400 dark:border-slate-700 dark:hover:border-slate-600'"
        >
          <div class="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400">
            <span class="text-3xl">📤</span>
          </div>

          <h3 class="mt-4 text-base font-semibold text-slate-900 dark:text-white">
            {{ file ? file.name : 'Select or drag raw CSV file here' }}
          </h3>
          <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
            {{ file ? `${(file.size / 1024).toFixed(1)} KB — ready to upload` : 'Supports standard CSV format with student feedback rows (Max 50 MB)' }}
          </p>

          <div class="mt-6 flex items-center gap-3">
            <label class="cursor-pointer rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 shadow-sm transition-all hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700">
              <span>Browse Files</span>
              <input type="file" accept=".csv" @change="handleFileSelect" class="hidden" />
            </label>

            <button
              v-if="file"
              type="button"
              @click="startUpload"
              :disabled="uploading"
              class="flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50"
            >
              <Spinner v-if="uploading" size="sm" color="text-white" />
              <span>{{ uploading ? `Uploading (${uploadProgress}%)` : 'Start Pipeline' }}</span>
            </button>
          </div>
        </div>

        <!-- Upload Progress Bar -->
        <div v-if="uploading" class="mt-6">
          <div class="flex items-center justify-between text-xs text-slate-600 dark:text-slate-400 mb-1">
            <span>Direct S3 Upload (Presigned PUT)</span>
            <span class="font-mono">{{ uploadProgress }}%</span>
          </div>
          <div class="h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
            <div
              class="h-full bg-indigo-600 transition-all duration-300"
              :style="{ width: `${uploadProgress}%` }"
            />
          </div>
        </div>

        <!-- Error Banner -->
        <div v-if="errorMessage" class="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
          {{ errorMessage }}
        </div>
      </div>

      <!-- Live Execution Stepper -->
      <div v-if="activeBatchId" class="space-y-4">
        <div class="flex items-center justify-between">
          <p class="text-xs font-mono text-slate-500">
            Batch ID: <span class="font-bold text-slate-700 dark:text-slate-300">{{ activeBatchId }}</span>
          </p>
          <div v-if="pipelineStatus === 'SUCCEEDED'" class="flex items-center gap-3">
            <span class="text-xs font-semibold text-emerald-600">🎉 Execution Succeeded!</span>
            <button
              type="button"
              @click="router.push('/')"
              class="rounded-xl bg-emerald-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-emerald-500"
            >
              View Dashboard →
            </button>
          </div>
        </div>

        <PipelineStepper :steps="pipelineSteps" :status="pipelineStatus" />
      </div>
    </template>
  </div>
</template>
