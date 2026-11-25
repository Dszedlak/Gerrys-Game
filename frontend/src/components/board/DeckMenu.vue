<template>
  <!-- Clicking a deck on the board: the scenario deck (draw & play, shuffle, played cards)
       or the collectable deck (buy, shuffle, the discard pile / Black Market) -->
  <transition name="deckmenu">
    <div v-if="open" class="deckmenu" :class="`deckmenu--${deck}`" role="dialog" :aria-label="meta.title" @click.self="$emit('close')">
      <section class="deckmenu__panel">
        <header class="deckmenu__head">
          <span class="deckmenu__icon">{{ meta.icon }}</span>
          <div>
            <h3 class="deckmenu__title">{{ meta.title }}</h3>
            <div class="deckmenu__sub">{{ drawCount }} in the deck · {{ discardCount }} {{ deck === 'scenario' ? 'played' : 'used' }}</div>
          </div>
          <button type="button" class="deckmenu__close" aria-label="Close" @click="$emit('close')">×</button>
        </header>

        <!-- Scenario: the card in play, or draw & play one -->
        <template v-if="deck === 'scenario'">
          <button v-if="eventInPlay" type="button" class="deckmenu__btn deckmenu__btn--main" @click="$emit('show-event')">
            <span>🃏 Show “{{ state.event.title }}”</span>
            <small>{{ state.event.done ? 'The last card played' : 'The card in play right now' }}</small>
          </button>
          <button
            type="button"
            class="deckmenu__btn"
            :class="{ 'deckmenu__btn--main': !eventInPlay }"
            :disabled="Boolean(drawBlocker)"
            :title="drawBlocker || 'Draw the top card; it is shown to everyone and played'"
            @click="draw"
          >
            <span>🃏 Draw &amp; play a scenario card</span>
            <small>{{ drawBlocker || (isMyTurn ? 'Shown to everyone, and played out' : `Admin: draws for ${currentName}`) }}</small>
          </button>
        </template>

        <!-- Collectables: buy as many as you like -->
        <div v-else class="deckmenu__buy" :class="{ 'is-off': Boolean(buyBlocker) }">
          <div class="deckmenu__buy-head">
            <span>🛒 Buy collectables</span>
            <small>{{ buyBlocker || `${price} each · any number (keep to your hand limit by the end of your turn)` }}</small>
          </div>
          <div v-if="!buyBlocker" class="deckmenu__buy-row">
            <span class="deckmenu__qty">
              <button type="button" :disabled="qty <= 1" aria-label="One fewer" @click="qty--">−</button>
              <strong>{{ qty }}</strong>
              <button type="button" :disabled="qty >= maxQty" aria-label="One more" @click="qty++">+</button>
            </span>
            <button type="button" class="deckmenu__go" @click="buy">Buy {{ qty }} · {{ totalPrice }}</button>
          </div>
        </div>

        <button
          type="button"
          class="deckmenu__btn"
          :disabled="Boolean(shuffleBlocker)"
          :title="shuffleBlocker || 'Put the discards back in and shuffle'"
          @click="shuffle"
        >
          <span>🔀 Shuffle the deck</span>
          <small>{{ shuffleBlocker || shuffleNote }}</small>
        </button>

        <button type="button" class="deckmenu__btn" :disabled="!discardCount" @click="$emit('show-discards')">
          <span>🗂️ {{ deck === 'scenario' ? 'See the played scenario cards' : 'See the discard pile (Black Market)' }}</span>
          <small>{{ discardCount ? `${discardCount} on the discard pile` : 'Nothing discarded yet' }}</small>
        </button>
      </section>
    </div>
  </transition>
</template>

<script setup>
import { askConfirm } from '@/composables/useConfirm'
import { ref, computed, watch } from 'vue'
import { formatPrice } from '@/components/board/boardLayout'

const props = defineProps({
  open: { type: Boolean, default: false },
  // 'scenario' or 'collectable'
  deck: { type: String, default: 'scenario' },
  board: { type: Object, required: true },
  state: { type: Object, default: null },
  playersById: { type: Object, default: () => ({}) },
  myUserId: { type: [Number, String], default: null },
  isAdmin: { type: Boolean, default: false },
  // Collectables: on a Collectables tile on my turn, after rolling
  canBuy: { type: Boolean, default: false },
  // Minutes per collectable (doubled under Democracy)
  unitMinutes: { type: Number, default: 60 }
})

const emit = defineEmits(['close', 'show-discards', 'show-event'])

const META = {
  scenario: { icon: '🃏', title: 'Scenario deck' },
  collectable: { icon: '🎴', title: 'Collectable deck' }
}
const meta = computed(() => META[props.deck] || META.scenario)

const drawCount = computed(() => props.state?.decks?.[props.deck]?.draw ?? 0)
const discardCount = computed(() => props.state?.decks?.[props.deck]?.discard ?? 0)

const started = computed(() => Boolean(props.state?.started))
const currentId = computed(() => props.state?.turn?.user_id ?? null)
const currentName = computed(() => props.playersById[currentId.value]?.username || 'the current player')
const isMyTurn = computed(() => started.value && currentId.value === props.myUserId)
const eventInPlay = computed(() => Boolean(props.state?.event))
const eventActive = computed(() => Boolean(props.state?.event && !props.state.event.done))

const drawBlocker = computed(() => {
  if (!started.value) return 'The game has not started'
  if (!isMyTurn.value && !props.isAdmin) return `Only ${currentName.value} can draw on their turn`
  if (eventActive.value) return 'A scenario card is still being played'
  if (props.state?.pending) return 'A card is still waiting on a decision'
  if (!drawCount.value && !discardCount.value) return 'The scenario deck is empty'
  return ''
})

const shuffleBlocker = computed(() => (!props.isAdmin && !isMyTurn.value ? 'You can shuffle on your turn' : ''))
const shuffleNote = computed(() => {
  const n = discardCount.value
  const base = `The ${n} ${props.deck === 'scenario' ? 'played' : 'used'} card${n === 1 ? '' : 's'} go back in`
  return props.deck === 'collectable' ? `${base} (this empties the Black Market)` : base
})

// --- buying ------------------------------------------------------------------
const qty = ref(1)
watch(() => props.open, (o) => { if (o) qty.value = 1 })
const maxQty = computed(() => Math.max(1, Math.min(50, drawCount.value + discardCount.value)))
const price = computed(() => formatPrice(props.unitMinutes))
const totalPrice = computed(() => formatPrice(props.unitMinutes * qty.value))
const buyBlocker = computed(() => {
  if (!props.canBuy) return 'Land on a Collectables tile on your turn to buy'
  if (!drawCount.value && !discardCount.value) return 'The collectable deck is empty'
  return ''
})

function buy() {
  props.board.purchase('collectable', null, qty.value)
  emit('close')
}

function draw() {
  emit('close')
  props.board.drawScenario()
}

async function shuffle() {
  const extra = props.deck === 'collectable' ? ' This empties the Black Market.' : ''
  if (await askConfirm(`Shuffle the ${props.deck} deck, with its discards put back in?${extra}`)) {
    props.board.shuffleDeck(props.deck)
    emit('close')
  }
}
</script>

<style scoped>
.deckmenu {
  --tone: #8B5CF6;
  position: absolute;
  inset: 0;
  z-index: 44;
  display: grid;
  place-items: center;
  padding: 16px;
  background: rgba(11, 15, 25, 0.5);
}

.deckmenu--collectable { --tone: #14B8A6; }

.deckmenu__panel {
  width: min(380px, 100%);
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px 16px 16px;
  border-radius: 16px;
  background: linear-gradient(180deg, #1A1F2E, #121726);
  border: 1px solid color-mix(in srgb, var(--tone) 65%, transparent);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.55), 0 0 30px color-mix(in srgb, var(--tone) 18%, transparent);
  color: #E2E8F0;
  text-align: left;
}

.deckmenu__head { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
.deckmenu__icon { font-size: 1.8rem; }

.deckmenu__title {
  margin: 0;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.45rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: color-mix(in srgb, var(--tone) 45%, #fff);
}

.deckmenu__sub { font-size: 0.8rem; color: #94A3B8; }

.deckmenu__close {
  margin-left: auto;
  align-self: flex-start;
  width: 28px;
  height: 28px;
  padding: 0;
  border-radius: 50%;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: transparent;
  color: #CBD5E1;
  font-size: 1.1rem;
  line-height: 1;
  cursor: pointer;
}

.deckmenu__btn {
  display: grid;
  gap: 2px;
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: rgba(148, 163, 184, 0.07);
  color: #E2E8F0;
  font-size: 0.98rem;
  font-weight: 700;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.deckmenu__btn small, .deckmenu__buy small { font-size: 0.78rem; font-weight: 400; color: #94A3B8; }
.deckmenu__btn:hover:not(:disabled) { border-color: var(--tone); background: color-mix(in srgb, var(--tone) 14%, transparent); }
.deckmenu__btn:disabled { opacity: 0.5; cursor: not-allowed; }

.deckmenu__btn--main {
  border-color: color-mix(in srgb, var(--tone) 70%, transparent);
  background: color-mix(in srgb, var(--tone) 20%, transparent);
}

.deckmenu__buy {
  display: grid;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid color-mix(in srgb, var(--tone) 70%, transparent);
  background: color-mix(in srgb, var(--tone) 16%, transparent);
}

.deckmenu__buy.is-off { opacity: 0.6; border-color: rgba(148, 163, 184, 0.3); background: rgba(148, 163, 184, 0.07); }
.deckmenu__buy-head { display: grid; gap: 2px; font-weight: 700; }
.deckmenu__buy-row { display: flex; align-items: center; gap: 10px; }

.deckmenu__qty {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  overflow: hidden;
}

.deckmenu__qty button {
  width: 32px;
  height: 32px;
  border: 0;
  background: transparent;
  color: #E2E8F0;
  font-size: 1.1rem;
  font-weight: 800;
  cursor: pointer;
}

.deckmenu__qty button:disabled { opacity: 0.3; cursor: not-allowed; }
.deckmenu__qty strong { min-width: 28px; text-align: center; font-size: 1.1rem; }

.deckmenu__go {
  flex: 1;
  padding: 8px 12px;
  border-radius: 9px;
  border: 1px solid var(--tone);
  background: color-mix(in srgb, var(--tone) 35%, transparent);
  color: #fff;
  font-weight: 800;
  cursor: pointer;
}

.deckmenu-enter-active, .deckmenu-leave-active { transition: opacity 0.18s ease; }
.deckmenu-enter-from, .deckmenu-leave-to { opacity: 0; }
</style>
