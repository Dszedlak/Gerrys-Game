<template>
  <!-- A scenario card in play, for the whole table: everyone sees it, each player
       rolls / chooses / votes when it's their go. Minimise it to see the board. -->
  <transition name="sev">
    <div v-if="ev && shown && !minimised && !moving" class="sev" role="dialog" :aria-label="ev.title">
      <section class="sev__panel">
        <header class="sev__head">
          <span class="sev__dot" :style="{ background: drawer?.color || '#A78BFA' }" />
          <span class="sev__eyebrow">
            <template v-if="ev.played">
              {{ ev.deck === 'ability' ? '⚡' : '🎴' }} {{ deckLabel }} · {{ ev.drawer === myUserId ? (ev.deck === 'ability' ? 'you used it' : 'you played it') : `${ev.deck === 'ability' ? 'used' : 'played'} by ${drawer?.username || 'someone'}` }}
            </template>
            <template v-else>
              🃏 Scenario · {{ ev.drawer === myUserId ? 'you drew it' : `drawn by ${drawer?.username || 'someone'}` }}
            </template>
          </span>
          <span v-if="ev.done" class="sev__state sev__state--done">✓ Done</span>
          <span v-else class="sev__state">In play</span>
          <button type="button" class="sev__icon-btn" title="Minimise (see the board)" aria-label="Minimise" @click="minimised = true">–</button>
        </header>

        <div class="sev__body">
          <div class="sev__card">
            <CardFace :card="ev.card" size="lg" />
          </div>

          <div class="sev__side">
            <!-- The last die rolled for this card -->
            <div v-if="ev.roll" class="sev__roll" :class="rollClass" :key="ev.roll.id">
              <div class="sev__dice">
                <BoardDie
                  v-for="(v, i) in ev.roll.values"
                  :key="`${ev.roll.id}-${i}`"
                  :value="v"
                  :animate="animateRoll"
                  variant="black"
                  size="46px"
                />
              </div>
              <div class="sev__roll-text">
                <strong>{{ nameOf(ev.roll.user_id) }}</strong>
                <span>{{ ev.roll.label }}</span>
                <span class="sev__roll-total">
                  {{ ev.roll.total }}<template v-if="ev.roll.bonus"> (incl. +{{ ev.roll.bonus }})</template>
                  <template v-if="ev.roll.ok !== null"> · {{ ev.roll.ok ? 'success' : 'failed' }}</template>
                </span>
              </div>
            </div>

            <!-- What has happened so far -->
            <ol ref="linesEl" class="sev__lines">
              <li v-for="(l, i) in ev.lines" :key="i" :class="`is-${l.tone || 'plain'}`">{{ l.text }}</li>
              <li v-if="!ev.lines.length" class="is-muted">Waiting for the first move…</li>
            </ol>

            <!-- The question being asked -->
            <div v-if="p" class="sev__ask" :class="{ 'is-mine': mine }">
              <div class="sev__question">
                <template v-if="p.kind === 'roll'">
                  🎲 <strong>{{ mine ? 'Your roll' : `${nameOf(p.user_id)} to roll` }}</strong>: {{ p.label }}
                  <span v-if="p.hint" class="sev__hint">({{ p.hint }})</span>
                </template>
                <template v-else>{{ p.question }}</template>
              </div>

              <!-- Roll -->
              <template v-if="p.kind === 'roll'">
                <button v-if="mine" type="button" class="sev__btn sev__btn--roll" @click="answer(true)">🎲 Roll the die</button>
                <p v-else class="sev__wait">Waiting for {{ nameOf(p.user_id) }} to roll…</p>
                <button v-if="!mine && isAdmin" type="button" class="sev__btn sev__btn--small" @click="answer(true)">
                  Roll for {{ nameOf(p.user_id) }}
                </button>
              </template>

              <!-- Choice -->
              <template v-else-if="p.kind === 'choice'">
                <div v-if="canAnswer" class="sev__options">
                  <button
                    v-for="o in p.options"
                    :key="o.key"
                    type="button"
                    class="sev__btn"
                    :class="{ 'sev__btn--discard': p.unusable }"
                    @click="answer(o.key)"
                  >{{ o.label }}</button>
                </div>
                <p v-if="!mine" class="sev__wait">
                  {{ nameOf(p.user_id) }} {{ p.unusable ? 'is to discard it…' : 'is deciding…' }}<span v-if="isAdmin"> (admin: you can answer for them)</span>
                </p>
              </template>

              <!-- Pick players / oppressions -->
              <template v-else-if="p.kind === 'pick'">
                <template v-if="canAnswer">
                  <div class="sev__options">
                    <button
                      v-for="o in p.options"
                      :key="o.key"
                      type="button"
                      class="sev__btn sev__btn--toggle"
                      :class="{ 'is-on': picked.includes(o.key) }"
                      @click="togglePick(o.key)"
                    >{{ picked.includes(o.key) ? '✓ ' : '' }}{{ o.label }}</button>
                  </div>
                  <button type="button" class="sev__btn sev__btn--go" :disabled="!pickValid" @click="answer([...picked])">
                    {{ picked.length ? `Confirm (${picked.length})` : (p.min === 0 ? 'Nobody / none' : 'Pick first') }}
                  </button>
                </template>
                <p v-if="!mine" class="sev__wait">{{ nameOf(p.user_id) }} is choosing…<span v-if="isAdmin"> (admin: you can answer for them)</span></p>
              </template>

              <!-- Choose cards from your hand -->
              <template v-else-if="p.kind === 'cards'">
                <template v-if="mine">
                  <div class="sev__options">
                    <button
                      v-for="c in myCandidates"
                      :key="c.uid"
                      type="button"
                      class="sev__btn sev__btn--toggle"
                      :class="{ 'is-on': picked.includes(c.uid) }"
                      @click="togglePick(c.uid, p.count)"
                    >{{ picked.includes(c.uid) ? '✓ ' : '' }}{{ c.title }}</button>
                  </div>
                  <button type="button" class="sev__btn sev__btn--go" :disabled="picked.length !== Math.min(p.count, p.candidates.length)" @click="answer([...picked])">
                    Confirm
                  </button>
                </template>
                <p v-else class="sev__wait">{{ nameOf(p.user_id) }} is choosing {{ p.count }} cards…</p>
                <button v-if="!mine && isAdmin" type="button" class="sev__btn sev__btn--small" @click="answer('random')">
                  Pick at random for {{ nameOf(p.user_id) }}
                </button>
              </template>

              <!-- Share out time -->
              <template v-else-if="p.kind === 'allocate'">
                <template v-if="canAnswer">
                  <div class="sev__alloc">
                    <div v-for="uid in p.recipients" :key="uid" class="sev__alloc-row">
                      <span>{{ p.labels?.[uid] || nameOf(uid) }}</span>
                      <span class="sev__stepper">
                        <button type="button" :disabled="!(alloc[uid] > 0)" @click="bump(uid, -p.step)">−</button>
                        <strong>{{ fmt(alloc[uid] || 0) }}</strong>
                        <button type="button" :disabled="allocLeft < p.step" @click="bump(uid, p.step)">+</button>
                      </span>
                    </div>
                  </div>
                  <button type="button" class="sev__btn sev__btn--go" :disabled="allocLeft !== 0" @click="answer({ ...alloc })">
                    {{ allocLeft ? `${fmt(allocLeft)} left to share` : 'Confirm' }}
                  </button>
                </template>
                <p v-if="!mine" class="sev__wait">{{ nameOf(p.user_id) }} is sharing it out…</p>
              </template>

              <!-- Choose a job: from the jobs card list -->
              <template v-else-if="p.kind === 'job'">
                <button v-if="canAnswer" type="button" class="sev__btn sev__btn--go" @click="$emit('pick-job', p)">
                  📋 Choose from the jobs list
                </button>
                <p v-if="!mine" class="sev__wait">{{ nameOf(p.user_id) }} is choosing a job…</p>
              </template>

              <!-- Move to a tile -->
              <template v-else-if="p.kind === 'tile'">
                <template v-if="canAnswer">
                  <select v-model="tile" class="sev__select" aria-label="Tile">
                    <option :value="null" disabled>Choose a tile…</option>
                    <option v-for="t in p.tiles" :key="t.key" :value="t.key">{{ t.label }}</option>
                  </select>
                  <button type="button" class="sev__btn sev__btn--go" :disabled="tile === null" @click="answer(tile)">Move there</button>
                </template>
                <p v-if="!mine" class="sev__wait">{{ nameOf(p.user_id) }} is choosing a tile…</p>
              </template>

              <!-- Buy at special prices -->
              <template v-else-if="p.kind === 'buy'">
                <template v-if="canAnswer">
                  <div class="sev__alloc">
                    <div v-for="it in p.items" :key="it.key" class="sev__alloc-row">
                      <span>{{ it.label }} <small>{{ fmt(it.minutes) }}</small></span>
                      <span class="sev__stepper">
                        <button type="button" :disabled="!(basket[it.key] > 0)" @click="basketBump(it.key, -1)">−</button>
                        <strong>{{ basket[it.key] || 0 }}</strong>
                        <button type="button" :disabled="basketCount >= p.max" @click="basketBump(it.key, 1)">+</button>
                      </span>
                    </div>
                  </div>
                  <button type="button" class="sev__btn sev__btn--go" @click="answer({ ...basket })">
                    {{ basketCount ? `Buy ${basketCount} · ${fmt(basketCost)}` : 'Buy nothing' }}
                  </button>
                </template>
                <p v-if="!mine" class="sev__wait">{{ nameOf(p.user_id) }} is shopping…</p>
              </template>

              <!-- Vote -->
              <template v-else-if="p.kind === 'vote'">
                <div v-if="canVote" class="sev__options">
                  <button
                    v-for="o in voteOptions"
                    :key="o.key"
                    type="button"
                    class="sev__btn"
                    @click="answer(o.key)"
                  >{{ o.label }}</button>
                </div>
                <p class="sev__wait">
                  <template v-if="p.voted?.includes(myUserId)">✓ Your vote is in. </template>
                  {{ p.voted?.length || 0 }} of {{ p.voters.length }} voted{{ p.anonymous ? ' (anonymous)' : '' }}.
                  <span v-if="waitingVoters.length">Waiting for {{ waitingVoters.join(', ') }}.</span>
                </p>
                <button v-if="isAdmin" type="button" class="sev__btn sev__btn--small" @click="answer('__close__')">Close the vote now</button>
              </template>
            </div>
          </div>
        </div>

        <footer class="sev__foot">
          <button v-if="!ev.done && canRedraw && !ev.played && !p?.unusable" type="button" class="sev__btn sev__btn--small sev__btn--redraw" @click="redraw">
            🔁 Discard &amp; draw another
          </button>
          <template v-if="!ev.done && isAdmin">
            <button v-if="p" type="button" class="sev__btn sev__btn--small" @click="board.eventSkip()">Skip this step</button>
            <button type="button" class="sev__btn sev__btn--small" @click="stopCard">Stop the card</button>
          </template>
          <span class="sev__spacer" />
          <button type="button" class="sev__btn sev__btn--small" @click="ev.done ? close() : (minimised = true)">
            {{ ev.done ? 'Close' : 'Minimise' }}
          </button>
        </footer>
      </section>
    </div>
  </transition>

  <!-- Minimised: a tab everyone can click to bring the card back -->
  <transition name="sev-tab">
    <button
      v-if="ev && shown && minimised && !moving"
      type="button"
      class="sev-tab"
      :class="{ 'is-mine': needsMe, 'is-done': ev.done }"
      @click="minimised = false"
    >
      🃏 <strong>{{ ev.title }}</strong>
      <span>· {{ tabStatus }}</span>
    </button>
  </transition>
</template>

<script setup>
import { askConfirm } from '@/composables/useConfirm'
import { ref, reactive, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import CardFace from '@/components/board/CardFace.vue'
import BoardDie from '@/components/board/BoardDie.vue'
import { moveDurationMs } from '@/components/board/boardLayout'

const props = defineProps({
  // state.event (see backend/app/websocket/board_events.py)
  event: { type: Object, default: null },
  lastRoll: { type: Object, default: null },
  // A pawn is still moving: wait until it lands
  moving: { type: Boolean, default: false },
  board: { type: Object, required: true },
  playersById: { type: Object, default: () => ({}) },
  myUserId: { type: [Number, String], default: null },
  isAdmin: { type: Boolean, default: false },
  // My hand, for "choose cards" questions
  hand: { type: Array, default: () => [] }
})

const emit = defineEmits(['visible', 'pick-job'])

const ev = computed(() => props.event)
const DECK_LABELS = { collectable: 'Collectable', job: 'Job Opportunity', promotion: 'Promotion', shortcut: 'Shortcut', hospital: 'Hospital item', ability: 'Job ability' }
const deckLabel = computed(() => DECK_LABELS[ev.value?.deck] || 'Card')

const p = computed(() => ev.value?.prompt || null)
const drawer = computed(() => props.playersById[ev.value?.drawer] || null)
const nameOf = (uid) => (uid === props.myUserId ? 'You' : props.playersById[uid]?.username || 'Someone')

const shown = ref(false)
const minimised = ref(false)
let seenId = null
let showTimer = null

watch(() => ev.value?.id, (id) => {
  clearTimeout(showTimer)
  if (id == null) {
    shown.value = false
    return
  }
  const first = seenId === null
  seenId = id
  minimised.value = false
  // Joining mid-game: only bring back a card that is still in play
  if (first && ev.value.done) {
    shown.value = false
    return
  }
  // Drawn by landing on the tile: wait for the pawn to finish moving
  const fromRoll = ev.value.after_roll != null && props.lastRoll?.id === ev.value.after_roll
  const delay = fromRoll && !first ? moveDurationMs(props.lastRoll) + 250 : 0
  shown.value = false
  showTimer = setTimeout(() => { shown.value = true }, delay)
}, { immediate: true })

// Once the card is done (every action taken, or it was discarded) the panel closes itself:
// soon after the last action, or after a read if it had no choices at all.
const AFTER_ACTION_MS = 2500
const READ_MS = 9000
let doneTimer = null
watch(() => [ev.value?.id, Boolean(ev.value?.done)], ([id, done], old) => {
  clearTimeout(doneTimer)
  if (!done) return
  const [oldId, wasDone] = old || []
  const justFinished = Boolean(old) && id === oldId && !wasDone
  doneTimer = setTimeout(() => { shown.value = false }, justFinished ? AFTER_ACTION_MS : READ_MS)
})

watch(() => Boolean(shown.value && ev.value && !minimised.value && !props.moving), (v) => emit('visible', v), { immediate: true })

// It's my go: bring the card back up
const needsMe = computed(() => {
  const q = p.value
  if (!q || ev.value?.done) return false
  if (q.kind === 'vote') return q.voters.includes(props.myUserId) && !q.voted?.includes(props.myUserId)
  return q.user_id === props.myUserId
})
watch(() => [p.value?.id, needsMe.value], () => {
  if (needsMe.value) {
    minimised.value = false
    if (!shown.value && ev.value) shown.value = true
  }
})

const mine = computed(() => Boolean(p.value) && p.value.user_id === props.myUserId)
const canAnswer = computed(() => mine.value || props.isAdmin)

const tabStatus = computed(() => {
  if (ev.value?.done) return 'done'
  const q = p.value
  if (!q) return 'in play'
  if (needsMe.value) return q.kind === 'roll' ? 'your roll!' : q.kind === 'vote' ? 'your vote!' : 'your move!'
  if (q.kind === 'vote') return `voting (${q.voted?.length || 0}/${q.voters.length})`
  return `waiting for ${nameOf(q.user_id)}`
})

// The die animates for a new roll only
// (the roll already there when this screen first saw the card isn't replayed)
const animateRoll = ref(false)
let seenRollId
watch(() => ev.value?.roll?.id, (id) => {
  if (seenRollId === undefined) {
    seenRollId = id ?? null
    animateRoll.value = false
    return
  }
  animateRoll.value = id != null && id !== seenRollId
  seenRollId = id ?? null
}, { immediate: true })
const rollClass = computed(() => {
  const r = ev.value?.roll
  return r?.ok === true ? 'is-good' : r?.ok === false ? 'is-bad' : ''
})

// Keep the newest line in view
const linesEl = ref(null)
watch(() => ev.value?.lines?.length, async () => {
  await nextTick()
  if (linesEl.value) linesEl.value.scrollTop = linesEl.value.scrollHeight
})

// --- answers ---------------------------------------------------------------
const picked = ref([])
const tile = ref(null)
const alloc = reactive({})
const basket = reactive({})
watch(() => p.value?.id, () => {
  picked.value = []
  tile.value = null
  Object.keys(alloc).forEach(k => delete alloc[k])
  Object.keys(basket).forEach(k => delete basket[k])
})

function answer(value) {
  if (!p.value) return
  props.board.eventAnswer(p.value.id, value)
}

function togglePick(key, limit) {
  const i = picked.value.indexOf(key)
  if (i !== -1) {
    picked.value.splice(i, 1)
    return
  }
  const max = limit ?? p.value?.max ?? 1
  if (max === 1) picked.value = [key]
  else if (picked.value.length < max) picked.value.push(key)
}

const pickValid = computed(() => {
  const q = p.value
  if (!q) return false
  return picked.value.length >= (q.min ?? 0) && picked.value.length <= (q.max ?? 1)
})

const myCandidates = computed(() => {
  const want = new Set(p.value?.candidates || [])
  return props.hand.filter(c => want.has(c.uid))
})

const allocLeft = computed(() => (p.value?.total || 0) - Object.values(alloc).reduce((a, b) => a + b, 0))
function bump(uid, delta) {
  alloc[uid] = Math.max(0, (alloc[uid] || 0) + delta)
}

const basketCount = computed(() => Object.values(basket).reduce((a, b) => a + b, 0))
const basketCost = computed(() => (p.value?.items || []).reduce((sum, it) => sum + (basket[it.key] || 0) * it.minutes, 0))
function basketBump(key, delta) {
  basket[key] = Math.max(0, (basket[key] || 0) + delta)
}

const canVote = computed(() => {
  const q = p.value
  return q?.kind === 'vote' && q.voters.includes(props.myUserId) && !q.voted?.includes(props.myUserId)
})
const voteOptions = computed(() => (p.value?.options || []).filter(o => !(p.value.exclude_self && o.key === String(props.myUserId))))
const waitingVoters = computed(() => {
  const q = p.value
  if (q?.kind !== 'vote') return []
  return q.voters.filter(v => !q.voted?.includes(v)).map(nameOf)
})

// --- footer ----------------------------------------------------------------
const canRedraw = computed(() => ev.value?.drawer === props.myUserId || props.isAdmin)

async function redraw() {
  if (await askConfirm(`Discard “${ev.value.title}” and draw another scenario card? What it has already done is not undone.`)) {
    props.board.redrawScenario()
  }
}

async function stopCard() {
  if (await askConfirm(`Stop “${ev.value.title}” here? Nothing more on it will happen.`)) props.board.eventSkip(true)
}

function close() {
  shown.value = false
}

function fmt(minutes) {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return h && m ? `${h}h ${m}m` : h ? `${h}h` : `${m}m`
}

/** Bring the card back (from the scenario deck menu, or the action pop-up). */
function open() {
  if (!ev.value) return false
  shown.value = true
  minimised.value = false
  return true
}

onBeforeUnmount(() => {
  clearTimeout(showTimer)
  clearTimeout(doneTimer)
})

defineExpose({ open })
</script>

<style scoped>
.sev {
  position: absolute;
  inset: 0;
  z-index: 42;
  display: grid;
  place-items: center;
  padding: 14px;
  background: radial-gradient(circle at 50% 45%, rgba(11, 15, 25, 0.5), rgba(11, 15, 25, 0.85));
  backdrop-filter: blur(2px);
}

.sev__panel {
  width: min(720px, 100%);
  max-height: 100%;
  display: flex;
  flex-direction: column;
  border-radius: 16px;
  background: linear-gradient(180deg, #1E1B2E, #131126);
  border: 1px solid rgba(139, 92, 246, 0.6);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6), 0 0 34px rgba(139, 92, 246, 0.16);
  color: #E2E8F0;
  overflow: hidden;
}

.sev__head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.25);
}

.sev__dot { width: 12px; height: 12px; border-radius: 50%; flex: 0 0 auto; }

.sev__eyebrow {
  flex: 1;
  min-width: 0;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 0.95rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #C4B5FD;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sev__state {
  padding: 2px 9px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
  background: rgba(234, 179, 8, 0.16);
  color: #FDE68A;
}

.sev__state--done { background: rgba(74, 222, 128, 0.16); color: #86EFAC; }

.sev__icon-btn {
  width: 30px;
  height: 26px;
  padding: 0;
  border-radius: 7px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: transparent;
  color: #CBD5E1;
  font-size: 1.2rem;
  font-weight: 700;
  line-height: 1;
  cursor: pointer;
}

.sev__body {
  display: grid;
  grid-template-columns: minmax(0, 240px) minmax(0, 1fr);
  gap: 14px;
  padding: 14px;
  min-height: 0;
  overflow-y: auto;
}

.sev__card { min-width: 0; }

/* The large card face is a fixed 340px wide elsewhere: here it fills its column */
.sev__card :deep(.card-face--lg) { width: 100%; max-width: 100%; }
.sev__card :deep(.card-face--lg .card-face__title) { font-size: 1.55rem; }
.sev__card :deep(.card-face--lg .card-face__text) { font-size: 0.92rem; }

.sev__side {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

.sev__roll {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.sev__roll.is-good { border-color: rgba(74, 222, 128, 0.55); }
.sev__roll.is-bad { border-color: rgba(248, 113, 113, 0.55); }

.sev__dice { display: flex; gap: 6px; }

.sev__roll-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
  font-size: 0.82rem;
  color: #94A3B8;
}

.sev__roll-text strong { color: #F8FAFC; font-size: 0.95rem; }

.sev__roll-total {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.15rem;
  font-weight: 800;
  color: #FDE68A;
}

.sev__roll.is-good .sev__roll-total { color: #86EFAC; }
.sev__roll.is-bad .sev__roll-total { color: #FCA5A5; }

.sev__lines {
  margin: 0;
  padding: 0;
  list-style: none;
  max-height: 170px;
  overflow-y: auto;
  font-size: 0.86rem;
  line-height: 1.4;
}

.sev__lines li {
  padding: 4px 8px;
  border-left: 3px solid rgba(148, 163, 184, 0.3);
  margin-bottom: 3px;
  background: rgba(148, 163, 184, 0.05);
  border-radius: 0 6px 6px 0;
}

.sev__lines li.is-good { border-left-color: #4ADE80; color: #BBF7D0; }
.sev__lines li.is-bad { border-left-color: #F87171; color: #FECACA; }
.sev__lines li.is-note { border-left-color: #EAB308; color: #FDE68A; }
.sev__lines li.is-muted { color: #64748B; border-left-color: transparent; }

.sev__ask {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.35);
}

.sev__ask.is-mine {
  background: rgba(234, 179, 8, 0.1);
  border-color: rgba(234, 179, 8, 0.7);
  box-shadow: 0 0 22px rgba(234, 179, 8, 0.15);
}

.sev__question { font-size: 0.95rem; color: #F1F5F9; }
.sev__hint { color: #A5B4FC; font-size: 0.82rem; }

.sev__wait { margin: 0; font-size: 0.85rem; color: #94A3B8; }

.sev__options { display: flex; flex-wrap: wrap; gap: 6px; }

.sev__btn {
  padding: 7px 12px;
  border-radius: 9px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: rgba(148, 163, 184, 0.08);
  color: #E2E8F0;
  font-weight: 700;
  font-size: 0.9rem;
  cursor: pointer;
}

.sev__btn:hover:not(:disabled) { border-color: #A78BFA; background: rgba(139, 92, 246, 0.16); }
.sev__btn:disabled { opacity: 0.45; cursor: not-allowed; }

.sev__btn--roll {
  padding: 12px;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.3rem;
  font-weight: 800;
  background: linear-gradient(180deg, #EAB308, #CA8A04);
  border-color: #EAB308;
  color: #1c1917;
  animation: sev-pulse 1.5s ease-in-out infinite;
}

.sev__btn--roll:hover:not(:disabled) { background: linear-gradient(180deg, #FACC15, #EAB308); border-color: #FDE68A; }

@keyframes sev-pulse { 50% { box-shadow: 0 0 22px rgba(234, 179, 8, 0.55); } }

.sev__btn--discard {
  border-color: rgba(239, 68, 68, 0.7);
  background: rgba(239, 68, 68, 0.16);
  color: #FECACA;
}

.sev__btn--discard:hover:not(:disabled) { border-color: #EF4444; background: rgba(239, 68, 68, 0.3); color: #fff; }

.sev__btn--go { border-color: rgba(74, 222, 128, 0.6); background: rgba(74, 222, 128, 0.12); color: #BBF7D0; }
.sev__btn--toggle.is-on { border-color: #A78BFA; background: rgba(139, 92, 246, 0.28); color: #EDE9FE; }
.sev__btn--small { padding: 5px 10px; font-size: 0.8rem; font-weight: 600; }
.sev__btn--redraw { border-color: rgba(167, 139, 250, 0.6); color: #DDD6FE; }

.sev__alloc { display: flex; flex-direction: column; gap: 4px; }

.sev__alloc-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 0.9rem;
}

.sev__alloc-row small { color: #94A3B8; }

.sev__stepper {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.sev__stepper button {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: transparent;
  color: #E2E8F0;
  font-weight: 800;
  cursor: pointer;
}

.sev__stepper button:disabled { opacity: 0.3; cursor: not-allowed; }
.sev__stepper strong { min-width: 50px; text-align: center; }

.sev__select {
  padding: 7px 9px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: #0B0F19;
  color: #E2E8F0;
}

.sev__foot {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  border-top: 1px solid rgba(139, 92, 246, 0.25);
}

.sev__spacer { flex: 1; }

/* Minimised */
.sev-tab {
  position: absolute;
  top: 10px;
  left: 50%;
  z-index: 42;
  display: flex;
  align-items: center;
  gap: 6px;
  max-width: calc(100% - 32px);
  padding: 7px 16px;
  border-radius: 999px;
  border: 1px solid rgba(167, 139, 250, 0.75);
  background: rgba(30, 27, 46, 0.95);
  color: #DDD6FE;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
  transform: translateX(-50%);
  cursor: pointer;
}

.sev-tab.is-mine { border-color: #EAB308; color: #FDE68A; animation: sev-pulse 1.4s ease-in-out infinite; }
.sev-tab.is-done { opacity: 0.85; }

.sev-enter-active, .sev-leave-active { transition: opacity 0.22s ease; }
.sev-enter-active .sev__panel { animation: sev-in 0.45s cubic-bezier(0.2, 0.9, 0.3, 1.15); }
.sev-enter-from, .sev-leave-to { opacity: 0; }

@keyframes sev-in { from { transform: scale(0.9) translateY(24px); opacity: 0; } }

.sev-tab-enter-active, .sev-tab-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.sev-tab-enter-from, .sev-tab-leave-to { opacity: 0; transform: translate(-50%, -10px); }

@media (max-width: 640px) {
  .sev__body { grid-template-columns: 1fr; }
  .sev__card { max-width: 220px; justify-self: center; }
}
</style>
