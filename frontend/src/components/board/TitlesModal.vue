<template>
  <!-- The titles: what they pay, what they do, what they need, and how close you are -->
  <transition name="titles">
    <div v-if="open" class="titles" role="dialog" aria-label="Titles" @click.self="$emit('close')">
      <section class="titles__panel">
        <header class="titles__head">
          <div>
            <div class="titles__eyebrow">{{ alert ? '🎖️ New title available' : 'Titles' }}</div>
            <h2 class="titles__title">
              {{ alert && nextTitle ? `You can become ${article(nextTitle)} ${nextTitle}!` : 'Climb the ranks' }}
            </h2>
            <p class="titles__sub">
              You need a Tier 3 job to apply. Titles go up one level at a time, on your turn.
            </p>
          </div>
          <button type="button" class="titles__close" aria-label="Close" @click="$emit('close')">×</button>
        </header>

        <div class="titles__grid">
          <article
            v-for="t in titles"
            :key="t.name"
            class="title-card"
            :class="{ 'is-mine': t.mine, 'is-next': t.isNext, 'is-ready': t.isNext && t.ready }"
          >
            <div class="title-card__top">
              <span class="title-card__icon">{{ ICONS[t.name] || '🎖️' }}</span>
              <div>
                <div class="title-card__name">{{ t.name }}</div>
                <div class="title-card__pay">+{{ t.pay }}m a turn · {{ t.left }} of {{ t.quantity }} left</div>
              </div>
              <span v-if="t.mine" class="title-card__badge">Your title</span>
            </div>
            <div class="title-card__label">What it gives</div>
            <p class="title-card__text">{{ t.abilities }}</p>
            <div class="title-card__label">What it needs</div>
            <ul class="title-card__checks">
              <li v-for="(c, i) in t.checks" :key="i" :class="c.ok ? 'is-ok' : 'is-no'">
                <span>{{ c.ok ? '✓' : '✗' }}</span>{{ c.text }}
              </li>
            </ul>
            <button
              v-if="t.isNext"
              type="button"
              class="title-card__apply"
              :disabled="!t.ready || !isMyTurn"
              :title="!isMyTurn ? 'Apply on your turn' : t.ready ? `Become ${t.name}` : 'You don’t meet all the requirements yet'"
              @click="apply(t)"
            >{{ t.ready ? (isMyTurn ? `Become ${t.name}` : 'Apply on your turn') : 'Not yet' }}</button>
          </article>
        </div>

        <footer class="titles__foot">
          <label v-if="isAdmin" class="titles__admin">
            Admin: set your title
            <select :value="myTitle || ''" @change="(e) => $emit('set-title', e.target.value)">
              <option value="">None</option>
              <option v-for="t in titles" :key="t.name" :value="t.name">{{ t.name }}</option>
            </select>
          </label>
          <span class="titles__spacer" />
          <button type="button" class="titles__btn" @click="$emit('close')">{{ alert ? 'Not now' : 'Close' }}</button>
        </footer>
      </section>
    </div>
  </transition>
</template>

<script setup>
import { askConfirm } from '@/composables/useConfirm'
import { computed } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  // Opened because the next title has just become available
  alert: { type: Boolean, default: false },
  // [{ name, pay, quantity, abilities, left, mine, isNext, ready, checks: [{ ok, text }] }]
  titles: { type: Array, default: () => [] },
  myTitle: { type: String, default: null },
  isMyTurn: { type: Boolean, default: false },
  isAdmin: { type: Boolean, default: false },
  board: { type: Object, required: true }
})

const emit = defineEmits(['close', 'set-title'])

const ICONS = { Manager: '📊', Senior: '⭐', Executive: '💎' }
const nextTitle = computed(() => props.titles.find(t => t.isNext)?.name || null)
const article = (w) => (/^[AEIOU]/i.test(w) ? 'an' : 'a')

async function apply(t) {
  const trade = t.name === 'Manager' ? ' A completed assignment slip is traded in.'
    : t.name === 'Senior' ? ' A Promotion card is used.' : ''
  if (await askConfirm(`Become ${article(t.name)} ${t.name}?${trade}`)) {
    props.board.applyTitle()
    emit('close')
  }
}
</script>

<style scoped>
.titles {
  position: fixed;
  inset: 0;
  z-index: 1044;
  display: grid;
  place-items: center;
  padding: 18px;
  background: rgba(3, 6, 12, 0.72);
  backdrop-filter: blur(3px);
}

.titles__panel {
  width: min(920px, 100%);
  max-height: calc(100vh - 36px);
  overflow-y: auto;
  border-radius: 18px;
  background: linear-gradient(180deg, #1A1F2E, #121726);
  border: 1px solid rgba(234, 179, 8, 0.55);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6);
  color: #E2E8F0;
}

.titles__head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 20px 12px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
}

.titles__eyebrow {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 0.9rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #22D3EE;
}

.titles__title {
  margin: 0;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.8rem;
  font-weight: 800;
  color: #FDE68A;
}

.titles__sub { margin: 2px 0 0; font-size: 0.88rem; color: #94A3B8; }

.titles__close {
  align-self: flex-start;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: transparent;
  color: #CBD5E1;
  font-size: 1.2rem;
  cursor: pointer;
}

.titles__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
  padding: 16px 20px;
}

.title-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.title-card.is-mine { border-color: rgba(234, 179, 8, 0.6); }
.title-card.is-next { border-color: rgba(34, 211, 238, 0.5); }
.title-card.is-ready { border-color: #22C55E; box-shadow: 0 0 0 1px #22C55E, 0 0 24px rgba(34, 197, 94, 0.25); }

.title-card__top { display: flex; align-items: center; gap: 10px; }
.title-card__icon { font-size: 1.8rem; }
.title-card__name { font-family: 'Barlow Condensed', sans-serif; font-size: 1.45rem; font-weight: 800; color: #F8FAFC; }
.title-card__pay { font-size: 0.8rem; color: #86EFAC; }

.title-card__badge {
  margin-left: auto;
  padding: 2px 9px;
  border-radius: 999px;
  background: rgba(234, 179, 8, 0.25);
  color: #FDE68A;
  font-size: 0.72rem;
  font-weight: 700;
}

.title-card__label {
  margin-top: 4px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #94A3B8;
}

.title-card__text { margin: 0; font-size: 0.85rem; line-height: 1.45; color: #CBD5E1; white-space: pre-line; }

.title-card__checks { margin: 0; padding: 0; list-style: none; font-size: 0.85rem; }
.title-card__checks li { display: flex; gap: 6px; padding: 2px 0; }
.title-card__checks li span { width: 14px; font-weight: 800; }
.title-card__checks li.is-ok { color: #BBF7D0; }
.title-card__checks li.is-ok span { color: #4ADE80; }
.title-card__checks li.is-no { color: #CBD5E1; }
.title-card__checks li.is-no span { color: #F87171; }

.title-card__apply {
  margin-top: auto;
  padding: 9px 12px;
  border-radius: 10px;
  border: 1px solid #22C55E;
  background: linear-gradient(180deg, #22C55E, #15803D);
  color: #F0FDF4;
  font-weight: 800;
  cursor: pointer;
}

.title-card__apply:disabled { border-color: rgba(148, 163, 184, 0.25); background: rgba(148, 163, 184, 0.08); color: #94A3B8; cursor: not-allowed; }

.titles__foot {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px 16px;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
}

.titles__spacer { flex: 1; }

.titles__admin { display: flex; align-items: center; gap: 8px; font-size: 0.82rem; color: #94A3B8; }
.titles__admin select {
  padding: 4px 8px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: #0B0F19;
  color: #F1F5F9;
}

.titles__btn {
  padding: 8px 18px;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.45);
  background: rgba(148, 163, 184, 0.1);
  color: #E2E8F0;
  font-weight: 700;
  cursor: pointer;
}

.titles-enter-active, .titles-leave-active { transition: opacity 0.2s ease; }
.titles-enter-from, .titles-leave-to { opacity: 0; }
</style>
