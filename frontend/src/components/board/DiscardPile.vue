<template>
  <!-- The discard piles, face up for everyone. Used cards can be bought at the
       Black Market, taken with a card that allows it, or moved by the admin. -->
  <transition name="discard">
    <div v-if="open" class="discard" role="dialog" aria-label="Discard pile" @click.self="$emit('close')">
      <section class="discard__panel">
        <header class="discard__head">
          <h3 class="discard__title">Discard pile</h3>
          <div class="discard__tabs" role="tablist">
            <button
              v-for="t in TABS"
              :key="t.deck"
              type="button"
              role="tab"
              :aria-selected="tab === t.deck"
              :class="{ 'is-active': tab === t.deck }"
              @click="tab = t.deck"
            >{{ t.label }} <span class="discard__count">{{ (discards[t.deck] || []).length }}</span></button>
          </div>
          <button type="button" class="discard__close" aria-label="Close" @click="$emit('close')">×</button>
        </header>

        <p v-if="tab === 'collectable' && myPicks > 0" class="discard__banner discard__banner--pick">
          ♻️ You may take {{ myPicks }} card{{ myPicks === 1 ? '' : 's' }} from this pile.
        </p>
        <p v-else-if="tab === 'collectable' && canBuy" class="discard__banner">
          🕶️ You're at the Black Market: buy any one of these for 2.5 hours.
        </p>
        <p v-else-if="tab === 'collectable'" class="discard__hint">
          Used collectables end up here. They can be bought at the Black Market.
        </p>

        <div v-if="!cards.length" class="discard__empty">Nothing has been discarded yet.</div>
        <div v-else class="discard__grid">
          <div v-for="c in cards" :key="c.uid" class="discard__slot">
            <CardFace :card="c" size="sm" />
            <div v-if="tab === 'collectable'" class="discard__actions">
              <button v-if="myPicks > 0" type="button" class="discard__btn discard__btn--go" @click="board.takeFromDiscard(c.uid)">
                Take
              </button>
              <button v-else-if="canBuy" type="button" class="discard__btn discard__btn--buy" @click="buy(c)">
                Buy · 2.5h
              </button>
              <div v-if="isAdmin" class="discard__admin">
                <select v-model="giveTo[c.uid]" class="discard__select" aria-label="Give to">
                  <option :value="undefined" disabled>Give to…</option>
                  <option v-for="p in players" :key="p.user_id" :value="p.user_id">{{ p.username }}</option>
                </select>
                <button
                  type="button"
                  class="discard__btn"
                  :disabled="giveTo[c.uid] === undefined"
                  title="Admin: move this card into a player's hand"
                  @click="board.takeFromDiscard(c.uid, giveTo[c.uid])"
                >Give</button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </transition>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import CardFace from '@/components/board/CardFace.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  board: { type: Object, required: true },
  // state.discards: { collectable: [...], scenario: [...], assignment: [...] }, newest first
  discards: { type: Object, default: () => ({}) },
  myPicks: { type: Number, default: 0 },
  // On the Black Market tile this turn, having rolled and not bought yet
  canBuy: { type: Boolean, default: false },
  isAdmin: { type: Boolean, default: false },
  players: { type: Array, default: () => [] },
  // Which pile to show when it opens
  initialTab: { type: String, default: 'collectable' }
})

const emit = defineEmits(['close'])

const TABS = [
  { deck: 'collectable', label: 'Collectables' },
  { deck: 'scenario', label: 'Scenario cards' },
  { deck: 'assignment', label: 'Assignment slips' }
]

const tab = ref(props.initialTab)
watch(() => props.open, (o) => { if (o) tab.value = props.initialTab })
const giveTo = reactive({})
const cards = computed(() => props.discards?.[tab.value] || [])

function buy(card) {
  props.board.purchase('black_market', card.uid)
  emit('close')
}
</script>

<style scoped>
.discard {
  position: fixed;
  inset: 0;
  z-index: 1050;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(11, 15, 25, 0.75);
  backdrop-filter: blur(3px);
}

.discard__panel {
  width: min(960px, 100%);
  max-height: min(760px, 100%);
  display: flex;
  flex-direction: column;
  border-radius: 14px;
  background: linear-gradient(180deg, #1A1F2E, #121726);
  border: 1px solid rgba(234, 179, 8, 0.35);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
  font-family: 'Barlow Condensed', 'Segoe UI', sans-serif;
  color: #E2E8F0;
  overflow: hidden;
}

.discard__head {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.15);
}

.discard__title {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #FDE68A;
}

.discard__tabs {
  display: flex;
  gap: 4px;
  padding: 3px;
  border-radius: 9px;
  background: #0B0F19;
}

.discard__tabs button {
  padding: 4px 12px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: #94A3B8;
  font-family: inherit;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
}

.discard__tabs button.is-active { background: #EAB308; color: #1c1917; }

.discard__count {
  margin-left: 2px;
  padding: 0 5px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.2);
  font-size: 0.75rem;
}

.discard__close {
  margin-left: auto;
  width: 32px;
  height: 32px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  border-radius: 8px;
  background: transparent;
  color: #CBD5E1;
  font-size: 1.3rem;
  line-height: 1;
  cursor: pointer;
}

.discard__banner,
.discard__hint {
  margin: 12px 16px 0;
  padding: 8px 12px;
  border-radius: 8px;
  font-family: 'Segoe UI', system-ui, sans-serif;
  font-size: 0.88rem;
}

.discard__banner { background: rgba(234, 179, 8, 0.12); color: #FDE68A; }
.discard__banner--pick { background: rgba(45, 212, 191, 0.12); color: #5EEAD4; }
.discard__hint { padding: 0; color: #64748B; }

.discard__empty {
  padding: 40px 16px;
  text-align: center;
  color: #64748B;
}

.discard__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 12px;
  padding: 14px 16px 18px;
  overflow-y: auto;
}

.discard__slot {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.discard__slot :deep(.card-face) { flex: 1; }

.discard__actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.discard__admin { display: flex; gap: 4px; }

.discard__select {
  flex: 1;
  min-width: 0;
  padding: 2px 4px;
  border-radius: 6px;
  font-size: 0.8rem;
}

.discard__btn {
  padding: 4px 10px;
  border-radius: 7px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: #0f1420;
  color: #CBD5E1;
  font-family: inherit;
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
}

.discard__btn:disabled { opacity: 0.4; cursor: not-allowed; }
.discard__btn:hover:not(:disabled) { border-color: #EAB308; color: #FDE68A; }
.discard__btn--go { border-color: rgba(45, 212, 191, 0.6); color: #5EEAD4; }
.discard__btn--buy { border-color: rgba(234, 179, 8, 0.6); color: #FDE68A; }

.discard-enter-active,
.discard-leave-active { transition: opacity 0.2s ease; }
.discard-enter-from,
.discard-leave-to { opacity: 0; }
</style>
