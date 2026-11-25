<template>
  <!-- My collectables: private hand, plus what I have equipped on the table -->
  <section class="hand" aria-label="Your collectables">
    <header class="hand__head">
      <span class="hand__eyebrow">Your cards</span>
      <span
        class="hand__count"
        :class="{ 'is-over': limitCount > handLimit }"
        :title="`Up to ${handLimit} collectables, job opportunities and promotions in hand, plus ${maxEquipped} equipped. Hospital items don't count.`"
      >
        {{ limitCount }}/{{ handLimit }} in hand · {{ equipped.length }}/{{ maxEquipped }} equipped
      </span>
    </header>

    <button v-if="picks > 0" type="button" class="hand__pick" @click="$emit('open-discard')">
      ♻️ You may take {{ picks }} card{{ picks === 1 ? '' : 's' }} from the discard pile — choose
    </button>

    <p v-if="!hand.length && !equipped.length" class="hand__empty">
      No cards yet. Landing on Collectables, the Job Centre or the Hospital deals cards straight into your hand.
    </p>

    <!-- Equipped: on the table, always working (never used up) -->
    <div class="hand__zone hand__zone--equipped">
      <div class="hand__zone-head">
        <span>🛡️ Equipped <small>always working</small></span>
        <span class="hand__zone-count">{{ equipped.length }}/{{ maxEquipped }}</span>
      </div>
      <p v-if="!equipped.length" class="hand__zone-empty">
        Nothing equipped. Equip a Charm, Hell Bent or Efficiency from your hand and it works on every roll and card, for good.
      </p>
      <div v-else class="hand__cards">
        <div v-for="c in equipped" :key="c.uid" class="hand__slot hand__slot--equipped">
          <span class="hand__active">ACTIVE</span>
          <CardFace :card="c" size="sm" />
          <div class="hand__actions">
            <button type="button" class="hand__btn" title="Take it back into your hand" @click="board.unequipCard(c.uid)">↩ To hand</button>
            <button type="button" class="hand__btn hand__btn--bad" title="Discard it" @click="confirmDiscard(c)">✕</button>
          </div>
        </div>
      </div>
    </div>

    <!-- In hand: private, used once -->
    <div v-if="hand.length" class="hand__zone hand__zone--hand">
      <div class="hand__zone-head">
        <span>🎴 In your hand <small>only you can see these</small></span>
        <span class="hand__zone-count" :class="{ 'is-over': limitCount > handLimit }">{{ limitCount }}/{{ handLimit }}</span>
      </div>
      <div class="hand__cards">
        <div v-for="c in hand" :key="c.uid" class="hand__slot">
          <CardFace :card="c" size="sm" />
          <div class="hand__actions">
            <button
              v-if="c.equip && c.deck === 'collectable'"
              type="button"
              class="hand__btn hand__btn--equip"
              :disabled="equipped.length >= maxEquipped"
              :title="equipped.length >= maxEquipped ? `You already have ${maxEquipped} equipped` : 'Put it on the table: it works all the time'"
              @click="board.equipCard(c.uid)"
            >🛡️ Equip</button>
            <button
              v-else
              type="button"
              class="hand__btn hand__btn--go"
              :disabled="!canAct || Boolean(unusable(c))"
              :title="unusable(c) || 'Use this card'"
              @click="startUse(c)"
            >Use</button>
            <button type="button" class="hand__btn" @click="picking = { uid: c.uid, mode: 'give' }">Give</button>
            <button type="button" class="hand__btn hand__btn--bad" @click="confirmDiscard(c)">✕</button>
          </div>
          <p v-if="canAct && unusable(c)" class="hand__why">{{ unusable(c) }}</p>
          <TargetPicker v-if="picking?.uid === c.uid" :mode="picking.mode" :players="others" @pick="finish" @cancel="picking = null" />
        </div>
      </div>
    </div>

    <button type="button" class="hand__discard" @click="$emit('open-discard')">
      🗑️ Discard pile <span>{{ discardCount }}</span>
    </button>

    <div v-if="slips.length" class="hand__slips">
      📜 Completed assignment slips: <strong>{{ slips.length }}</strong>
      <span class="hand__slip-names">{{ slips.map(s => s.title).join(', ') }}</span>
    </div>
  </section>
</template>

<script setup>
import { askConfirm } from '@/composables/useConfirm'
import { ref, computed, h } from 'vue'
import CardFace from '@/components/board/CardFace.vue'
import { HAND_LIMIT_DECKS } from '@/components/board/boardLayout'

const props = defineProps({
  board: { type: Object, required: true },
  hand: { type: Array, default: () => [] },
  equipped: { type: Array, default: () => [] },
  slips: { type: Array, default: () => [] },
  playersById: { type: Object, default: () => ({}) },
  myUserId: { type: [Number, String], default: null },
  handLimit: { type: Number, default: 5 },
  maxEquipped: { type: Number, default: 2 },
  started: { type: Boolean, default: false },
  discardCount: { type: Number, default: 0 },
  // Cards I may take from the discard pile (from a card that allows it)
  picks: { type: Number, default: 0 },
  // The board state, to tell when a card can't be used right now (and why)
  state: { type: Object, default: null }
})

defineEmits(['open-discard'])

const limitCount = computed(() => props.hand.filter(c => HAND_LIMIT_DECKS.includes(c.deck || 'collectable')).length)

const picking = ref(null)

const me = computed(() => props.playersById[props.myUserId] || null)
const canAct = computed(() => props.started && Boolean(me.value?.alive))

// Cards that only work at certain moments say so, instead of failing when used
const ON_YOUR_TURN = new Set(['Advance', 'Shortcut', 'Remote Access'])
const BLACK_MARKET = 19
const myTurn = computed(() => Boolean(props.state?.started) && props.state?.turn?.user_id === props.myUserId)

function unusable(card) {
  const s = props.state
  if (!s) return ''
  if (s.event && !s.event.done) return `Finish “${s.event.title}” first`
  if (!ON_YOUR_TURN.has(card.title)) return ''
  if (!myTurn.value) return 'Use this on your turn'
  if (me.value?.jailed) return "You can't use this from Jail"
  if (card.title === 'Remote Access' && s.turn?.remote_senate) return 'You already have Remote Access this turn'
  if (card.title === 'Advance') {
    const mine = s.positions?.[String(props.myUserId)]
    const ahead = Object.values(props.playersById).filter(p => {
      const pos = s.positions?.[String(p.user_id)]
      return p.user_id !== props.myUserId && p.alive && !p.jailed && pos > mine && pos <= BLACK_MARKET
    })
    if (!ahead.length) return 'Nobody is ahead of you before the Black Market'
  }
  return ''
}
const others = computed(() =>
  Object.values(props.playersById).filter(p => p.user_id !== props.myUserId && (picking.value?.mode === 'give' || p.alive))
)

function startUse(card) {
  if (card.needs_target) {
    picking.value = { uid: card.uid, mode: 'use' }
  } else {
    props.board.playCard(card.uid)
  }
}

function finish(userId) {
  const p = picking.value
  picking.value = null
  if (!p) return
  if (p.mode === 'give') props.board.giveCard(p.uid, userId)
  else props.board.playCard(p.uid, userId)
}

async function confirmDiscard(card) {
  if (await askConfirm(`Discard “${card.title}”? It goes to the Black Market.`)) {
    props.board.discardCard(card.uid)
  }
}

// Small inline player picker
const TargetPicker = (p, { emit }) =>
  h('div', { class: 'picker' }, [
    h('span', { class: 'picker__ask' }, p.mode === 'give' ? 'Give to:' : 'Use on:'),
    ...p.players.map(pl =>
      h('button', {
        type: 'button',
        class: 'picker__btn',
        style: { '--pawn': pl.color },
        onClick: () => emit('pick', pl.user_id)
      }, [h('span', { class: 'picker__dot' }), pl.username])
    ),
    h('button', { type: 'button', class: 'picker__btn picker__btn--muted', onClick: () => emit('cancel') }, 'Cancel')
  ])
TargetPicker.props = ['mode', 'players']
TargetPicker.emits = ['pick', 'cancel']
</script>

<style scoped>
.hand {
  padding: 10px 12px 12px;
  border-radius: 12px;
  background: linear-gradient(180deg, #1A1F2E, #121726);
  border: 1px solid rgba(20, 184, 166, 0.3);
  font-family: 'Barlow Condensed', 'Segoe UI', sans-serif;
  color: #E2E8F0;
}

.hand__head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 8px;
}

.hand__eyebrow {
  font-size: 0.85rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #5EEAD4;
}

.hand__count {
  font-size: 0.85rem;
  color: #94A3B8;
}

.hand__count.is-over { color: #FDBA74; font-weight: 700; }

.hand__empty {
  margin: 0;
  font-family: 'Segoe UI', system-ui, sans-serif;
  font-size: 0.82rem;
  color: #64748B;
}

.hand__group + .hand__group { margin-top: 10px; }

.hand__label {
  margin-bottom: 4px;
  font-size: 0.78rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #94A3B8;
}

.hand__cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 8px;
}

.hand__slot {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hand__slot :deep(.card-face) {
  flex: 1;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35), inset 0 0 0 2px rgba(255, 255, 255, 0.5);
}

.hand__actions {
  display: flex;
  gap: 4px;
}

.hand__btn {
  flex: 1;
  padding: 3px 0;
  border-radius: 6px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: #0f1420;
  color: #CBD5E1;
  font-family: inherit;
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
}

.hand__btn:hover:not(:disabled) { border-color: #EAB308; color: #FDE68A; }
.hand__btn:disabled { opacity: 0.4; cursor: not-allowed; }
.hand__btn--go { border-color: rgba(45, 212, 191, 0.6); color: #5EEAD4; }
.hand__btn--bad { flex: 0 0 28px; color: #FCA5A5; }

.hand__pick,
.hand__discard {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  margin-top: 10px;
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: rgba(148, 163, 184, 0.06);
  color: #CBD5E1;
  font-family: inherit;
  font-size: 0.95rem;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
}

.hand__discard span {
  padding: 0 7px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.2);
  font-size: 0.8rem;
}

.hand__discard:hover { border-color: #EAB308; color: #FDE68A; }

.hand__pick {
  margin: 0 0 8px;
  border-color: rgba(45, 212, 191, 0.6);
  background: rgba(45, 212, 191, 0.12);
  color: #5EEAD4;
  animation: pick-pulse 1.6s ease-in-out infinite;
}

@keyframes pick-pulse {
  50% { box-shadow: 0 0 0 3px rgba(45, 212, 191, 0.25); }
}

.hand__slips {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid rgba(148, 163, 184, 0.15);
  font-size: 0.95rem;
  color: #FDBA74;
}

.hand__slip-names {
  display: block;
  font-size: 0.8rem;
  color: #94A3B8;
}

:deep(.picker) {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 6px;
  border-radius: 8px;
  background: #0B0F19;
  border: 1px solid rgba(234, 179, 8, 0.4);
}

:deep(.picker__ask) {
  width: 100%;
  font-size: 0.8rem;
  color: #FDE68A;
}

:deep(.picker__btn) {
  --pawn: #94A3B8;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 6px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: #1A1F2E;
  color: #F1F5F9;
  font-family: inherit;
  font-size: 0.85rem;
  cursor: pointer;
}

:deep(.picker__btn:hover) { border-color: #EAB308; }
:deep(.picker__btn--muted) { color: #94A3B8; }

:deep(.picker__dot) {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--pawn);
}
/* Equipped vs in hand: two clearly different trays */
.hand__zone {
  margin-top: 8px;
  padding: 8px 10px 10px;
  border-radius: 10px;
}

.hand__zone--equipped {
  background: linear-gradient(180deg, rgba(234, 179, 8, 0.12), rgba(234, 179, 8, 0.04));
  border: 1px solid rgba(234, 179, 8, 0.55);
}

.hand__zone--hand {
  background: rgba(15, 23, 42, 0.55);
  border: 1px dashed rgba(148, 163, 184, 0.35);
}

.hand__zone-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.hand__zone--equipped .hand__zone-head { color: #FDE68A; }
.hand__zone--hand .hand__zone-head { color: #CBD5E1; }

.hand__zone-head small {
  margin-left: 4px;
  font-size: 0.72rem;
  font-weight: 400;
  letter-spacing: 0.04em;
  text-transform: none;
  color: #94A3B8;
}

.hand__zone-count { font-size: 0.85rem; color: #94A3B8; }
.hand__zone-count.is-over { color: #FDBA74; }

.hand__zone-empty {
  margin: 0;
  font-family: 'Segoe UI', system-ui, sans-serif;
  font-size: 0.78rem;
  color: #A8A29E;
}

.hand__slot--equipped {
  position: relative;
  padding: 4px;
  border-radius: 10px;
  box-shadow: 0 0 0 2px rgba(234, 179, 8, 0.7), 0 0 16px rgba(234, 179, 8, 0.25);
}

.hand__active {
  position: absolute;
  top: -8px;
  right: 8px;
  z-index: 2;
  padding: 1px 8px;
  border-radius: 999px;
  background: #EAB308;
  color: #1c1917;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.1em;
}

.hand__why {
  margin: 0;
  font-family: 'Segoe UI', system-ui, sans-serif;
  font-size: 0.72rem;
  line-height: 1.3;
  color: #FDBA74;
}

.hand__btn--equip { border-color: rgba(234, 179, 8, 0.7); color: #FDE68A; background: rgba(234, 179, 8, 0.12); }
</style>
