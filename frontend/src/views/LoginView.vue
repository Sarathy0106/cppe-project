<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Spinner from '../components/Spinner.vue'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('admin@campusvoice.local')
const password = ref('CampusVoice@2026!')
const loading = ref(false)
const errorMessage = ref('')

async function handleSubmit() {
  if (!email.value || !password.value) {
    errorMessage.value = 'Please provide both email and password.'
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    await authStore.login(email.value, password.value)
    router.push('/')
  } catch (err: any) {
    errorMessage.value = err.message || 'Login failed. Please verify credentials.'
  } finally {
    loading.value = false
  }
}

function fillCredentials(type: 'admin' | 'viewer') {
  if (type === 'admin') {
    email.value = 'admin@campusvoice.local'
    password.value = 'CampusVoice@2026!'
  } else {
    email.value = 'viewer@campusvoice.local'
    password.value = 'CampusVoice@2026!'
  }
  errorMessage.value = ''
}
</script>

<template>
  <div class="flex min-h-screen flex-col justify-center bg-slate-50 py-12 sm:px-6 lg:px-8 dark:bg-slate-950">
    <div class="sm:mx-auto sm:w-full sm:max-w-md text-center">
      <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-3xl shadow-lg shadow-indigo-500/25 text-white">
        🎓
      </div>
      <h2 class="mt-6 text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
        CampusVoice
      </h2>
      <p class="mt-2 text-sm text-slate-600 dark:text-slate-400">
        AI & Big-Data Student Feedback Intelligence Platform
      </p>
      <div class="mt-2 inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50/70 px-3 py-1 text-xs font-semibold text-indigo-700 dark:border-indigo-900 dark:bg-indigo-950/60 dark:text-indigo-300">
        <span>Wipro CPPE Module 1-4 Capstone</span>
      </div>
    </div>

    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
      <div class="rounded-2xl border border-slate-200/80 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <!-- Demo Quick-Select Buttons -->
        <div class="mb-6 rounded-xl border border-dashed border-indigo-200 bg-indigo-50/50 p-4 dark:border-indigo-900/60 dark:bg-indigo-950/30">
          <p class="text-xs font-semibold uppercase tracking-wider text-indigo-900 dark:text-indigo-300 mb-2">
            🚀 Quick Demo Login
          </p>
          <div class="grid grid-cols-2 gap-2">
            <button
              type="button"
              @click="fillCredentials('admin')"
              class="rounded-lg border border-indigo-200 bg-white px-3 py-2 text-xs font-semibold text-indigo-700 shadow-sm transition-all hover:bg-indigo-50 dark:border-indigo-800 dark:bg-slate-850 dark:text-indigo-300 dark:hover:bg-indigo-900/40"
            >
              👑 Admin Role
            </button>
            <button
              type="button"
              @click="fillCredentials('viewer')"
              class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm transition-all hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-850 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              👀 Viewer Role
            </button>
          </div>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label for="email" class="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Email Address
            </label>
            <input
              id="email"
              v-model="email"
              type="email"
              required
              class="mt-1 block w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              placeholder="user@campusvoice.local"
            />
          </div>

          <div>
            <label for="password" class="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Password
            </label>
            <input
              id="password"
              v-model="password"
              type="password"
              required
              class="mt-1 block w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              placeholder="••••••••••••"
            />
          </div>

          <div v-if="errorMessage" class="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
            {{ errorMessage }}
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            <Spinner v-if="loading" size="sm" color="text-white" />
            <span>{{ loading ? 'Authenticating...' : 'Sign In via Cognito' }}</span>
          </button>
        </form>

        <div class="mt-6 border-t border-slate-100 pt-4 text-center dark:border-slate-800">
          <p class="text-xs text-slate-400">
            Protected by Amazon Cognito User Pool & JWT Authorization
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
