<template>
  <!-- A card drawn, played or completed, shown to the whole table at once.
       It waits for the pawn to finish moving when it came from a roll. -->
  <transition name="reveal">
    <div v-if="visible && reveal && !holdBack" class="reveal" role="dialog" :aria-label="headline" @click.self="close">
      <div class="reveal__panel" @mouseenter="hold = true" @mouseleave="hold = false">
        <div class="reveal__headline">
          <span class="reveal__dot" :style="{ background: actor?.color || '#94A3B8' }" />
          <span>{{ headline }}</span>
        </div>

        <div class="reveal__flip" :key="reveal.id">
          <div class="reveal__back" :style="{ '--tone': meta.color }">
            <span>{{ meta.icon }}</span>
          </div>
          <CardFace class="reveal__front" :card="reveal.card" size="lg" />
        </div>

        <ul v-if="reveal.lines?.length" class="reveal__lines">
          <li v-for="(line, i) in reveal.lines" :key="i" :class="lineClass(line)" :style="{ animationDelay: `${1.1 + i * 0.12}s` }">
            {{ line }}
          </li>
        </ul>
        <ul v-if="reveal.notes?.length" class="reveal__notes">
          <li v-for="(note, i) in reveal.notes" :key="i">✍️ Resolve by hand: {{ note }}</li>
        </ul>

        <!-- Waiting on a decision from whoever drew it -->
        <div v-if="pendingHere" class="reveal__decide">
          <template v-if="pendingHere.user_id === myUserId">
            <template v-if="pendingHere.kind === 'choose_target'">
              <div class="reveal__ask">Choose a player:</div>
              <div class="reveal__choices">
                <button
                  v-for="p in targetChoices"
                  :key="p.user_id"
                  type="button"
                  class="reveal__choice"
                  :style="{ '--pawn': p.color }"
                  @click="board.chooseCardTarget(p.user_id)"
                >
                  <span class="reveal__choice-dot" />{{ p.username }}
                </button>
              </div>
            </template>
            <template v-else-if="pendingHere.kind === 'replace'">
              <div class="reveal__ask">Replace which slip? Its target stays the same.</div>
              <div class="reveal__choices">
                <button
                  v-for="a in replaceChoices"
                  :key="a.id"
                  type="button"
                  class="reveal__choice"
                  @click="board.replaceAssignment(a.id)"
                >
                  “{{ a.card?.title }}” → {{ playersById[a.target]?.username || 'someone' }}
                </button>
                <button type="button" class="reveal__choice reveal__choice--muted" @click="board.replaceAssignment(null)">
                  Discard the new slip
                </button>
              </div>
            </template>
          </template>
          <div v-else class="reveal__waiting">
            Waiting for {{ actor?.username || 'the player' }} to decide…
          </div>
        </div>

        <div class="reveal__buttons">
          <button v-if="canRedraw" type="button" class="reveal__close reveal__close--redraw" @click="redraw">
            🔁 Discard &amp; draw another
          </button>
          <button type="button" class="reveal__close" @click="close">
            {{ pendingHere && pendingHere.user_id === myUserId ? 'Decide later' : 'Close' }}
          </button>
        </div>
        <div v-if="!pendingHere && !hold" :key="`t${reveal.id}-${visible}`" class="reveal__timer" />
      </div>
    </div>
  </transition>
</template>

<script setup>
import { askConfirm } from '@/composables/useConfirm'
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import CardFace from '@/components/board/CardFace.vue'
import { DECK_META, moveDurationMs } from '@/components/board/boardLayout'

const props = defineProps({
  // False until the first board state arrives, so an old card isn't replayed on join
  ready: { type: Boolean, default: true },
  // A pawn is still moving to its tile: wait
  holdBack: { type: Boolean, default: false },
  reveal: { type: Object, default: null },
  pending: { type: Object, default: null },
  lastRoll: { type: Object, default: null },
  assignments: { type: Array, default: () => [] },
  playersById: { type: Object, default: () => ({}) },
  myUserId: { type: [Number, String], default: null },
  board: { type: Object, required: true },
  // This turn's scenario card and whose turn it is, for "discard & draw another"
  turnScenario: { type: String, default: null },
  turnUserId: { type: [Number, String], default: null },
  isAdmin: { type: Boolean, default: false }
})

const emit = defineEmits(['visible'])

const AUTO_CLOSE_MS = 6000

const visible = ref(false)
const hold = ref(false)
let seenId = null
let showTimer = null
let closeTimer = null

const meta = computed(() => DECK_META[props.reveal?.deck] || DECK_META.collectable)
const actor = computed(() => props.playersById[props.reveal?.user_id] || null)
const target = computed(() => props.playersById[props.reveal?.target_user_id] || null)

const headline = computed(() => {
  const r = props.reveal
  if (!r) return ''
  const who = r.user_id === props.myUserId ? 'You' : actor.value?.username || 'Someone'
  switch (r.action) {
    case 'played': return `${who} played ${/^[AEIOU]/i.test(meta.value.label) ? 'an' : 'a'} ${meta.value.label.toLowerCase()}`
    case 'claimed': return `${who} completed an assignment`
    case 'introduced': return `${who} introduced a government oppression`
    case 'oppressed': return `${who} used an oppression${target.value ? ` on ${target.value.username}` : ''}`
    case 'assignment': return `${who} drew an assignment${target.value ? ` — target: ${target.value.username}` : ''}`
    default: return `${who} drew a ${meta.value.label} card`
  }
})

// The pending decision belongs to this reveal while the card is the same
const pendingHere = computed(() => {
  const p = props.pending
  const r = props.reveal
  return p && r?.pending && p.user_id === r.user_id ? p : null
})

const targetChoices = computed(() =>
  Object.values(props.playersById).filter(p => p.alive && p.user_id !== props.myUserId)
)
const replaceChoices = computed(() => props.assignments.filter(a => a.target !== props.myUserId))

function lineClass(line) {
  if (/\s\+\d/.test(line) || / took /.test(line)) return 'is-good'
  if (/\s−\d/.test(line) || /Jail|misses/.test(line)) return 'is-bad'
  return ''
}

function scheduleClose() {
  clearTimeout(closeTimer)
  if (pendingHere.value) return
  closeTimer = setTimeout(() => {
    if (hold.value) scheduleClose()
    else visible.value = false
  }, AUTO_CLOSE_MS)
}

function show(delay) {
  clearTimeout(showTimer)
  showTimer = setTimeout(() => {
    visible.value = true
    scheduleClose()
  }, delay)
}

// The scenario card drawn this turn can be swapped by whoever drew it, or the admin
const canRedraw = computed(() =>
  props.reveal?.deck === 'scenario' && Boolean(props.turnScenario) &&
  props.reveal?.card?.uid === props.turnScenario &&
  (props.turnUserId === props.myUserId || props.isAdmin)
)

async function redraw() {
  const applied = (props.reveal?.lines || []).length > 0
  const warning = applied ? ' What it has already done is not undone.' : ''
  if (await askConfirm(`Discard “${props.reveal?.card?.title}” and draw another scenario card?${warning}`)) {
    close()
    props.board.redrawScenario()
  }
}

function close() {
  clearTimeout(closeTimer)
  visible.value = false
}

/** Re-open the latest card (from the deck, or "choose a target" in the turn panel). */
function open() {
  if (!props.reveal) return
  show(0)
}

watch(() => [props.ready, props.reveal?.id], ([ready, id]) => {
  if (!ready) return
  if (seenId === null) {
    // First board state: don't replay an old card, unless it is waiting on me.
    seenId = id ?? 0
    if (id != null && pendingHere.value?.user_id === props.myUserId) show(300)
    return
  }
  if (id == null || id === seenId) return
  seenId = id
  const r = props.reveal
  const fromRoll = r.after_roll != null && props.lastRoll?.id === r.after_roll
  show(fromRoll ? moveDurationMs(props.lastRoll) + 250 : 0)
}, { immediate: true })

watch(hold, (h) => { if (!h && visible.value) scheduleClose() })
watch(() => visible.value && Boolean(props.reveal) && !props.holdBack, (v) => emit('visible', v))
watch(pendingHere, (p) => { if (!p && visible.value) scheduleClose() })

onBeforeUnmount(() => {
  clearTimeout(showTimer)
  clearTimeout(closeTimer)
})

defineExpose({ open })
</script>

<style scoped>
.reveal {
  position: absolute;
  inset: 0;
  z-index: 40;
  display: grid;
  place-items: center;
  padding: 16px;
  background: radial-gradient(circle at 50% 45%, rgba(11, 15, 25, 0.55), rgba(11, 15, 25, 0.88));
  backdrop-filter: blur(3px);
}

.reveal__panel {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  max-width: 460px;
  width: 100%;
  font-family: 'Barlow Condensed', 'Segoe UI', sans-serif;
  color: #E2E8F0;
}

.reveal__headline {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 999px;
  background: rgba(11, 15, 25, 0.85);
  border: 1px solid rgba(234, 179, 8, 0.4);
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.reveal__dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.4);
}

/* Card flip: the back shows first, then the card turns over */
.reveal__flip {
  position: relative;
  perspective: 1200px;
  display: grid;
}

.reveal__back,
.reveal__front {
  grid-area: 1 / 1;
  backface-visibility: hidden;
}

.reveal__back {
  --tone: #8B5CF6;
  display: grid;
  place-items: center;
  border-radius: 12px;
  font-size: 4.5rem;
  background:
    repeating-linear-gradient(45deg, rgba(255, 255, 255, 0.07) 0 10px, transparent 10px 20px),
    linear-gradient(160deg, color-mix(in srgb, var(--tone) 85%, #fff), color-mix(in srgb, var(--tone) 60%, #000));
  border: 2px solid rgba(255, 255, 255, 0.35);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.55);
  animation: flip-back 1s cubic-bezier(0.3, 0.7, 0.3, 1) both;
}

.reveal__front {
  animation: flip-front 1s cubic-bezier(0.3, 0.7, 0.3, 1) both;
}

@keyframes flip-back {
  0%   { transform: translateY(-40px) scale(0.7) rotateY(0deg); opacity: 0; }
  30%  { transform: translateY(0) scale(1) rotateY(0deg); opacity: 1; }
  100% { transform: rotateY(180deg); }
}

@keyframes flip-front {
  0%, 30% { transform: rotateY(-180deg); }
  100%    { transform: rotateY(0deg); }
}

.reveal__lines,
.reveal__notes {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 6px;
}

.reveal__lines li {
  padding: 4px 10px;
  border-radius: 8px;
  background: rgba(30, 41, 59, 0.92);
  border: 1px solid rgba(148, 163, 184, 0.3);
  font-size: 1.05rem;
  font-weight: 700;
  animation: line-in 0.35s ease-out both;
}

.reveal__lines li.is-good { color: #86EFAC; border-color: rgba(74, 222, 128, 0.45); }
.reveal__lines li.is-bad { color: #FCA5A5; border-color: rgba(248, 113, 113, 0.45); }

.reveal__notes li {
  padding: 4px 10px;
  border-radius: 8px;
  background: rgba(234, 179, 8, 0.15);
  color: #FDE68A;
  font-size: 0.95rem;
}

@keyframes line-in {
  from { transform: translateY(6px); opacity: 0; }
  to   { transform: none; opacity: 1; }
}

.reveal__decide {
  width: 100%;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(11, 15, 25, 0.9);
  border: 1px solid rgba(234, 179, 8, 0.45);
  text-align: center;
}

.reveal__ask {
  margin-bottom: 8px;
  font-size: 1.05rem;
  font-weight: 700;
  color: #FDE68A;
}

.reveal__choices {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 6px;
}

.reveal__choice {
  --pawn: #94A3B8;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.4);
  background: #1A1F2E;
  color: #F1F5F9;
  font-family: inherit;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.12s, border-color 0.15s;
}

.reveal__choice:hover {
  transform: translateY(-1px);
  border-color: #EAB308;
}

.reveal__choice--muted { color: #94A3B8; font-weight: 600; }

.reveal__choice-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--pawn);
}

.reveal__waiting {
  color: #CBD5E1;
  font-size: 1rem;
}

.reveal__close {
  padding: 5px 18px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: rgba(15, 23, 42, 0.9);
  color: #CBD5E1;
  font-family: inherit;
  font-size: 0.95rem;
  cursor: pointer;
}

.reveal__close:hover { color: #fff; border-color: #EAB308; }

.reveal__buttons { display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; }
.reveal__close--redraw { border-color: rgba(167, 139, 250, 0.6); color: #C4B5FD; }

.reveal__timer {
  width: 120px;
  height: 3px;
  border-radius: 2px;
  background: #EAB308;
  transform-origin: left;
  animation: timer 9s linear both;
}

@keyframes timer {
  from { transform: scaleX(1); }
  to   { transform: scaleX(0); }
}

.reveal-enter-active,
.reveal-leave-active { transition: opacity 0.25s ease; }
.reveal-enter-from,
.reveal-leave-to { opacity: 0; }

</style>
