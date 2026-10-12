import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'
import { CONFIG } from './config'

async function init() {
  try {
    const res = await fetch('/config.json')
    if (res.ok) {
      const cfg = await res.json()
      if (cfg.apiUrl) CONFIG.API_URL = cfg.apiUrl
      if (cfg.userPoolId) CONFIG.USER_POOL_ID = cfg.userPoolId
      if (cfg.clientId) CONFIG.CLIENT_ID = cfg.clientId
      if (cfg.region) CONFIG.REGION = cfg.region
    }
  } catch {
    // fallback to defaults from config.ts
  }

  const app = createApp(App)
  const pinia = createPinia()

  app.use(pinia)
  app.use(router)
  app.mount('#app')
}

init()
