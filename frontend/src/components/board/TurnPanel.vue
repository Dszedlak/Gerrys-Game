<template>
  <section class="turn" :class="{ 'is-mine': isMyTurn }" aria-live="polite">
    <!-- ============ Rolling for the first turn ============ -->
    <template v-if="state?.phase === 'initiative'">
      <header class="turn__head">
        <span class="turn__eyebrow">{{ initiative.round > 1 ? `Tie-break · roll ${initiative.round}` : 'Before the game' }}</span>
        <h3 class="turn__title">Roll for the first turn</h3>
      </header>
      <p class="turn__text">
        <template v-if="initiative.round > 1">It's a tie at the top: these players roll again.</template>
        <template v-else>Everyone rolls the die. The highest roll goes first.</template>
      </p>
      <ul class="init">
        <li
          v-for="row in initiativeRows"
          :key="row.user_id"
          class="init__row"
          :class="{ 'is-out': !row.inRound, 'is-me': row.user_id === myUserId }"
        >
          <span class="init__dot" :style="{ background: row.color }" />
          <span class="init__name">{{ row.username }}</span>
          <span class="init__roll" :class="{ 'is-waiting': row.roll === null }">
            {{ row.roll === null ? (row.inRound ? 'to roll…' : '') : row.roll }}
          </span>
        </li>
      </ul>
      <button
        v-if="canRollInitiative"
        type="button"
        class="turn__btn turn__btn--primary turn__btn--roll turn__init-all"
        @click="board.initiativeRoll()"
      >🎲 Roll the die</button>
      <p v-else-if="initiativeInRound" class="turn__hint">You've rolled. Waiting for the others…</p>
      <button
        v-if="isAdmin && initiativeWaiting.length"
        type="button"
        class="turn__btn turn__btn--small turn__init-all"
        :title="`Roll for ${initiativeWaiting.join(', ')}`"
        @click="board.initiativeRollAll()"
      >Roll for everyone still to roll ({{ initiativeWaiting.length }})</button>
    </template>

    <!-- ============ Not started (the lobby normally covers this) ============ -->
    <template v-else-if="!state?.started">
      <header class="turn__head">
        <span class="turn__eyebrow">{{ state?.phase === 'jobs' ? 'Before the first turn' : 'Lobby' }}</span>
        <h3 class="turn__title">{{ state?.phase === 'jobs' ? 'Choosing jobs' : 'Waiting to start' }}</h3>
      </header>
      <p class="turn__hint">
        {{ state?.phase === 'jobs' ? 'Everyone picks a Tier 1 job, then the first turn begins.' : 'Waiting for everyone to ready up…' }}
      </p>
    </template>

    <!-- ============ Started ============ -->
    <template v-else>
      <header class="turn__head">
        <span class="turn__eyebrow">Round {{ state.round }}</span>
        <h3 class="turn__title">
          <span class="turn__dot" :style="{ background: currentPlayer?.color }" />
          <template v-if="isMyTurn">Your turn</template>
          <template v-else-if="currentPlayer">{{ currentPlayer.username }}'s turn</template>
          <template v-else>No one to play</template>
        </h3>
      </header>

      <!-- ---------- My turn ---------- -->
      <template v-if="isMyTurn">
        <!-- Servant of the Reaper -->
        <div v-if="!me?.alive" class="turn__block turn__block--reaper">
          <p class="turn__text">You're out of time and serve the Reaper now. Your roll is added to the central counter.</p>
          <button type="button" class="turn__btn turn__btn--primary" :disabled="turn.rolled" @click="board.roll()">
            💀 {{ turn.rolled ? 'Rolled' : 'Roll for the Reaper' }}
          </button>
        </div>

        <!-- In Jail -->
        <div v-else-if="me?.jailed" class="turn__block turn__block--jail">
          <p class="turn__text">
            You're in <strong>Jail</strong>. Pay <strong>{{ jailFeeHours }} hours</strong> to walk to Start
            and carry on with your turn as normal.
          </p>
          <button type="button" class="turn__btn turn__btn--danger" @click="$emit('get-out-of-jail')">
            🔓 Pay {{ jailFeeHours }}h &amp; walk to Start
          </button>
        </div>

        <ol v-else class="steps">
          <!-- 1. Income -->
          <li class="step" :class="stepState(1)">
            <span class="step__mark">{{ turn.paid ? '✓' : '1' }}</span>
            <div class="step__text">
              <span class="step__title">Collect income</span>
              <span class="step__sub" :class="incomeNet >= 0 ? 'is-good' : 'is-bad'">
                {{ turn.paid ? 'Collected' : `${formatSigned(incomeNet)} this turn` }}
              </span>
            </div>
            <button v-if="!turn.paid" type="button" class="step__action step__action--income" @click="board.collectIncome()">
              Collect
            </button>
          </li>

          <!-- 2. Roll -->
          <li class="step" :class="stepState(2)">
            <span class="step__mark">{{ turn.rolled ? '✓' : '2' }}</span>
            <div class="step__text">
              <span class="step__title">Roll the die</span>
              <span class="step__sub">
                {{ turn.rolled ? (lastMoveValue ? `You rolled a ${lastMoveValue}` : 'Rolled') : 'Or click the die on the board' }}
              </span>
            </div>
            <button v-if="!turn.rolled" type="button" class="step__action step__action--roll" @click="board.roll()">
              🎲 Roll
            </button>
            <span v-else-if="lastMoveValue" class="step__pip" :aria-label="`Rolled ${lastMoveValue}`">{{ lastMoveValue }}</span>
          </li>

          <!-- 3. The tile you landed on -->
          <li class="step step--tile" :class="[stepState(3), `step--${tone}`]">
            <span class="step__mark">3</span>
            <div class="step__text">
              <span class="step__title">{{ onTile && myTile ? myTile.label : 'Your tile' }}</span>
              <span v-if="!onTile" class="step__sub">Resolve the tile you land on</span>
              <span v-else-if="dealtText" class="step__sub step__sub--dealt">🎴 {{ dealtText }}</span>
              <span v-else-if="turn.dealt_note" class="step__sub">{{ turn.dealt_note }}</span>
              <span v-else-if="hasActions" class="step__sub">{{ myPending ? 'Your card needs a decision' : 'Actions available on this tile' }}</span>
              <span v-else class="step__sub">{{ description }}</span>
            </div>
            <button
              v-if="onTile && hasActions"
              type="button"
              class="step__action"
              :class="{ 'is-urgent': myPending }"
              @click="$emit('open-actions')"
            >{{ myPending ? '🃏 Decide' : 'Actions' }}</button>
          </li>
        </ol>

        <button
          type="button"
          class="turn__btn turn__btn--end"
          :disabled="Boolean(myPending) || eventInPlay"
          @click="onEndTurn"
        >
          End turn
        </button>
        <!-- Tier 3 job abilities (and an Executive's second one) -->
        <div v-if="abilities.length && me?.alive" class="abilities">
          <div class="abilities__label">Job abilities</div>
          <div v-for="a in abilities" :key="a.slot" class="ability" :title="a.text">
            <div class="ability__text">
              <span class="ability__name">⚡ {{ a.job }}<small v-if="a.slot === 'secondary'"> · executive</small></span>
              <span class="ability__sub">{{ a.automatic || (a.used ? 'Used this turn' : 'Once per turn') }}</span>
            </div>
            <button
              v-if="!a.automatic"
              type="button"
              class="ability__use"
              :disabled="a.used || eventInPlay"
              @click="board.useAbility(a.slot)"
            >{{ a.used ? 'Used' : 'Use' }}</button>
          </div>
        </div>

        <p v-if="eventInPlay" class="turn__hint turn__hint--warn">
          🃏 “{{ state.event.title }}” is being played: finish it before ending your turn.
        </p>
        <p v-if="handOver > 0" class="turn__hint turn__hint--warn">
          🎴 You're holding {{ handOver }} more card{{ handOver === 1 ? '' : 's' }} than your limit: you'll choose what to discard or give away when you end your turn.
        </p>
      </template>

      <!-- ---------- Someone else's turn ---------- -->
      <template v-else>
        <p class="turn__text">
          <template v-if="currentPlayer && !currentPlayer.alive">
            {{ currentPlayer.username }} is rolling for the Reaper.
          </template>
          <template v-else-if="currentPlayer?.jailed">
            {{ currentPlayer.username }} is in Jail.
          </template>
          <template v-else-if="currentTile">
            {{ currentPlayer?.username }} is on <strong>{{ currentTile.label }}</strong>.
          </template>
        </p>
        <p v-if="myPosition !== null" class="turn__hint">Your turn is {{ turnsUntilMine }}.</p>
      </template>

      <!-- Heat limit: you go to Jail -->
      <div v-if="me?.alive && !me?.jailed && me?.heat >= me?.heatMax" class="turn__alarm">
        <span>🚔 You've reached {{ me.heatMax }} heat.</span>
        <button type="button" class="turn__btn turn__btn--danger" @click="confirmJail">Go to Jail</button>
      </div>

      <!-- Admin tools -->
      <details v-if="isAdmin" class="turn__admin">
        <summary>Admin tools</summary>
        <div class="turn__admin-row">
          <button v-if="!isMyTurn && currentPlayer" type="button" class="turn__btn turn__btn--small" @click="board.endTurn()">
            ⏭ End {{ currentPlayer.username }}'s turn
          </button>
          <button
            v-if="!reaperSummoned"
            type="button"
            class="turn__btn turn__btn--small"
            @click="board.summonReaper()"
          >☠️ Summon the Reaper now</button>
          <button type="button" class="turn__btn turn__btn--small" @click="confirmRestart">🔀 Restart (roll for first turn)</button>
          <button type="button" class="turn__btn turn__btn--small turn__btn--bad" @click="confirmReset">Reset board</button>
        </div>
        <div class="turn__admin-label">Change whose turn it is (starts their turn afresh)</div>
        <div class="turn__admin-row">
          <select v-model="turnTarget" class="turn__select" aria-label="Whose turn">
            <option :value="null" disabled>Choose a player…</option>
            <option v-for="p in Object.values(playersById)" :key="p.user_id" :value="p.user_id">
              {{ p.username }}{{ p.user_id === turn.user_id ? ' (now)' : '' }}
            </option>
          </select>
          <button type="button" class="turn__btn turn__btn--small" :disabled="turnTarget === null" @click="confirmSetTurn">
            Make it their turn
          </button>
        </div>
        <div v-if="turn.scenario && !isMyTurn" class="turn__admin-row">
          <button type="button" class="turn__btn turn__btn--small" @click="confirmRedraw">
            🔁 Discard {{ currentPlayer?.username }}'s scenario card &amp; draw another
          </button>
        </div>
        <div class="turn__admin-label">Shuffle a deck (its discard pile goes back in)</div>
        <div class="turn__admin-row">
          <button
            v-for="d in SHUFFLE_DECKS"
            :key="d.deck"
            type="button"
            class="turn__btn turn__btn--small"
            :title="`${deckSize(d.deck)}`"
            @click="confirmShuffle(d)"
          >🔀 {{ d.label }}</button>
        </div>
        <p class="turn__hint">Click any tile to move a pawn by hand. The discard pile lets you hand out used collectables.</p>
      </details>
    </template>
  </section>
</template>

<script setup>
import { askConfirm } from '@/composables/useConfirm'
import { ref, computed } from 'vue'
import { tileTheme, tileDescription, ACTION_TILE_KINDS, dealtSummary } from '@/components/board/boardLayout'

const props = defineProps({
  board: { type: Object, required: true },
  state: { type: Object, default: null },
  // Ledger entries (see BoardView), keyed by user id
  playersById: { type: Object, default: () => ({}) },
  myUserId: { type: [Number, String], default: null },
  isAdmin: { type: Boolean, default: false },
  incomeNet: { type: Number, default: 0 },
  doctorInPlay: { type: Boolean, default: false },
  jailFeeHours: { type: Number, default: 8 },
  serverOffsetMs: { type: Number, default: 0 },
  // 2 under Democracy ("All purchases are double in price")
  priceMultiplier: { type: Number, default: 1 },
  governmentName: { type: String, default: 'Democracy' },
  handSize: { type: Number, default: 0 },
  // [{ slot, job, text, automatic, used }] - my Tier 3 job abilities (see BoardView)
  abilities: { type: Array, default: () => [] },
  handLimit: { type: Number, default: 5 }
})

const emit = defineEmits(['get-out-of-jail', 'set-approval', 'open-card', 'open-discard', 'over-limit', 'open-actions'])

// Over the hand limit: ask which cards to discard or give away first
function onEndTurn() {
  if (handOver.value > 0) emit('over-limit')
  else props.board.endTurn()
}

const SHUFFLE_DECKS = [
  { deck: 'scenario', label: 'Scenario' },
  { deck: 'collectable', label: 'Collectables' },
  { deck: 'assignment', label: 'Assignments' },
  { deck: 'all', label: 'All decks' }
]

function deckSize(deck) {
  const d = props.state?.decks?.[deck]
  return d ? `${d.draw} in the deck, ${d.discard} discarded` : 'Every deck, including job opportunities, promotions and hospital items'
}

const turnTarget = ref(null)
async function confirmSetTurn() {
  const p = props.playersById[turnTarget.value]
  if (!p) return
  if (await askConfirm(`Make it ${p.username}'s turn now? Their turn starts afresh (collect income, roll...), and any scenario card being played is stopped.`)) {
    props.board.setTurn(p.user_id)
    turnTarget.value = null
  }
}

async function confirmRedraw() {
  if (await askConfirm('Discard this turn\'s scenario card and draw another? What it has already done is not undone.')) {
    props.board.redrawScenario()
  }
}

async function confirmShuffle(d) {
  const what = d.deck === 'all' ? 'every deck' : `the ${d.label.toLowerCase()} deck`
  const extra = d.deck === 'collectable' || d.deck === 'all' ? ' This empties the Black Market.' : ''
  if (await askConfirm(`Shuffle ${what}, with its discard pile put back in?${extra}`)) {
    props.board.shuffleDeck(d.deck)
  }
}

const myPending = computed(() => {
  const p = props.state?.pending
  return p && p.user_id === props.myUserId ? p : null
})
const handOver = computed(() => Math.max(0, props.handSize - props.handLimit))
// A scenario card is being played out: finish it first
const eventInPlay = computed(() => Boolean(props.state?.event && !props.state.event.done))

const turn = computed(() => props.state?.turn || {})

// Rolling for the first turn
const initiative = computed(() => props.state?.initiative || { round: 1, contenders: [], rolls: {}, first_rolls: {} })
const initiativeRows = computed(() => {
  const init = initiative.value
  return Object.values(props.playersById).map(p => {
    const inRound = (init.contenders || []).includes(p.user_id)
    const key = String(p.user_id)
    const roll = inRound ? init.rolls?.[key] ?? null : init.first_rolls?.[key] ?? null
    return { ...p, inRound, roll }
  }).sort((a, b) => (b.inRound - a.inRound) || ((b.roll ?? -1) - (a.roll ?? -1)))
})
const initiativeInRound = computed(() => (initiative.value.contenders || []).includes(props.myUserId))
const canRollInitiative = computed(() =>
  initiativeInRound.value && !(String(props.myUserId) in (initiative.value.rolls || {}))
)
const initiativeWaiting = computed(() =>
  initiativeRows.value.filter(r => r.inRound && r.roll === null).map(r => r.username)
)
const me = computed(() => props.playersById[props.myUserId] || null)
const currentPlayer = computed(() => props.playersById[turn.value.user_id] || null)
const isMyTurn = computed(() => Boolean(props.state?.started) && turn.value.user_id === props.myUserId)

function positionOf(uid) {
  const pos = props.state?.positions?.[String(uid)]
  return pos === undefined ? null : pos
}

const myTile = computed(() => {
  const pos = positionOf(props.myUserId)
  return pos === null || pos < 0 ? null : props.state?.tiles?.[pos] || null
})
const currentTile = computed(() => {
  const pos = positionOf(turn.value.user_id)
  return pos === null || pos < 0 ? null : props.state?.tiles?.[pos] || null
})

const tone = computed(() => tileTheme(myTile.value?.kind).tone)
const description = computed(() => tileDescription(myTile.value, { doctorInPlay: props.doctorInPlay }))

// On a tile this turn: by rolling, or moved there by a card (Advance, Shortcut)
const onTile = computed(() => Boolean(turn.value.rolled || turn.value.landed))

// What the tile dealt into your hand ("1 Collectable added to your hand")
const dealtText = computed(() => dealtSummary(turn.value))

// Step rows: done, the one to do now, or still to come
function stepState(n) {
  const done = [Boolean(turn.value.paid), Boolean(turn.value.rolled), false]
  if (n === 3 && onTile.value && !turn.value.rolled) return 'is-current'
  if (done[n - 1]) return 'is-done'
  return done.findIndex(d => !d) === n - 1 ? 'is-current' : 'is-upcoming'
}

// The tile's actions are in the pop-up over the board (see ActionPopup)
const hasActions = computed(() => ACTION_TILE_KINDS.includes(myTile.value?.kind) || Boolean(myPending.value))

const lastMoveValue = computed(() => {
  const roll = props.state?.last_roll
  return roll && roll.user_id === props.myUserId && roll.kind === 'move' ? roll.values?.[0] : null
})

// How many turns until mine, for the waiting message
const myPosition = computed(() => {
  const order = props.state?.turn_order || []
  const i = order.indexOf(props.myUserId)
  return i === -1 ? null : i
})
const turnsUntilMine = computed(() => {
  const order = props.state?.turn_order || []
  const current = props.state?.turn_index ?? 0
  if (myPosition.value === null || !order.length) return ''
  const n = (myPosition.value - current + order.length) % order.length
  return n === 1 ? 'next' : `in ${n} turns`
})

const reaperSummoned = computed(() => {
  const t = Date.parse(props.state?.reaper?.arrives_at || '')
  return !Number.isNaN(t) && t <= Date.now() + props.serverOffsetMs
})

function formatSigned(total) {
  const sign = total >= 0 ? '+' : '−'
  const abs = Math.abs(total)
  const h = Math.floor(abs / 60)
  const m = abs % 60
  if (h && !m) return `${sign}${h}h`
  return `${sign}${h ? `${h}h ` : ''}${m}m`
}

async function confirmJail() {
  if (await askConfirm('Go to Jail? Your heat resets to zero, you lose your job and drop one title rank, and your turn ends.')) {
    props.board.goToJail()
  }
}

async function confirmRestart() {
  if (await askConfirm('Restart the game? Everyone rolls for the first turn again and every pawn goes back to Start. Clocks are not touched.')) {
    props.board.start(true)
  }
}

async function confirmReset() {
  if (await askConfirm('Reset the board to the lobby? Pawns, turn order, the Reaper and the log are cleared. Clocks are not touched.')) {
    props.board.reset()
  }
}
</script>

<style scoped>
.turn {
  padding: 14px 16px;
  border-radius: 12px;
  background: linear-gradient(180deg, #1A1F2E, #121726);
  border: 1px solid rgba(148, 163, 184, 0.16);
  color: #E2E8F0;
  font-size: 0.9rem;
  text-align: left;
}

.turn.is-mine {
  border-color: rgba(234, 179, 8, 0.6);
  box-shadow: 0 0 0 1px rgba(234, 179, 8, 0.25), 0 0 26px rgba(234, 179, 8, 0.12);
}

.turn__head { margin-bottom: 10px; }

.turn__eyebrow {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 0.8rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #22D3EE;
}

.turn__title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.55rem;
  font-weight: 800;
  color: #F8FAFC;
}

.turn.is-mine .turn__title { color: #FDE68A; }

.turn__dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.15);
}

.turn__text {
  margin: 0 0 10px;
  line-height: 1.45;
  color: #CBD5E1;
}

.turn__hint {
  margin: 6px 0 0;
  font-size: 0.8rem;
  color: #64748B;
}

.turn__hint--warn { color: #FDBA74; }

/* Roll for the first turn */
.init {
  margin: 8px 0 10px;
  padding: 0;
  list-style: none;
  text-align: left;
}

.init__row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 2px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
}

.init__row.is-out { opacity: 0.45; }
.init__row.is-me .init__name { color: #A5F3FC; }

.init__dot { width: 10px; height: 10px; border-radius: 50%; }

.init__name { flex: 1; min-width: 0; font-weight: 600; }

.init__roll {
  min-width: 28px;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.3rem;
  font-weight: 800;
  text-align: right;
  color: #FDE68A;
}

.init__roll.is-waiting { font-size: 0.85rem; font-weight: 400; color: #64748B; }

.turn__init-all { width: 100%; margin-top: 8px; }

.turn__admin-label {
  margin-top: 8px;
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #64748B;
}

.turn__muted { color: #64748B; padding: 6px 0; }

/* Steps ----------------------------------------------------------------- */
.turn__steps {
  list-style: none;
  margin: 0 0 10px;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: left;
}

.turn__step {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.turn__step-mark {
  flex: 0 0 24px;
  height: 24px;
  margin-top: 4px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  border: 1px solid rgba(234, 179, 8, 0.6);
  color: #FDE68A;
  font-weight: 700;
  font-size: 0.8rem;
}

.turn__step.is-done .turn__step-mark {
  background: #16a34a;
  border-color: #16a34a;
  color: #fff;
}

.turn__step.is-locked .turn__step-mark { opacity: 0.4; }

.turn__step-body { flex: 1; min-width: 0; }

/* Buttons --------------------------------------------------------------- */
.turn__btn {
  padding: 7px 12px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: rgba(148, 163, 184, 0.08);
  color: #E2E8F0;
  font-weight: 600;
  font-size: 0.88rem;
  cursor: pointer;
  transition: transform 0.12s ease, background 0.15s ease, border-color 0.15s ease;
}

.turn__btn:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: #EAB308;
}

.turn__btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.turn__steps .turn__btn,
.turn__block .turn__btn { width: 100%; }

.turn__btn--primary {
  background: linear-gradient(180deg, #EAB308, #CA8A04);
  border-color: #EAB308;
  color: #1c1917;
  font-weight: 800;
}

.turn__btn--roll {
  font-size: 1.05rem;
  padding: 10px 12px;
  letter-spacing: 0.02em;
}

.turn__btn--good { border-color: rgba(74, 222, 128, 0.55); color: #86EFAC; background: rgba(74, 222, 128, 0.08); }
.turn__btn--bad { border-color: rgba(248, 113, 113, 0.55); color: #FCA5A5; background: rgba(248, 113, 113, 0.08); }
.turn__btn--danger { border-color: #EF4444; background: rgba(239, 68, 68, 0.18); color: #FECACA; }
.turn__btn--virus { border-color: rgba(163, 230, 53, 0.6); background: rgba(163, 230, 53, 0.12); color: #D9F99D; }

.turn__btn--end {
  width: 100%;
  margin-top: 2px;
  padding: 10px 12px;
  border-radius: 10px;
  border-color: #22D3EE;
  background: linear-gradient(180deg, #0E7490, #155E75);
  color: #ECFEFF;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.1rem;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.turn__btn--end:hover:not(:disabled) { border-color: #67E8F9; background: linear-gradient(180deg, #0891B2, #0E7490); }

.turn__btn--end:disabled {
  opacity: 1;
  border-color: rgba(148, 163, 184, 0.2);
  background: rgba(148, 163, 184, 0.06);
  color: #64748B;
}

/* Job abilities */
.abilities {
  margin: 0 0 10px;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(129, 140, 248, 0.35);
}

.abilities__label {
  margin-bottom: 4px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #A5B4FC;
}

.ability { display: flex; align-items: center; gap: 10px; padding: 4px 0; }
.ability + .ability { border-top: 1px solid rgba(129, 140, 248, 0.2); }
.ability__text { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.ability__name { font-family: 'Barlow Condensed', sans-serif; font-size: 1.05rem; font-weight: 700; color: #E0E7FF; }
.ability__name small { font-size: 0.75rem; color: #A5B4FC; }
.ability__sub { font-size: 0.75rem; color: #94A3B8; }

.ability__use {
  padding: 5px 16px;
  border-radius: 8px;
  border: 1px solid #818CF8;
  background: linear-gradient(180deg, #6366F1, #4338CA);
  color: #EEF2FF;
  font-weight: 800;
  cursor: pointer;
}

.ability__use:disabled { border-color: rgba(148, 163, 184, 0.25); background: rgba(148, 163, 184, 0.08); color: #94A3B8; cursor: not-allowed; }

@media (max-height: 980px) {
  .turn { padding: 10px 14px; }
  .turn__head { margin-bottom: 6px; }
  .turn__title { font-size: 1.3rem; }
  .steps { gap: 5px; margin-bottom: 8px; }
  .step { padding: 6px 10px; }
  .step__title { font-size: 1rem; }
  .turn__btn--end { padding: 8px 12px; }
  .turn__admin { margin-top: 8px; padding-top: 6px; }
}

/* Steps: one row each -------------------------------------------------------- */
.steps {
  list-style: none;
  margin: 2px 0 12px;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  text-align: left;
}

.step {
  --tone: #94A3B8;
  display: grid;
  grid-template-columns: 26px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.55);
  border: 1px solid rgba(148, 163, 184, 0.12);
  transition: border-color 0.2s ease, background 0.2s ease;
}

.step.is-current {
  border-color: rgba(234, 179, 8, 0.6);
  background: linear-gradient(90deg, rgba(234, 179, 8, 0.12), rgba(15, 23, 42, 0.55) 70%);
}

.step.is-upcoming { opacity: 0.6; }

.step__mark {
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  border: 1.5px solid rgba(148, 163, 184, 0.4);
  color: #94A3B8;
  font-size: 0.8rem;
  font-weight: 800;
}

.step.is-current .step__mark { border-color: #EAB308; color: #FDE68A; }
.step.is-done .step__mark { background: #16a34a; border-color: #16a34a; color: #fff; }

.step__text { min-width: 0; display: flex; flex-direction: column; gap: 1px; }

.step__title {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.08rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  line-height: 1.15;
  color: #F1F5F9;
}

.step--tile .step__title { color: color-mix(in srgb, var(--tone) 65%, #fff); text-transform: uppercase; letter-spacing: 0.04em; }

.step__sub { font-size: 0.78rem; line-height: 1.35; color: #94A3B8; }
.step__sub.is-good { color: #86EFAC; }
.step__sub.is-bad { color: #FCA5A5; }
.step__sub--dealt { color: #5EEAD4; font-weight: 600; }

.step__action {
  padding: 6px 14px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.4);
  background: rgba(148, 163, 184, 0.08);
  color: #E2E8F0;
  font-size: 0.85rem;
  font-weight: 700;
  white-space: nowrap;
  cursor: pointer;
  transition: transform 0.12s ease, border-color 0.15s ease, background 0.15s ease;
}

.step__action:hover { transform: translateY(-1px); border-color: #EAB308; }
.step__action--income { border-color: rgba(74, 222, 128, 0.55); background: rgba(74, 222, 128, 0.12); color: #BBF7D0; }
.step__action--roll { border-color: #EAB308; background: linear-gradient(180deg, #EAB308, #CA8A04); color: #1c1917; }
.step__action--roll:hover { border-color: #FDE68A; }
.step__action.is-urgent { border-color: #A78BFA; background: rgba(167, 139, 250, 0.16); color: #DDD6FE; }

.step__pip {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border-radius: 7px;
  background: #0B0F19;
  border: 1px solid rgba(234, 179, 8, 0.5);
  color: #FDE68A;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.1rem;
  font-weight: 800;
}

.step--collectables { --tone: #2DD4BF; }
.step--assignment { --tone: #FB923C; }
.step--scenario { --tone: #A78BFA; }
.step--virus { --tone: #A3E635; }
.step--jump,
.step--job { --tone: #EC4899; }
.step--senate { --tone: #3B82F6; }
.step--hospital { --tone: #EAB308; }
.step--start { --tone: #34D399; }
.step--market { --tone: #EAB308; }

.turn__btn--chip { padding: 4px 10px; font-size: 0.8rem; }
.turn__btn--chip.is-active { border-color: #EAB308; background: rgba(234, 179, 8, 0.2); color: #FDE68A; }

.turn__btn--small { padding: 5px 9px; font-size: 0.8rem; }

.turn__select {
  flex: 1;
  min-width: 0;
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: #0B0F19;
  color: #E2E8F0;
}

/* Step 3: the tile you're on ------------------------------------------- */
.turn__tile {
  --tone: #94A3B8;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px 6px 12px;
  border-radius: 9px;
  background: rgba(11, 15, 25, 0.6);
  border: 1px solid color-mix(in srgb, var(--tone) 50%, transparent);
  border-left-width: 4px;
}

.turn__tile--collectables { --tone: #2DD4BF; }
.turn__tile--assignment { --tone: #FB923C; }
.turn__tile--scenario { --tone: #A78BFA; }
.turn__tile--virus { --tone: #A3E635; }
.turn__tile--jump,
.turn__tile--job { --tone: #EC4899; }
.turn__tile--senate { --tone: #3B82F6; }
.turn__tile--hospital { --tone: #EAB308; }
.turn__tile--start { --tone: #34D399; }
.turn__tile--market { --tone: #EAB308; }

.turn__tile-name {
  flex: 1;
  min-width: 0;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.1rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: color-mix(in srgb, var(--tone) 70%, #fff);
}

.turn__steps .turn__tile-open { width: auto; flex: 0 0 auto; }
.turn__tile-open.is-urgent { border-color: #A78BFA; color: #DDD6FE; background: rgba(167, 139, 250, 0.16); }

.turn__tile-text {
  margin: 6px 0 0;
  font-size: 0.8rem;
  line-height: 1.4;
  color: #94A3B8;
}

.turn__block {
  margin-bottom: 10px;
  padding: 10px 12px;
  border-radius: 10px;
}

.turn__block--reaper { background: rgba(167, 139, 250, 0.1); border: 1px solid rgba(167, 139, 250, 0.4); }
.turn__block--jail { background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.4); }

.turn__alarm {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.45);
  color: #FECACA;
  font-size: 0.85rem;
}

/* Admin ----------------------------------------------------------------- */
.turn__admin {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px dashed rgba(148, 163, 184, 0.2);
}

.turn__admin summary {
  cursor: pointer;
  color: #22D3EE;
  font-size: 0.8rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.turn__admin-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}
</style>
