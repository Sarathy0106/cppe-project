<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const userEmail = computed(() => authStore.user?.email || 'User')
const isAdmin = computed(() => authStore.isAdmin)

const navLinks = computed(() => [
  { name: 'Dashboard', path: '/', icon: '📊' },
  { name: 'Feedback Explorer', path: '/explorer', icon: '🔍' },
  { name: 'Ask AI & Agent', path: '/ask', icon: '🤖' },
  ...(isAdmin.value ? [{ name: 'Data Pipeline', path: '/upload', icon: '🚀' }] : []),
  { name: 'Security Controls', path: '/security', icon: '🛡️' },
])

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <header class="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/90">
    <div class="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
      <!-- Brand -->
      <div class="flex items-center gap-8">
        <router-link to="/" class="flex items-center gap-3 group">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white shadow-md shadow-indigo-500/20 group-hover:scale-105 transition-transform">
            <span class="text-xl">🎓</span>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <span class="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
                CampusVoice
              </span>
              <span class="rounded bg-indigo-50 px-1.5 py-0.5 text-[10px] font-semibold text-indigo-700 dark:bg-indigo-950/80 dark:text-indigo-300">
                Wipro CPPE
              </span>
            </div>
            <p class="text-[11px] text-slate-500 dark:text-slate-400">
              Feedback Intelligence & Big Data
            </p>
          </div>
        </router-link>

        <!-- Desktop Navigation -->
        <nav class="hidden md:flex items-center gap-1">
          <router-link
            v-for="link in navLinks"
            :key="link.path"
            :to="link.path"
            class="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors"
            :class="[
              route.path === link.path
                ? 'bg-indigo-50 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400 font-semibold'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'
            ]"
          >
            <span>{{ link.icon }}</span>
            <span>{{ link.name }}</span>
          </router-link>
        </nav>
      </div>

      <!-- User Menu -->
      <div class="flex items-center gap-3">
        <!-- Role badge -->
        <div class="hidden sm:flex flex-col items-end">
          <span class="text-xs font-medium text-slate-900 dark:text-white truncate max-w-[160px]">
            {{ userEmail }}
          </span>
          <span
            class="rounded px-1.5 py-0.2 text-[10px] font-semibold uppercase tracking-wider"
            :class="isAdmin
              ? 'bg-purple-100 text-purple-800 dark:bg-purple-950/70 dark:text-purple-300'
              : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/70 dark:text-emerald-300'"
          >
            {{ isAdmin ? 'Admin' : 'Viewer' }}
          </span>
        </div>

        <!-- Logout button -->
        <button
          type="button"
          @click="handleLogout"
          class="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:border-slate-300 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
        >
          <span>🚪</span>
          <span>Sign Out</span>
        </button>
      </div>
    </div>

    <!-- Mobile Navigation Subbar -->
    <div class="flex md:hidden overflow-x-auto border-t border-slate-100 px-4 py-2 dark:border-slate-800 gap-1 scrollbar-none">
      <router-link
        v-for="link in navLinks"
        :key="link.path"
        :to="link.path"
        class="flex shrink-0 items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium"
        :class="[
          route.path === link.path
            ? 'bg-indigo-50 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400 font-semibold'
            : 'text-slate-600 dark:text-slate-400'
        ]"
      >
        <span>{{ link.icon }}</span>
        <span>{{ link.name }}</span>
      </router-link>
    </div>
  </header>
</template>
