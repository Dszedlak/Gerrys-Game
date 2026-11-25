<template>
  <!-- A new version was put live while this tab was open: ask to refresh,
       so nobody plays on an old copy of the game -->
  <transition name="update">
    <div v-if="available" class="update" role="status">
      <span>🔄 A new version of Gerry's Game is ready.</span>
      <button type="button" class="update__btn" @click="reload">Refresh now</button>
    </div>
  </transition>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const CHECK_MS = 60 * 1000

const available = ref(false)
let timer = null

/** The hashed app script this tab is running (absent on the dev server). */
function currentBuild() {
  const script = [...document.querySelectorAll('script[src]')].find(s => /\/js\/app\.[0-9a-f]+\.js/.test(s.src))
  return script ? script.src.match(/app\.([0-9a-f]+)\.js/)[1] : null
}

async function liveBuild(fetchFn = window.fetch.bind(window)) {
  const res = await fetchFn(`/?v=${Date.now()}`, {
    cache: 'no-store',
    headers: { 'ngrok-skip-browser-warning': '1' }
  })
  if (!res.ok) return null
  const html = await res.text()
  const m = html.match(/\/js\/app\.([0-9a-f]+)\.js/)
  return m ? m[1] : null
}

async function check() {
  const mine = currentBuild()
  if (!mine || available.value) return
  try {
    const live = await liveBuild()
    if (live && live !== mine) available.value = true
  } catch (e) {
    // Offline or the server is restarting: try again next time
  }
}

function reload() {
  window.location.reload()
}

function onVisible() {
  if (document.visibilityState === 'visible') check()
}

onMounted(() => {
  timer = setInterval(check, CHECK_MS)
  document.addEventListener('visibilitychange', onVisible)
})

onBeforeUnmount(() => {
  clearInterval(timer)
  document.removeEventListener('visibilitychange', onVisible)
})
</script>

<style scoped>
.update {
  position: fixed;
  left: 50%;
  bottom: 18px;
  z-index: 2000;
  display: flex;
  align-items: center;
  gap: 12px;
  max-width: calc(100vw - 32px);
  padding: 10px 12px 10px 18px;
  border-radius: 999px;
  background: #1A1F2E;
  border: 1px solid #EAB308;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.55), 0 0 24px rgba(234, 179, 8, 0.2);
  color: #FDE68A;
  font-weight: 600;
  transform: translateX(-50%);
}

.update__btn {
  flex: 0 0 auto;
  padding: 6px 14px;
  border-radius: 999px;
  border: 0;
  background: linear-gradient(180deg, #EAB308, #CA8A04);
  color: #1c1917;
  font-weight: 800;
  cursor: pointer;
}

.update-enter-active, .update-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.update-enter-from, .update-leave-to { opacity: 0; transform: translate(-50%, 12px); }
</style>
