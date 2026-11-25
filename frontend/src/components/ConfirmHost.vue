<template>
  <!-- In-game confirmation dialogs (see composables/useConfirm.js) -->
  <transition name="confirm">
    <div v-if="current" class="confirm" role="alertdialog" aria-modal="true" :aria-label="current.title" @click.self="answer(false)">
      <section class="confirm__panel" :class="{ 'is-danger': current.danger }">
        <div class="confirm__icon" aria-hidden="true">{{ current.danger ? '⚠️' : '❔' }}</div>
        <h2 class="confirm__title">{{ current.title }}</h2>
        <p v-if="current.detail" class="confirm__detail">{{ current.detail }}</p>
        <div class="confirm__buttons">
          <button type="button" class="confirm__btn confirm__btn--cancel" @click="answer(false)">{{ current.cancelText }}</button>
          <button ref="okBtn" type="button" class="confirm__btn confirm__btn--ok" @click="answer(true)">{{ current.confirmText }}</button>
        </div>
      </section>
    </div>
  </transition>
</template>

<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { registerConfirmHost } from '@/composables/useConfirm'

const current = ref(null)
const okBtn = ref(null)
const queue = []

function show(request) {
  return new Promise(resolve => {
    queue.push({ ...request, resolve })
    if (!current.value) next()
  })
}

async function next() {
  current.value = queue.shift() || null
  if (current.value) {
    await nextTick()
    okBtn.value?.focus()
  }
}

function answer(ok) {
  const req = current.value
  if (!req) return
  req.resolve(ok)
  next()
}

function onKey(e) {
  if (!current.value) return
  if (e.key === 'Escape') answer(false)
}

let unregister = null
onMounted(() => {
  unregister = registerConfirmHost(show)
  window.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => {
  unregister?.()
  window.removeEventListener('keydown', onKey)
})
</script>

<style scoped>
.confirm {
  position: fixed;
  inset: 0;
  z-index: 3000;
  display: grid;
  place-items: center;
  padding: 18px;
  background: rgba(3, 6, 12, 0.65);
  backdrop-filter: blur(3px);
}

.confirm__panel {
  width: min(420px, 100%);
  padding: 22px 22px 18px;
  border-radius: 18px;
  background: linear-gradient(180deg, #1A1F2E, #121726);
  border: 1px solid rgba(234, 179, 8, 0.6);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6), 0 0 30px rgba(234, 179, 8, 0.12);
  color: #E2E8F0;
  text-align: center;
}

.confirm__panel.is-danger { border-color: rgba(239, 68, 68, 0.65); box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6), 0 0 30px rgba(239, 68, 68, 0.15); }

.confirm__icon { font-size: 1.8rem; margin-bottom: 4px; }

.confirm__title {
  margin: 0;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.55rem;
  font-weight: 800;
  line-height: 1.2;
  color: #F8FAFC;
}

.confirm__detail { margin: 8px 0 0; font-size: 0.92rem; line-height: 1.5; color: #CBD5E1; }

.confirm__buttons { display: flex; gap: 10px; margin-top: 18px; }

.confirm__btn {
  flex: 1;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 0.98rem;
  font-weight: 800;
  cursor: pointer;
  transition: transform 0.12s ease, background 0.15s ease;
}

.confirm__btn:hover { transform: translateY(-1px); }

.confirm__btn--cancel {
  border: 1px solid rgba(148, 163, 184, 0.45);
  background: rgba(148, 163, 184, 0.1);
  color: #E2E8F0;
}

.confirm__btn--ok {
  border: 1px solid #EAB308;
  background: linear-gradient(180deg, #FACC15, #EAB308 55%, #CA8A04);
  color: #1c1917;
}

.is-danger .confirm__btn--ok {
  border-color: #EF4444;
  background: linear-gradient(180deg, #EF4444, #B91C1C);
  color: #FEF2F2;
}

.confirm-enter-active, .confirm-leave-active { transition: opacity 0.18s ease; }
.confirm-enter-active .confirm__panel { animation: confirm-in 0.25s cubic-bezier(0.2, 0.9, 0.3, 1.2); }
.confirm-enter-from, .confirm-leave-to { opacity: 0; }

@keyframes confirm-in { from { transform: scale(0.92); opacity: 0; } }
</style>
