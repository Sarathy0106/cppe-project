<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from './components/Navbar.vue'

const route = useRoute()
const isLoginPage = computed(() => route.path === '/login')
</script>

<template>
  <div class="min-h-screen bg-slate-50 text-slate-900 transition-colors dark:bg-slate-950 dark:text-slate-100 font-sans antialiased selection:bg-indigo-500 selection:text-white">
    <!-- Navbar (Hidden on Login) -->
    <Navbar v-if="!isLoginPage" />

    <!-- Main Container -->
    <main :class="[!isLoginPage ? 'mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8' : '']">
      <router-view />
    </main>

    <!-- Footer (Hidden on Login) -->
    <footer v-if="!isLoginPage" class="mt-16 border-t border-slate-200/80 bg-white/50 py-6 text-center text-xs text-slate-500 dark:border-slate-800 dark:bg-slate-900/50 dark:text-slate-400">
      <div class="mx-auto max-w-7xl px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <span>🎓 CampusVoice Capstone</span>
          <span>·</span>
          <span>Wipro CPPE (Cloud Platform & Big Data Engineering)</span>
        </div>
        <div class="flex items-center gap-4 text-[11px]">
          <span>AWS Serverless Lakehouse</span>
          <span>•</span>
          <span>Bedrock Claude Haiku 4.5 & Titan Embeddings</span>
          <span>•</span>
          <span>KMS Encrypted</span>
        </div>
      </div>
    </footer>
  </div>
</template>
