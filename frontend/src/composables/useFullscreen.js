import { ref } from 'vue'

/**
 * useFullscreen
 *
 * Browser full screen for the whole page (hides the tabs, bookmarks and
 * address bar). Shared state, so any button showing it stays in sync, and
 * it follows the user leaving full screen with Esc.
 */
const doc = typeof document !== 'undefined' ? document : null
const isFullscreen = ref(false)
const supported = Boolean(doc && (doc.fullscreenEnabled || doc.webkitFullscreenEnabled))

function current() {
  return doc?.fullscreenElement || doc?.webkitFullscreenElement || null
}

function sync() {
  isFullscreen.value = Boolean(current())
}

if (doc) {
  doc.addEventListener('fullscreenchange', sync)
  doc.addEventListener('webkitfullscreenchange', sync)
}

async function toggleFullscreen() {
  if (!doc) return
  try {
    if (current()) {
      await (doc.exitFullscreen || doc.webkitExitFullscreen).call(doc)
    } else {
      const el = doc.documentElement
      await (el.requestFullscreen || el.webkitRequestFullscreen).call(el)
    }
  } catch (e) {
    console.warn('[fullscreen] not allowed:', e)
  }
  sync()
}

export function useFullscreen() {
  return { isFullscreen, supported, toggleFullscreen }
}
