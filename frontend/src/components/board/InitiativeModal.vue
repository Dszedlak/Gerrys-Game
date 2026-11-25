<template>
  <!-- Rolling for the first turn: one player at a time, in a random order.
       A tie for the highest roll becomes a roll battle. Everyone sees it. -->
  <transition name="init">
    <div v-if="visible" class="init-modal" role="dialog" aria-label="Roll for the first turn">
      <section class="init-modal__panel">
        <!-- The winner -->
        <template v-if="showingResult">
          <div class="init-modal__eyebrow">Let the game begin</div>
          <h2 class="init-modal__title init-modal__title--win">
            <span class="init-modal__dot" :style="{ background: winner?.color }" />
            {{ winner?.user_id === myUserId ? 'You start!' : `${winner?.username || 'Someone'} starts!` }}
          </h2>
          <p class="init-modal__sub">Highest roll: {{ init?.winning_roll }}</p>
          <ol class="init-modal__order">
            <li v-for="(p, i) in turnOrder" :key="p.user_id" :style="{ '--pawn': p.color }">
              <span class="init-modal__pos">{{ i + 1 }}</span><span class="init-modal__dot" />{{ p.username }}
            </li>
          </ol>
          <button type="button" class="init-modal__btn" @click="dismiss">Let's go</button>
        </template>

        <!-- Rolling -->
        <template v-else>
          <div class="init-modal__eyebrow">{{ battle ? `Roll battle ${init.round - 1}` : 'Before the game' }}</div>
          <h2 class="init-modal__title">{{ battle ? '⚔️ Roll battle!' : 'Roll for the first turn' }}</h2>
          <p class="init-modal__sub">
            <template v-if="battle">{{ battleNames }} tied on {{ battleTop }}: highest roll wins.</template>
            <template v-else>Everyone rolls once, in a random order. The highest roll starts.</template>
          </p>

          <div class="init-modal__die">
            <!-- Room around the die: it's 3D, and tumbles and bounces beyond its box -->
            <div class="init-modal__die-stage">
              <BoardDie
                :key="dieKey"
                :value="lastRoll?.values?.[0] || 1"
                :animate="animateDie"
                variant="black"
                size="92px"
              />
            </div>
            <div class="init-modal__die-caption">
              <template v-if="lastRoll && rollSettled">{{ nameOf(lastRoll.user_id) }} rolled {{ lastRoll.values[0] }}</template>
              <template v-else-if="lastRoll">{{ nameOf(lastRoll.user_id) }} rolls…</template>
            </div>
          </div>

          <ul class="init-modal__rows">
            <li
              v-for="row in rows"
              :key="row.user_id"
              class="init-modal__row"
              :class="{ 'is-current': row.current, 'is-out': !row.inRound, 'is-top': row.top }"
              :style="{ '--pawn': row.color }"
            >
              <span class="init-modal__dot" />
              <span class="init-modal__name">{{ row.username }}<small v-if="row.user_id === myUserId"> (you)</small></span>
              <span v-if="row.first !== null && battle && row.inRound" class="init-modal__first" title="First roll">{{ row.first }}</span>
              <span class="init-modal__roll">
                <template v-if="row.roll !== null">{{ row.roll }}</template>
                <template v-else-if="row.current">rolling…</template>
                <template v-else-if="row.inRound">waiting</template>
              </span>
            </li>
          </ul>

          <div class="init-modal__turn">
            <button
              v-if="currentId === myUserId"
              type="button"
              class="init-modal__btn init-modal__btn--roll"
              :disabled="rolling"
              @click="roll"
            >🎲 Your turn: roll!</button>
            <p v-else-if="current" class="init-modal__waiting">
              <span class="init-modal__dot" :style="{ background: current.color }" />
              {{ current.username }}'s turn to roll
            </p>
            <button
              v-if="isAdmin && current && currentId !== myUserId"
              type="button"
              class="init-modal__admin"
              @click="board.initiativeRollCurrent()"
            >Roll for {{ current.username }}</button>
          </div>
        </template>
      </section>
    </div>
  </transition>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import BoardDie from '@/components/board/BoardDie.vue'
import { DIE_SETTLE_MS } from '@/components/board/boardLayout'

const props = defineProps({
  state: { type: Object, default: null },
  phase: { type: String, default: 'loading' },
  playersById: { type: Object, default: () => ({}) },
  myUserId: { type: [Number, String], default: null },
  isAdmin: { type: Boolean, default: false },
  board: { type: Object, required: true }
})

const RESULT_MS = 6000

const init = computed(() => props.state?.initiative || null)
const battle = computed(() => (init.value?.round || 1) > 1)
const nameOf = (uid) => props.playersById[uid]?.username || 'Someone'

// --- The die: tumble for rolls made while we're watching ------------------
const lastRoll = computed(() => (props.state?.last_roll?.kind === 'initiative' ? props.state.last_roll : null))
let seenRollId = null
const animateDie = ref(false)
const rollSettled = ref(true)
const dieKey = computed(() => lastRoll.value?.id ?? 'none')
let settleTimer = null
const rolling = ref(false)

// A roll made in the last couple of seconds (by the server's clock, which the
// payload carries as server_now) is fresh, however this screen came to see it.
const FRESH_MS = 2500
function isFresh(roll) {
  const at = Date.parse(roll?.at || '')
  const now = Date.parse(props.state?.server_now || '')
  return !Number.isNaN(at) && !Number.isNaN(now) && now - at < FRESH_MS
}

watch(() => lastRoll.value?.id, (id) => {
  rolling.value = false
  const first = seenRollId === null
  if (first) seenRollId = id ?? 0
  if (id == null || (!first && id === seenRollId)) return
  // Seen for the first time: only animate it if it's just been rolled
  // (opening the pop-up mid-way shouldn't replay an old roll)
  if (first && !isFresh(lastRoll.value)) return
  seenRollId = id
  animateDie.value = true
  rollSettled.value = false
  clearTimeout(settleTimer)
  settleTimer = setTimeout(() => { rollSettled.value = true }, DIE_SETTLE_MS)
}, { immediate: true })

function roll() {
  rolling.value = true
  props.board.initiativeRoll()
  setTimeout(() => { rolling.value = false }, 3000)
}

// --- Who's rolling --------------------------------------------------------
const currentId = computed(() => {
  const i = init.value
  if (!i || i.done) return null
  return (i.order || [])[i.current ?? 0] ?? null
})
const current = computed(() => (currentId.value == null ? null : props.playersById[currentId.value] || null))

const roundRolls = computed(() => init.value?.rolls || {})
const battleTop = computed(() => {
  const last = init.value?.history?.[init.value.history.length - 1]
  if (!last) return null
  return Math.max(...Object.values(last.rolls))
})
const battleNames = computed(() => (init.value?.order || []).map(nameOf).join(' and '))

const rows = computed(() => {
  const i = init.value
  if (!i) return []
  const firstOrder = i.history?.[0]?.order || i.order || []
  const inRound = new Set(i.order || [])
  const ids = [...(i.order || []), ...firstOrder.filter(u => !inRound.has(u))]
  const vals = Object.values(roundRolls.value)
  const top = vals.length ? Math.max(...vals) : null
  return ids.map(uid => {
    const p = props.playersById[uid] || { user_id: uid, username: nameOf(uid) }
    const key = String(uid)
    const roll = inRound.has(uid) ? (roundRolls.value[key] ?? null) : (i.first_rolls?.[key] ?? null)
    return {
      ...p,
      inRound: inRound.has(uid),
      current: uid === currentId.value,
      roll,
      first: i.first_rolls?.[key] ?? null,
      top: inRound.has(uid) && roll !== null && roll === top
    }
  })
})

// --- Showing the result once someone wins -----------------------------------
const showingResult = ref(false)
// The winning roll is still tumbling: keep the pop-up open until it lands
const pendingResult = ref(false)
let resultTimer = null
const winner = computed(() => props.playersById[init.value?.winner] || null)
const turnOrder = computed(() => (props.state?.turn_order || []).map(u => props.playersById[u]).filter(Boolean))

watch(() => props.phase, (now, before) => {
  // Only announce the winner to people who were watching the roll
  if (before === 'initiative' && (now === 'playing' || now === 'jobs') && init.value?.done) {
    clearTimeout(resultTimer)
    pendingResult.value = true
    resultTimer = setTimeout(() => {
      pendingResult.value = false
      showingResult.value = true
      resultTimer = setTimeout(() => { showingResult.value = false }, RESULT_MS)
    }, DIE_SETTLE_MS + 400)
  }
})

const visible = computed(() => props.phase === 'initiative' || pendingResult.value || showingResult.value)

function dismiss() {
  clearTimeout(resultTimer)
  pendingResult.value = false
  showingResult.value = false
}

onBeforeUnmount(() => {
  clearTimeout(settleTimer)
  clearTimeout(resultTimer)
})
</script>

<style scoped>
.init-modal {
  position: fixed;
  inset: 0;
  z-index: 1040;
  display: grid;
  place-items: center;
  padding: 24px;
  background: radial-gradient(circle at 50% 40%, rgba(11, 15, 25, 0.7), rgba(11, 15, 25, 0.92));
  backdrop-filter: blur(4px);
}

.init-modal__panel {
  width: min(520px, 100%);
  padding: 22px 26px 24px;
  border-radius: 16px;
  background: linear-gradient(180deg, #1A1F2E, #121726);
  border: 1px solid rgba(234, 179, 8, 0.45);
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.6);
  font-family: 'Barlow Condensed', 'Segoe UI', sans-serif;
  color: #E2E8F0;
  text-align: center;
}

.init-modal__eyebrow {
  font-size: 0.9rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #22D3EE;
}

.init-modal__title {
  margin: 2px 0 0;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 2.2rem;
  font-weight: 800;
  color: #FDE68A;
}

.init-modal__title--win { font-size: 2.6rem; animation: win-pop 0.5s cubic-bezier(0.3, 1.6, 0.5, 1) both; }

@keyframes win-pop {
  from { transform: scale(0.6); opacity: 0; }
  to   { transform: none; opacity: 1; }
}

.init-modal__sub {
  margin: 4px 0 0;
  font-family: 'Segoe UI', system-ui, sans-serif;
  font-size: 0.9rem;
  color: #94A3B8;
}

.init-modal__die {
  display: grid;
  justify-items: center;
  gap: 4px;
  margin: 4px 0 14px;
}

.init-modal__die-stage {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  width: 160px;
  height: 178px;
  padding-bottom: 22px;
}

.init-modal__die-caption { position: relative; z-index: 1; min-height: 1.4em; font-size: 1.25rem; font-weight: 700; color: #FDE68A; }

.init-modal__rows {
  margin: 0;
  padding: 0;
  list-style: none;
  text-align: left;
}

.init-modal__row {
  --pawn: #94A3B8;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  border-radius: 8px;
  font-size: 1.15rem;
  transition: background 0.2s ease;
}

.init-modal__row + .init-modal__row { margin-top: 2px; }
.init-modal__row.is-current { background: rgba(234, 179, 8, 0.15); box-shadow: inset 0 0 0 1px rgba(234, 179, 8, 0.5); }
.init-modal__row.is-out { opacity: 0.45; }
.init-modal__row.is-top .init-modal__roll { color: #86EFAC; }

.init-modal__dot {
  flex: 0 0 12px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--pawn);
}

.init-modal__name { flex: 1; font-weight: 700; }
.init-modal__name small { color: #64748B; font-weight: 400; }

.init-modal__first {
  padding: 0 6px;
  border-radius: 4px;
  background: rgba(148, 163, 184, 0.15);
  color: #94A3B8;
  font-size: 0.85rem;
}

.init-modal__roll {
  min-width: 70px;
  text-align: right;
  font-size: 1.5rem;
  font-weight: 800;
  color: #FDE68A;
}

.init-modal__row:not(.is-out) .init-modal__roll:empty::after { content: ''; }
.init-modal__row .init-modal__roll { font-variant-numeric: tabular-nums; }
.init-modal__row.is-current .init-modal__roll,
.init-modal__row .init-modal__roll:not(:empty) { line-height: 1; }

.init-modal__turn {
  display: grid;
  justify-items: center;
  gap: 8px;
  margin-top: 18px;
}

.init-modal__waiting {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 1.3rem;
  font-weight: 700;
  color: #F1F5F9;
}

.init-modal__btn {
  padding: 10px 28px;
  border-radius: 12px;
  border: 1px solid #EAB308;
  background: linear-gradient(180deg, #EAB308, #CA8A04);
  color: #1c1917;
  font-family: inherit;
  font-size: 1.35rem;
  font-weight: 800;
  cursor: pointer;
}

.init-modal__btn--roll { animation: roll-pulse 1.4s ease-in-out infinite; }
.init-modal__btn:disabled { opacity: 0.5; cursor: wait; animation: none; }

@keyframes roll-pulse {
  50% { box-shadow: 0 0 0 8px rgba(234, 179, 8, 0.2); }
}

.init-modal__admin {
  padding: 3px 12px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: transparent;
  color: #94A3B8;
  font-family: inherit;
  font-size: 0.9rem;
  cursor: pointer;
}

.init-modal__order {
  margin: 16px auto 18px;
  padding: 0;
  max-width: 300px;
  list-style: none;
  text-align: left;
}

.init-modal__order li {
  --pawn: #94A3B8;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 0;
  font-size: 1.15rem;
  font-weight: 700;
}

.init-modal__pos {
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  border: 1px solid rgba(234, 179, 8, 0.6);
  color: #FDE68A;
  font-size: 0.85rem;
}

.init-enter-active,
.init-leave-active { transition: opacity 0.25s ease; }
.init-enter-from,
.init-leave-to { opacity: 0; }
</style>
