<template>
  <div class="game-board" :style="{ '--grid': GRID_TEMPLATE }">
    <!-- ================= Track ================= -->
    <div class="game-board__grid">
      <button
        v-for="tile in tiles"
        :key="tile.index"
        type="button"
        class="tile"
        :class="[
          `tile--${theme(tile).tone}`,
          `tile--${tileSide(tile.index)}`,
          {
            'is-current': tile.index === currentPawnTile,
            'is-landing': tile.index === landingTile,
            'is-selected': tile.index === selectedTile
          }
        ]"
        :style="{
          gridRow: tileGridPosition(tile.index).row + 1,
          gridColumn: tileGridPosition(tile.index).col + 1,
          '--glow': currentColor
        }"
        :aria-label="`${tile.label}. ${tileDescription(tile, { doctorInPlay })}`"
        @click="openTile(tile.index)"
      >
        <span class="tile__card">
          <!-- Only Start keeps an icon; every other tile is just its words -->
          <span v-if="tile.kind === 'start'" class="tile__icon">{{ theme(tile).icon }}</span>
          <span class="tile__label">{{ tile.label }}</span>
          <span v-if="subLabel(tile)" class="tile__sub">{{ subLabel(tile) }}</span>
        </span>
      </button>

      <!-- ================= Centre ================= -->
      <div class="board-center" :style="{ inset: `${CENTER_INSET}%` }">
        <svg class="board-center__flow" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          <rect x="2.5" y="2.5" width="95" height="95" rx="5" class="board-center__flow-line" />
          <!-- One arrow centred on each side, all pointing clockwise -->
          <path d="M2.5 47.5 L0 52.5 L5 52.5 Z" class="board-center__flow-head" />
          <path d="M52.5 2.5 L47.5 0 L47.5 5 Z" class="board-center__flow-head" />
          <path d="M97.5 52.5 L95 47.5 L100 47.5 Z" class="board-center__flow-head" />
          <path d="M47.5 97.5 L52.5 95 L52.5 100 Z" class="board-center__flow-head" />
        </svg>

        <div class="board-center__brand">
          <span class="board-center__wordmark">Gerry's Game</span>
          <span v-if="state?.game_version_name" class="board-center__version">{{ state.game_version_name }}</span>
        </div>

        <div class="board-center__turn">
          <template v-if="state?.phase === 'initiative'">
            <span class="board-center__turn-text"><strong>Everyone rolls</strong> · highest goes first</span>
          </template>
          <template v-else-if="!state?.started">
            <span class="board-center__turn-text">Waiting for the admin to start the game</span>
          </template>
          <template v-else-if="currentPlayer">
            <span class="board-center__turn-dot" :style="{ background: currentColor }" />
            <span class="board-center__turn-text">
              Round {{ state.round }} ·
              <strong>{{ currentPlayer.user_id === myUserId ? 'Your' : `${currentPlayer.username}'s` }}</strong> turn
            </span>
          </template>
        </div>

        <!-- Scenario deck -->
        <button
          type="button"
          class="deck deck--scenario board-center__scen"
          title="Scenario deck: draw & play a card, shuffle, or see the played cards"
          @click="$emit('open-scenario-deck')"
        >
          <span class="deck__card" /><span class="deck__card" /><span class="deck__card deck__card--top">
            <span class="deck__glyph">🃏</span>
            <span class="deck__title">Scenario</span>
            <span class="deck__hint">{{ deckHint('scenario') }}</span>
          </span>
        </button>

        <!-- Dice tray + Reaper's counter -->
        <div class="board-center__tray">
          <component
            :is="canRoll ? 'button' : 'div'"
            :type="canRoll ? 'button' : undefined"
            class="dice-tray"
            :class="[`dice-tray--${dice.kind}`, { 'is-rollable': canRoll }]"
            :title="canRoll ? 'Click to roll' : undefined"
            @click="canRoll && $emit('roll')"
          >
            <BoardDie
              v-for="(v, i) in dice.values"
              :key="`${dice.rollId}-${i}`"
              :value="v"
              :animate="dice.animate"
              :variant="dice.variant"
              size="5.4cqw"
            />
          </component>
          <div class="dice-caption" :class="{ 'is-cta': canRoll }">{{ canRoll ? '👆 Click the die to roll' : diceCaption }}</div>

          <div class="reaper" :title="reaperTitle">
            <svg viewBox="0 0 100 100" class="reaper__dial">
              <circle cx="50" cy="50" r="42" class="reaper__track" />
              <circle
                v-for="(h, i) in HORSEMEN"
                :key="h.name"
                cx="50" cy="50" r="42"
                class="reaper__quarter"
                :stroke="h.color"
                :stroke-dasharray="`${QUARTER - 1.5} ${CIRC - QUARTER + 1.5}`"
                :stroke-dashoffset="-(i * QUARTER)"
              />
              <circle
                cx="50" cy="50" r="42"
                class="reaper__progress"
                :stroke="horseman?.color || '#64748B'"
                :stroke-dasharray="`${progressLength} ${CIRC}`"
              />
              <circle cx="50" cy="50" r="33" class="reaper__face" />
              <text x="50" y="52" class="reaper__number">{{ reaperCounter }}</text>
            </svg>
            <div class="reaper__label">
              <template v-if="reaperArrived">
                <strong :style="{ color: horseman?.color }">{{ horseman?.name || 'The Reaper' }}</strong>
                <span v-if="!horseman">walks the board</span>
              </template>
              <template v-else-if="reaperArrivesAt">
                <span>Reaper in</span>
                <strong>{{ reaperCountdown }}</strong>
              </template>
              <template v-else>
                <span>The Reaper</span>
              </template>
            </div>
          </div>
        </div>

        <!-- Collectable deck -->
        <button
          type="button"
          class="deck deck--collectable board-center__coll"
          :class="{ 'is-cta': canBuyCollectable }"
          :title="canBuyCollectable ? `Click to buy collectables (${collectablePrice} each)`
            : 'Collectable deck: buy, shuffle, or see the discard pile'"
          @click="$emit('open-collectable-deck')"
        >
          <span class="deck__card" /><span class="deck__card" /><span class="deck__card deck__card--top">
            <span class="deck__glyph">🎴</span>
            <span class="deck__title">Collectable</span>
            <span class="deck__hint">{{ deckHint('collectable') }}</span>
            <span v-if="state?.decks?.collectable?.discard" class="deck__hint deck__hint--used">{{ state.decks.collectable.discard }} used</span>
          </span>
          <span v-if="canBuyCollectable" class="deck__cta">👆 Buy · {{ collectablePrice }}</span>
        </button>

        <!-- Jail -->
        <div class="jail board-center__jail" :class="{ 'has-inmates': jailed.length }">
          <div class="jail__bars" aria-hidden="true" />
          <div class="jail__title">Jail</div>
          <div class="jail__inmates">
            <div
              v-for="p in jailed"
              :key="p.user_id"
              class="jail__pawn"
              :title="`${p.username} is in Jail`"
            >
              <BoardPawn :color="p.color" :piece="p.piece" />
            </div>
          </div>
          <div class="jail__fee">{{ jailFeeHours }}h to walk free</div>
        </div>

        <div class="board-center__rules">
          <span>Collectables: <strong>no limit</strong> · max <strong>1</strong> promotion card</span>
          <span class="board-center__rules-bonus">No Bleed = +1 Collectable</span>
        </div>
      </div>

      <!-- ================= Big roll (everyone sees it) ================= -->
      <transition name="dice-stage">
        <div
          v-if="bigRoll.show"
          class="dice-stage"
          :class="`dice-stage--${bigRoll.kind}`"
          :style="{ inset: `${CENTER_INSET}%`, '--who': bigRoll.color }"
          aria-live="polite"
        >
          <div class="dice-stage__who">
            <span class="dice-stage__dot" />{{ bigRoll.who }}
          </div>
          <div class="dice-stage__dice">
            <BoardDie
              v-for="(v, i) in bigRoll.values"
              :key="`${bigRoll.id}-${i}`"
              :value="v"
              :animate="true"
              :variant="bigRoll.variant"
              size="12cqw"
            />
          </div>
          <div class="dice-stage__result" :class="{ 'is-shown': bigRoll.settled }">{{ bigRoll.result }}</div>
        </div>
      </transition>

      <!-- ================= Pawns ================= -->
      <div class="board-pawns">
        <button
          v-for="pawn in pawnPlacements"
          :key="pawn.user_id"
          type="button"
          class="pawn"
          :class="{
            'is-current': pawn.user_id === state?.turn?.user_id && state?.started,
            'is-dead': !pawn.alive,
            'is-me': pawn.user_id === myUserId
          }"
          :style="{ left: `${pawn.x}%`, top: `${pawn.y}%`, '--pawn': pawn.color, zIndex: Math.round(pawn.y * 10) }"
          :title="pawn.alive ? pawn.username : `${pawn.username} (servant of the Reaper)`"
          @click="openTile(pawn.tile)"
        >
          <span class="pawn__halo" />
          <span :key="hopTick[pawn.user_id] || 0" class="pawn__hop">
            <BoardPawn :color="pawn.color" :piece="pawn.piece" />
          </span>
          <span v-if="!pawn.alive" class="pawn__skull">💀</span>
          <span class="pawn__tag">{{ pawn.username }}</span>
        </button>
      </div>

      <!-- ================= Tile popover ================= -->
      <div v-if="selectedTile !== null" class="tile-pop-backdrop" @click="selectedTile = null" />
      <div
        v-if="selectedTileData"
        class="tile-pop"
        :class="popoverAnchor"
        :style="popoverStyle"
        role="dialog"
        :aria-label="selectedTileData.label"
      >
        <div class="tile-pop__head" :class="`tile-pop__head--${theme(selectedTileData).tone}`">
          <span class="tile-pop__icon">{{ theme(selectedTileData).icon }}</span>
          <span class="tile-pop__title">{{ selectedTileData.label }}</span>
          <button type="button" class="tile-pop__close" aria-label="Close" @click="selectedTile = null">×</button>
        </div>
        <p class="tile-pop__text">{{ tileDescription(selectedTileData, { doctorInPlay }) }}</p>

        <div v-if="pawnsOn(selectedTile).length" class="tile-pop__here">
          <span class="tile-pop__here-label">Here:</span>
          <span v-for="p in pawnsOn(selectedTile)" :key="p.user_id" class="tile-pop__chip">
            <span class="tile-pop__dot" :style="{ background: p.color }" />{{ p.username }}
          </span>
        </div>

        <div v-if="canMoveSelf || isAdmin" class="tile-pop__actions">
          <button v-if="canMoveSelf" type="button" class="tile-pop__btn" @click="moveHere(myUserId)">
            ✋ Move my pawn here
          </button>
          <div v-if="isAdmin" class="tile-pop__admin">
            <select v-model="adminTarget" class="tile-pop__select" aria-label="Player to move">
              <option v-for="p in players" :key="p.user_id" :value="p.user_id">{{ p.username }}</option>
            </select>
            <button type="button" class="tile-pop__btn tile-pop__btn--admin" @click="moveHere(adminTarget)">
              Move (admin)
            </button>
          </div>
          <p class="tile-pop__note">Manual moves skip tile effects and are written to the game log.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import BoardDie from '@/components/board/BoardDie.vue'
import BoardPawn from '@/components/board/BoardPawn.vue'
import {
  GRID_TEMPLATE,
  CENTER_INSET,
  JAIL,
  HORSEMEN,
  tileGridPosition,
  tileSide,
  tileCenter,
  pawnOffsets,
  tileTheme,
  tileDescription,
  tileSubLabel,
  horsemanFor,
  formatCountdown,
  DIE_SETTLE_MS as DIE_MS,
  STEP_MS as HOP_MS
} from '@/components/board/boardLayout'

const props = defineProps({
  state: { type: Object, default: null },
  // [{ user_id, username, color (hex), alive, jailed }]
  players: { type: Array, default: () => [] },
  myUserId: { type: [Number, String], default: null },
  isAdmin: { type: Boolean, default: false },
  doctorInPlay: { type: Boolean, default: false },
  jailFeeHours: { type: Number, default: 8 },
  serverOffsetMs: { type: Number, default: 0 },
  // It's my turn and I haven't rolled: the die in the centre is a button
  canRoll: { type: Boolean, default: false },
  // I'm on a Collectables tile and can buy more: the collectable pile is a button
  canBuyCollectable: { type: Boolean, default: false },
  collectablePrice: { type: String, default: '1h' }
})

const emit = defineEmits(['move-token', 'roll', 'open-card', 'open-discard', 'open-collectable-deck', 'open-scenario-deck', 'landed'])

function deckHint(deck) {
  const d = props.state?.decks?.[deck]
  if (!d) return deck === 'collectable' ? '1 hour each' : 'card'
  return `${d.draw} left`
}

const tiles = computed(() => props.state?.tiles || [])
const theme = (tile) => tileTheme(tile.kind)
const subLabel = (tile) => tileSubLabel(tile, { doctorInPlay: props.doctorInPlay })

const playersById = computed(() => {
  const map = {}
  props.players.forEach(p => { map[p.user_id] = p })
  return map
})

const currentPlayer = computed(() => {
  const id = props.state?.turn?.user_id
  return id == null ? null : playersById.value[id] || null
})
const currentColor = computed(() => currentPlayer.value?.color || '#EAB308')

// ---------------------------------------------------------------------------
// Pawn positions and movement animation
// ---------------------------------------------------------------------------

// Rolls and moves always animate, even with the OS "reduce motion" setting:
// they are how the table sees what happened (Windows turns that setting on
// whenever "Animation effects" is off). Only decorative loops are toned down.
// How far below a tile's centre pawns stand (% of the board)
const PAWN_DROP = 5.4
const DIE_SETTLE_MS = DIE_MS
const STEP_MS = HOP_MS

// What's drawn, which lags the server while a move is being animated
const displayPos = reactive({})
const hopTick = reactive({})
const animating = new Set()
const landingTile = ref(null)
let seenRollId = null
let unmounted = false
let landingTimer = null

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

function serverPosition(uid) {
  const p = playersById.value[uid]
  if (p?.jailed) return JAIL
  const pos = props.state?.positions?.[String(uid)]
  return pos === undefined || pos === null ? 0 : pos
}

function syncPositions() {
  props.players.forEach(p => {
    if (!animating.has(p.user_id)) displayPos[p.user_id] = serverPosition(p.user_id)
  })
}

async function animateMove(roll, wait = DIE_SETTLE_MS) {
  const uid = roll.user_id
  animating.add(uid)
  await sleep(wait)
  for (const tile of roll.path || []) {
    if (unmounted) return
    displayPos[uid] = tile
    hopTick[uid] = (hopTick[uid] || 0) + 1
    await sleep(STEP_MS)
  }
  if (roll.jumped_from !== null && roll.jumped_from !== undefined) {
    // "Go to the Job Centre": pause on the tile, then glide across
    await sleep(350)
    displayPos[uid] = roll.to
    await sleep(500)
  }
  if (unmounted) return
  animating.delete(uid)
  landingTile.value = roll.to
  clearTimeout(landingTimer)
  landingTimer = setTimeout(() => { landingTile.value = null }, 1800)
  syncPositions()
  // The pawn is on its tile: the tile's pop-ups can open now
  emit('landed', roll.id)
}

// ---------------------------------------------------------------------------
// Dice
// ---------------------------------------------------------------------------

const DIE_VARIANT = { move: 'black', servant: 'bone', reaper: 'bone', virus: 'toxic', initiative: 'black' }
const dice = reactive({ values: [1], rollId: 0, animate: false, variant: 'black', kind: 'idle', roll: null })

function showRoll(roll, animate) {
  dice.values = roll.values?.length ? roll.values : [1]
  dice.rollId = roll.id
  dice.animate = animate
  dice.variant = DIE_VARIANT[roll.kind] || 'black'
  dice.kind = roll.kind
  dice.roll = roll
}

const diceCaption = computed(() => {
  const roll = dice.roll
  if (!roll) return props.state?.started ? 'Roll to move' : ''
  const who = roll.user_id != null ? playersById.value[roll.user_id]?.username || 'Someone' : 'The Reaper'
  const total = (roll.values || []).reduce((a, b) => a + b, 0)
  switch (roll.kind) {
    case 'move': return `${who} rolled ${total}`
    case 'virus': {
      const target = playersById.value[roll.target_user_id]?.username || 'someone'
      return `Virus on ${target}: −${total * 30}m`
    }
    case 'servant': return `${who} rolled ${total} for the Reaper`
    case 'reaper': return `The Reaper rolled ${total}`
    case 'initiative': return `${who} rolled ${total} for the first turn`
    default: return ''
  }
})

// The big roll in the middle of the board, so the whole table sees it
const bigRoll = reactive({ show: false, settled: false, id: 0, kind: 'move', values: [1], variant: 'black', who: '', color: '#EAB308', result: '' })
let bigTimers = []

function rollResultText(roll) {
  const total = (roll.values || []).reduce((a, b) => a + b, 0)
  switch (roll.kind) {
    case 'move': {
      const to = props.state?.tiles?.[roll.jumped_from ?? roll.to]?.label
      return to ? `${total} → ${to}` : String(total)
    }
    case 'virus': {
      const target = playersById.value[roll.target_user_id]?.username || 'someone'
      return `${total} — ${target} loses ${total * 30}m`
    }
    case 'servant': return `${total} for the Reaper`
    case 'reaper': return `${roll.values.join(' + ')} = ${total}`
    case 'initiative': return `${total} for the first turn`
    default: return String(total)
  }
}

function showBigRoll(roll) {
  bigTimers.forEach(clearTimeout)
  const p = roll.user_id != null ? playersById.value[roll.user_id] : null
  Object.assign(bigRoll, {
    show: true,
    settled: false,
    id: roll.id,
    kind: roll.kind,
    values: roll.values?.length ? roll.values : [1],
    variant: DIE_VARIANT[roll.kind] || 'black',
    who: roll.kind === 'reaper' ? '☠️ The Reaper rolls' : `${p?.username || 'Someone'} ${roll.kind === 'virus' ? 'releases the Time Virus' : 'rolls'}`,
    color: p?.color || '#A78BFA',
    result: rollResultText(roll)
  })
  bigTimers = [
    setTimeout(() => { bigRoll.settled = true }, DIE_SETTLE_MS),
    setTimeout(() => { bigRoll.show = false }, roll.kind === 'virus' ? 6000 : DIE_SETTLE_MS + 1100)
  ]
}

// One watcher for the whole payload: a new roll has to be noticed *before*
// positions are synced, or the pawn would jump straight to its new tile.
watch(() => props.state, (s) => {
  if (!s) return
  const roll = s.last_roll
  if (seenRollId === null) {
    seenRollId = roll?.id ?? 0
    if (roll && roll.kind !== 'card_move') showRoll(roll, false)
    if (roll) emit('landed', roll.id)  // joined after it: nothing to wait for
  } else if (roll && roll.id !== seenRollId && roll.kind === 'card_move') {
    // Moved by a card (Advance, Shortcut): hop along at once, the die stays as it was
    seenRollId = roll.id
    animateMove(roll, 150)
  } else if (roll && roll.id !== seenRollId) {
    seenRollId = roll.id
    showRoll(roll, true)
    // The first-turn roll has its own pop-up with the die
    if (roll.kind !== 'initiative') showBigRoll(roll)
    if (roll.kind === 'move') animateMove(roll)
  }
  syncPositions()
}, { immediate: true })

watch(() => props.players.map(p => `${p.user_id}:${p.jailed}`).join('|'), syncPositions)

const pawnPlacements = computed(() => {
  const byTile = {}
  props.players.forEach(p => {
    const tile = displayPos[p.user_id]
    if (tile === undefined || tile === JAIL) return
    ;(byTile[tile] = byTile[tile] || []).push(p)
  })
  const out = []
  Object.entries(byTile).forEach(([tile, list]) => {
    const centre = tileCenter(Number(tile))
    const offsets = pawnOffsets(list.length)
    // Stand along the bottom of the tile, clear of its text; extra rows stack upwards
    const lowest = Math.max(...offsets.map(o => o.dy))
    list.forEach((p, i) => {
      out.push({
        ...p,
        tile: Number(tile),
        x: centre.x + offsets[i].dx,
        y: centre.y + PAWN_DROP + offsets[i].dy - lowest
      })
    })
  })
  // Stable DOM order so CSS transitions survive re-grouping
  return out.sort((a, b) => a.user_id - b.user_id)
})

const jailed = computed(() => props.players.filter(p => displayPos[p.user_id] === JAIL))

const currentPawnTile = computed(() => {
  const id = props.state?.turn?.user_id
  if (!props.state?.started || id == null) return null
  const pos = displayPos[id]
  return pos === JAIL ? null : pos
})

function pawnsOn(tile) {
  return props.players.filter(p => displayPos[p.user_id] === tile)
}

// ---------------------------------------------------------------------------
// The Reaper
// ---------------------------------------------------------------------------

const CIRC = 2 * Math.PI * 42
const QUARTER = CIRC / 4

const nowMs = ref(Date.now())
let ticker = null
onMounted(() => { ticker = setInterval(() => { nowMs.value = Date.now() }, 1000) })
onBeforeUnmount(() => {
  unmounted = true
  clearInterval(ticker)
  clearTimeout(landingTimer)
  bigTimers.forEach(clearTimeout)
})

const reaperCounter = computed(() => props.state?.reaper?.counter || 0)
const horseman = computed(() => horsemanFor(reaperCounter.value))
const progressLength = computed(() => (Math.min(100, reaperCounter.value) / 100) * CIRC)
const reaperArrivesAt = computed(() => {
  const iso = props.state?.reaper?.arrives_at
  const t = iso ? Date.parse(iso) : NaN
  return Number.isNaN(t) ? null : t
})
const reaperRemaining = computed(() =>
  reaperArrivesAt.value === null ? null : reaperArrivesAt.value - (nowMs.value + props.serverOffsetMs)
)
const reaperArrived = computed(() => reaperRemaining.value !== null && reaperRemaining.value <= 0)
const reaperCountdown = computed(() => formatCountdown(reaperRemaining.value || 0))
const reaperTitle = computed(() => {
  if (!props.state?.started) return 'The Reaper arrives 2 hours after the game starts.'
  if (!reaperArrived.value) return 'When the Reaper arrives it rolls twice after the last player in every round.'
  return `Counter ${reaperCounter.value}. ${props.state?.reaper?.effect || ''}`
})

// ---------------------------------------------------------------------------
// Tile popover
// ---------------------------------------------------------------------------

const selectedTile = ref(null)
const adminTarget = ref(null)
const selectedTileData = computed(() =>
  selectedTile.value === null ? null : tiles.value[selectedTile.value] || null
)

const canMoveSelf = computed(() =>
  Boolean(props.state?.started) &&
  props.state?.turn?.user_id === props.myUserId &&
  !playersById.value[props.myUserId]?.jailed
)

function openTile(index) {
  selectedTile.value = selectedTile.value === index ? null : index
  if (adminTarget.value === null) adminTarget.value = props.state?.turn?.user_id ?? props.myUserId
}

function moveHere(userId) {
  if (userId === null || userId === undefined || selectedTile.value === null) return
  emit('move-token', { userId, tile: selectedTile.value })
  selectedTile.value = null
}

const popoverAnchor = computed(() => {
  if (selectedTile.value === null) return ''
  const { x, y } = tileCenter(selectedTile.value)
  return [x > 50 ? 'is-left' : 'is-right', y > 50 ? 'is-up' : 'is-down'].join(' ')
})

const popoverStyle = computed(() => {
  if (selectedTile.value === null) return {}
  const { x, y } = tileCenter(selectedTile.value)
  return { left: `${x}%`, top: `${y}%` }
})
</script>

<style scoped>
/* =====================================================================
   Board shell
   ===================================================================== */
.game-board {
  container-type: inline-size;
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  border-radius: 2.2cqw;
  padding: 0.9cqw;
  background:
    radial-gradient(120% 120% at 50% 0%, #1b2436 0%, #0f1522 55%, #0a0e17 100%);
  box-shadow:
    0 0 0 1px rgba(34, 211, 238, 0.18),
    0 0 0 0.6cqw rgba(11, 15, 25, 0.9),
    0 0 0 calc(0.6cqw + 1px) rgba(234, 179, 8, 0.35),
    0 3cqw 6cqw rgba(0, 0, 0, 0.6);
  font-family: 'Barlow Condensed', 'Segoe UI', sans-serif;
  user-select: none;
}

.game-board__grid {
  position: relative;
  width: 100%;
  height: 100%;
  display: grid;
  grid-template-columns: var(--grid);
  grid-template-rows: var(--grid);
}

/* =====================================================================
   Tiles
   ===================================================================== */
.tile {
  --accent: #94A3B8;
  --fill: linear-gradient(160deg, #1d2536 0%, #151b29 100%);
  --ink: #E2E8F0;
  --ink-soft: #94A3B8;
  position: relative;
  padding: 0.32cqw;
  border: 0;
  background: none;
  cursor: pointer;
  font: inherit;
  text-align: center;
  min-width: 0;
  min-height: 0;
}

.tile__card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  gap: 0.25cqw;
  width: 100%;
  height: 100%;
  padding: 1.3cqw 0.5cqw 0.5cqw;
  border-radius: 1.1cqw;
  background: var(--fill);
  border: 1px solid rgba(148, 163, 184, 0.14);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.06),
    0 0.4cqw 0.9cqw rgba(0, 0, 0, 0.35);
  overflow: hidden;
  transition: transform 0.18s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}

/* Accent bar along the inside edge of plain tiles */
.tile__card::before {
  content: '';
  position: absolute;
  left: 18%;
  right: 18%;
  top: 0;
  height: 0.32cqw;
  border-radius: 0 0 0.4cqw 0.4cqw;
  background: var(--accent);
  opacity: 0.9;
}

.tile:hover .tile__card,
.tile:focus-visible .tile__card {
  transform: translateY(-0.25cqw);
  border-color: rgba(234, 179, 8, 0.55);
}

.tile:focus-visible {
  outline: none;
}

.tile__icon {
  font-size: 2.1cqw;
  line-height: 1;
  filter: drop-shadow(0 0.2cqw 0.4cqw rgba(0, 0, 0, 0.5));
}

.tile__label {
  font-size: max(2.1cqw, 12px);
  font-weight: 700;
  line-height: 1.02;
  letter-spacing: 0.02em;
  color: var(--ink);
  text-transform: uppercase;
}

.tile__sub {
  font-size: max(1.75cqw, 11px);
  line-height: 1.12;
  color: var(--ink-soft);
  font-weight: 700;
  white-space: pre-line;
}

.tile--corner .tile__icon { font-size: 3cqw; }
.tile--corner .tile__label { font-size: 2.6cqw; }
.tile--corner .tile__sub { font-size: 1.95cqw; }

/* Tones ---------------------------------------------------------------- */
.tile--collectables { --accent: #2DD4BF; }
.tile--assignment   { --accent: #FB923C; }
.tile--scenario     { --accent: #A78BFA; }
.tile--virus        { --accent: #A3E635; }
.tile--jump         { --accent: #F472B6; }

.tile--start {
  --accent: #34D399;
  --fill: linear-gradient(160deg, #064e3b 0%, #052e25 100%);
  --ink-soft: #A7F3D0;
}

.tile--job {
  --accent: transparent;
  --fill: linear-gradient(160deg, #db2777 0%, #9d174d 100%);
  --ink: #fff;
  --ink-soft: #FBCFE8;
}

.tile--senate {
  --accent: transparent;
  --fill: linear-gradient(160deg, #3b82f6 0%, #1e40af 100%);
  --ink: #fff;
  --ink-soft: #DBEAFE;
}

.tile--hospital {
  --accent: transparent;
  --fill: linear-gradient(160deg, #fde047 0%, #eab308 100%);
  --ink: #1c1917;
  --ink-soft: #44403c;
}

.tile--market {
  --accent: #EAB308;
  --fill: linear-gradient(160deg, #0b0b0f 0%, #1c1917 100%);
  --ink: #FDE68A;
  --ink-soft: #A8A29E;
}

.tile--market .tile__card { border-color: rgba(234, 179, 8, 0.4); }

/* States ---------------------------------------------------------------- */
.tile.is-current .tile__card {
  border-color: var(--glow);
  box-shadow:
    0 0 0 0.18cqw var(--glow),
    0 0 2.2cqw color-mix(in srgb, var(--glow) 55%, transparent),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.tile.is-landing .tile__card {
  animation: tile-land 1.8s ease-out;
}

.tile.is-selected .tile__card {
  border-color: #EAB308;
}

@keyframes tile-land {
  0%   { transform: scale(1); filter: brightness(1); }
  15%  { transform: scale(1.06); filter: brightness(1.35); }
  40%  { transform: scale(1); filter: brightness(1.15); }
  100% { transform: scale(1); filter: brightness(1); }
}

/* =====================================================================
   Centre
   ===================================================================== */
.board-center {
  position: absolute;
  display: grid;
  grid-template-columns: 1fr 1.3fr 1fr;
  grid-template-rows: auto auto 1fr auto auto;
  grid-template-areas:
    "brand brand brand"
    "turn  turn  turn"
    "scen  tray  coll"
    "scen  jail  coll"
    "rules rules rules";
  gap: 1.1cqw 1.6cqw;
  padding: 3cqw 3.2cqw 2.4cqw;
  border-radius: 1.6cqw;
  background:
    radial-gradient(70% 60% at 50% 35%, rgba(34, 211, 238, 0.07), transparent 70%),
    linear-gradient(180deg, #121a2a 0%, #0d1320 100%);
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.1), inset 0 0 4cqw rgba(0, 0, 0, 0.55);
  margin: 0.4cqw;
}

.board-center__flow {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.board-center__flow-line {
  fill: none;
  stroke: rgba(234, 179, 8, 0.28);
  stroke-width: 0.35;
  stroke-dasharray: 1.6 2.4;
  vector-effect: non-scaling-stroke;
  animation: flow 3.5s linear infinite;
}

.board-center__flow-head {
  fill: rgba(234, 179, 8, 0.55);
}

@keyframes flow {
  to { stroke-dashoffset: -40; }
}

.board-center__version {
  display: block;
  margin-top: 0.3cqw;
  font-size: 1.4cqw;
  letter-spacing: 0.08em;
  color: #64748B;
}

.board-center__brand {
  grid-area: brand;
  text-align: center;
  line-height: 1;
}

.board-center__wordmark {
  display: inline-block;
  font-size: 5.6cqw;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  background: linear-gradient(180deg, #ffffff 0%, #cbd5e1 45%, #64748b 52%, #e2e8f0 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  filter: drop-shadow(0 0.35cqw 0 rgba(0, 0, 0, 0.55)) drop-shadow(0 0 1.4cqw rgba(34, 211, 238, 0.18));
}

.board-center__turn {
  grid-area: turn;
  justify-self: center;
  display: inline-flex;
  align-items: center;
  gap: 0.8cqw;
  padding: 0.45cqw 1.6cqw;
  border-radius: 999px;
  background: rgba(11, 15, 25, 0.7);
  border: 1px solid rgba(234, 179, 8, 0.35);
  color: #E2E8F0;
  font-size: 1.6cqw;
  letter-spacing: 0.02em;
}

.board-center__turn strong { color: #FDE68A; }

.board-center__turn-dot {
  width: 1.3cqw;
  height: 1.3cqw;
  border-radius: 50%;
  box-shadow: 0 0 0 0.25cqw rgba(255, 255, 255, 0.12), 0 0 1cqw currentColor;
}

.board-center__scen { grid-area: scen; }
.board-center__coll { grid-area: coll; }
.board-center__tray { grid-area: tray; }
.board-center__jail { grid-area: jail; }
.board-center__rules { grid-area: rules; }

/* Decks ---------------------------------------------------------------- */
.deck {
  position: relative;
  align-self: center;
  justify-self: center;
  width: 82%;
  aspect-ratio: 0.68;
  padding: 0;
  border: 0;
  background: none;
  font: inherit;
}

button.deck { cursor: pointer; }

.deck__card {
  position: absolute;
  inset: 0;
  border-radius: 1.1cqw;
  background: var(--deck-back);
  border: 1px solid rgba(255, 255, 255, 0.14);
  box-shadow: 0 0.5cqw 1.2cqw rgba(0, 0, 0, 0.5);
}

.deck__card:nth-child(1) { transform: translate(0.9cqw, 0.9cqw) rotate(3deg); opacity: 0.6; }
.deck__card:nth-child(2) { transform: translate(0.45cqw, 0.45cqw) rotate(1.5deg); opacity: 0.8; }

.deck__card--top {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.4cqw;
  transition: transform 0.25s ease;
}

.deck:hover .deck__card--top { transform: translateY(-0.6cqw) rotate(-1.5deg); }

.deck__glyph { font-size: 3.6cqw; }

.deck__title {
  font-size: 1.9cqw;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #fff;
}

.deck__hint--used { opacity: 0.75; }

.deck__hint {
  font-size: 1.65cqw;
  color: rgba(255, 255, 255, 0.75);
}

/* A pile you can click right now: it glows like the die does */
.deck.is-cta .deck__card--top {
  box-shadow: 0 0 0 0.25cqw #FDE68A, 0 0.5cqw 1.2cqw rgba(0, 0, 0, 0.5);
  animation: pile-me 1.4s ease-in-out infinite;
}

@keyframes pile-me {
  50% { box-shadow: 0 0 0 0.25cqw #FDE68A, 0 0 2.4cqw 0.6cqw rgba(253, 230, 138, 0.55); }
}

.deck__cta {
  position: absolute;
  left: 50%;
  bottom: -1.4cqw;
  transform: translateX(-50%);
  padding: 0.3cqw 1cqw;
  border-radius: 999px;
  background: #FDE68A;
  color: #1c1917;
  font-size: 1.45cqw;
  font-weight: 800;
  white-space: nowrap;
  box-shadow: 0 0.3cqw 0.8cqw rgba(0, 0, 0, 0.5);
  pointer-events: none;
}

.deck--scenario {
  --deck-back:
    repeating-linear-gradient(45deg, rgba(255, 255, 255, 0.05) 0 0.6cqw, transparent 0.6cqw 1.2cqw),
    linear-gradient(160deg, #6d28d9 0%, #3b0764 100%);
}

.deck--collectable {
  --deck-back:
    repeating-linear-gradient(-45deg, rgba(255, 255, 255, 0.05) 0 0.6cqw, transparent 0.6cqw 1.2cqw),
    linear-gradient(160deg, #0d9488 0%, #134e4a 100%);
}

/* Dice tray + Reaper --------------------------------------------------- */
.board-center__tray {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.8cqw;
  min-height: 0;
}

.dice-tray {
  display: flex;
  gap: 1.6cqw;
  justify-content: center;
  align-items: center;
  min-height: 7.4cqw;
  padding: 0.9cqw 1.8cqw;
  border-radius: 1.4cqw;
  background: radial-gradient(circle at 50% 40%, #1e293b, #0b1220 75%);
  box-shadow: inset 0 0.3cqw 1.2cqw rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(148, 163, 184, 0.12);
}

.dice-tray--virus { box-shadow: inset 0 0.3cqw 1.2cqw rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(163, 230, 53, 0.45); }
.dice-tray--reaper,
.dice-tray--servant { box-shadow: inset 0 0.3cqw 1.2cqw rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(167, 139, 250, 0.45); }

.dice-tray.is-rollable {
  border: 0;
  font: inherit;
  cursor: pointer;
  box-shadow: inset 0 0.3cqw 1.2cqw rgba(0, 0, 0, 0.7), 0 0 0 0.2cqw #EAB308;
  animation: roll-me 1.4s ease-in-out infinite;
}

.dice-tray.is-rollable:hover { transform: translateY(-0.3cqw) scale(1.04); }

@keyframes roll-me {
  0%, 100% { box-shadow: inset 0 0.3cqw 1.2cqw rgba(0, 0, 0, 0.7), 0 0 0 0.2cqw #EAB308, 0 0 0 0 rgba(234, 179, 8, 0.5); }
  50%      { box-shadow: inset 0 0.3cqw 1.2cqw rgba(0, 0, 0, 0.7), 0 0 0 0.2cqw #EAB308, 0 0 0 1.4cqw rgba(234, 179, 8, 0); }
}

.dice-caption {
  min-height: 1.6cqw;
  font-size: 1.75cqw;
  color: #CBD5E1;
  text-align: center;
  letter-spacing: 0.02em;
}

.dice-caption.is-cta { color: #FDE68A; font-weight: 700; }

/* Big roll ------------------------------------------------------------- */
.dice-stage {
  --who: #EAB308;
  position: absolute;
  z-index: 15;
  margin: 0.4cqw;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2.4cqw;
  border-radius: 1.6cqw;
  background: radial-gradient(circle at 50% 45%, rgba(15, 23, 42, 0.82), rgba(11, 15, 25, 0.94));
  backdrop-filter: blur(2px);
  pointer-events: none;
}

.dice-stage--virus { background: radial-gradient(circle at 50% 45%, rgba(54, 83, 20, 0.85), rgba(11, 15, 25, 0.95)); }
.dice-stage--reaper,
.dice-stage--servant { background: radial-gradient(circle at 50% 45%, rgba(59, 7, 100, 0.85), rgba(11, 15, 25, 0.95)); }

.dice-stage__who {
  display: flex;
  align-items: center;
  gap: 1cqw;
  padding: 0.6cqw 2cqw;
  border-radius: 999px;
  background: rgba(11, 15, 25, 0.8);
  border: 1px solid color-mix(in srgb, var(--who) 60%, transparent);
  font-size: 2.6cqw;
  font-weight: 800;
  letter-spacing: 0.03em;
  color: #F8FAFC;
}

.dice-stage__dot {
  width: 1.8cqw;
  height: 1.8cqw;
  border-radius: 50%;
  background: var(--who);
  box-shadow: 0 0 1.2cqw var(--who);
}

.dice-stage__dice {
  display: flex;
  gap: 4cqw;
  animation: dice-drop 0.45s cubic-bezier(0.3, 1.4, 0.5, 1) both;
}

@keyframes dice-drop {
  from { transform: translateY(-8cqw) scale(0.6); opacity: 0; }
  to   { transform: none; opacity: 1; }
}

.dice-stage__result {
  min-height: 5cqw;
  font-size: 4.2cqw;
  font-weight: 800;
  color: #FDE68A;
  text-shadow: 0 0 2cqw rgba(234, 179, 8, 0.5);
  opacity: 0;
  transform: scale(0.6);
  transition: opacity 0.25s ease, transform 0.35s cubic-bezier(0.3, 1.6, 0.5, 1);
}

.dice-stage__result.is-shown { opacity: 1; transform: none; }

.dice-stage-enter-active { transition: opacity 0.2s ease; }
.dice-stage-leave-active { transition: opacity 0.45s ease; }
.dice-stage-enter-from,
.dice-stage-leave-to { opacity: 0; }

.reaper {
  display: flex;
  align-items: center;
  gap: 1cqw;
}

.reaper__dial {
  width: 9.5cqw;
  height: 9.5cqw;
  transform: rotate(-90deg);
}

.reaper__track { fill: none; stroke: rgba(148, 163, 184, 0.12); stroke-width: 7; }
.reaper__quarter { fill: none; stroke-width: 7; opacity: 0.22; }
.reaper__progress {
  fill: none;
  stroke-width: 7;
  stroke-linecap: round;
  transition: stroke-dasharray 1.2s cubic-bezier(.2, .8, .2, 1), stroke 0.6s;
  filter: drop-shadow(0 0 3px currentColor);
}
.reaper__face { fill: #05070c; stroke: rgba(255, 255, 255, 0.08); stroke-width: 1; }
.reaper__number {
  transform: rotate(90deg);
  transform-origin: 50px 50px;
  fill: #F8FAFC;
  font-size: 30px;
  font-weight: 800;
  text-anchor: middle;
  dominant-baseline: middle;
  font-family: 'Barlow Condensed', sans-serif;
}

.reaper__label {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
  font-size: 1.6cqw;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.reaper__label strong {
  font-size: 2.1cqw;
  color: #E2E8F0;
  letter-spacing: 0.03em;
}

/* Jail ----------------------------------------------------------------- */
.jail {
  position: relative;
  display: grid;
  grid-template-rows: auto 1fr auto;
  justify-items: center;
  min-height: 9cqw;
  padding: 0.7cqw 1.2cqw;
  border-radius: 1.1cqw;
  background: #0b0f19;
  border: 1px solid rgba(148, 163, 184, 0.25);
  overflow: hidden;
}

.jail__bars {
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(90deg, transparent 0 2.2cqw, rgba(148, 163, 184, 0.16) 2.2cqw 2.5cqw);
  pointer-events: none;
}

.jail.has-inmates { border-color: rgba(239, 68, 68, 0.55); box-shadow: 0 0 1.6cqw rgba(239, 68, 68, 0.2); }

.jail__title {
  font-size: 1.7cqw;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #E2E8F0;
}

.jail__inmates {
  display: flex;
  gap: 0.6cqw;
  align-items: flex-end;
  min-height: 3.6cqw;
}

.jail__pawn { width: 2.8cqw; }

.jail__fee {
  font-size: 1.5cqw;
  color: #94A3B8;
}

/* Rules strip ---------------------------------------------------------- */
.board-center__rules {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.6cqw 1.6cqw;
  font-size: 1.55cqw;
  color: #94A3B8;
}

.board-center__rules strong { color: #E2E8F0; }

.board-center__rules-bonus {
  padding: 0.25cqw 1cqw;
  border: 1px solid rgba(234, 179, 8, 0.6);
  border-radius: 0.6cqw;
  color: #FDE68A;
  font-weight: 700;
}

/* =====================================================================
   Pawns
   ===================================================================== */
.board-pawns {
  position: absolute;
  inset: 0;
  z-index: 5; /* own stacking context: per-pawn z-index stays inside it */
  pointer-events: none;
}

.pawn {
  position: absolute;
  width: 3.4cqw;
  padding: 0;
  border: 0;
  background: none;
  transform: translate(-50%, -78%);
  transition: left 0.26s cubic-bezier(.3, .7, .4, 1), top 0.26s cubic-bezier(.3, .7, .4, 1);
  pointer-events: auto;
  cursor: pointer;
}

.pawn__hop {
  display: block;
  /* A light rim so pawns stay visible on same-coloured tiles */
  filter: drop-shadow(0 0 1px rgba(255, 255, 255, 0.7)) drop-shadow(0 0.3cqw 0.4cqw rgba(0, 0, 0, 0.5));
  animation: pawn-hop 0.27s ease-out;
}

.pawn.is-current .pawn__hop {
  animation: pawn-hop 0.27s ease-out, pawn-bob 1.6s ease-in-out 0.3s infinite;
}

.pawn__halo {
  position: absolute;
  left: 50%;
  bottom: -3%;
  width: 150%;
  height: 34%;
  transform: translateX(-50%);
  border-radius: 50%;
  background: radial-gradient(closest-side, var(--pawn), transparent);
  opacity: 0;
}

.pawn.is-current .pawn__halo {
  animation: halo 1.6s ease-in-out infinite;
}

.pawn.is-dead {
  filter: grayscale(1) brightness(0.6);
  opacity: 0.75;
}

.pawn__skull {
  position: absolute;
  top: -18%;
  right: -28%;
  font-size: 1.5cqw;
}

.pawn__tag {
  position: absolute;
  left: 50%;
  top: -42%;
  transform: translateX(-50%) translateY(0.4cqw);
  padding: 0.15cqw 0.7cqw;
  border-radius: 0.5cqw;
  background: rgba(11, 15, 25, 0.92);
  border: 1px solid var(--pawn);
  color: #F1F5F9;
  font-size: 1.15cqw;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s, transform 0.15s;
}

.pawn:hover .pawn__tag,
.pawn:focus-visible .pawn__tag {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

@keyframes pawn-hop {
  0%   { transform: translateY(0) scale(1, 1); }
  40%  { transform: translateY(-55%) scale(0.96, 1.05); }
  85%  { transform: translateY(0) scale(1.06, 0.94); }
  100% { transform: translateY(0) scale(1, 1); }
}

@keyframes pawn-bob {
  0%, 100% { transform: translateY(0); }
  50%      { transform: translateY(-12%); }
}

@keyframes halo {
  0%, 100% { opacity: 0.35; transform: translateX(-50%) scale(0.85); }
  50%      { opacity: 0.85; transform: translateX(-50%) scale(1.1); }
}

/* =====================================================================
   Tile popover
   ===================================================================== */
.tile-pop-backdrop {
  position: absolute;
  inset: 0;
  z-index: 20;
}

.tile-pop {
  position: absolute;
  z-index: 21;
  width: min(300px, 34cqw);
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(15, 20, 32, 0.97);
  border: 1px solid rgba(234, 179, 8, 0.45);
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.6);
  color: #E2E8F0;
  font-family: 'Segoe UI', system-ui, sans-serif;
  font-size: 0.85rem;
  animation: pop-in 0.16s ease-out;
}

.tile-pop.is-right { transform: translateX(4%); }
.tile-pop.is-left  { transform: translateX(-104%); }
.tile-pop.is-down  { margin-top: 2%; }
.tile-pop.is-up    { translate: 0 calc(-100% - 2cqw); }

@keyframes pop-in {
  from { opacity: 0; scale: 0.96; }
  to   { opacity: 1; scale: 1; }
}

.tile-pop__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: -12px -14px 10px;
  padding: 8px 12px;
  border-radius: 12px 12px 0 0;
  background: rgba(148, 163, 184, 0.1);
}

.tile-pop__head--job      { background: linear-gradient(90deg, #db2777, #9d174d); }
.tile-pop__head--senate   { background: linear-gradient(90deg, #3b82f6, #1e40af); }
.tile-pop__head--hospital { background: linear-gradient(90deg, #eab308, #a16207); }
.tile-pop__head--start    { background: linear-gradient(90deg, #059669, #064e3b); }
.tile-pop__head--market   { background: linear-gradient(90deg, #1c1917, #0b0b0f); }

.tile-pop__icon { font-size: 1.2rem; }

.tile-pop__title {
  flex: 1;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.15rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #fff;
}

.tile-pop__close {
  border: 0;
  background: none;
  color: rgba(255, 255, 255, 0.8);
  font-size: 1.3rem;
  line-height: 1;
  cursor: pointer;
}

.tile-pop__text {
  margin: 0 0 8px;
  line-height: 1.4;
  color: #CBD5E1;
  text-align: left;
}

.tile-pop__here {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.tile-pop__here-label { color: #94A3B8; }

.tile-pop__chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.12);
}

.tile-pop__dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}

.tile-pop__actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-top: 8px;
  border-top: 1px solid rgba(148, 163, 184, 0.15);
}

.tile-pop__admin {
  display: flex;
  gap: 6px;
}

.tile-pop__select {
  flex: 1;
  min-width: 0;
  padding: 5px 8px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: #0B0F19;
  color: #E2E8F0;
}

.tile-pop__btn {
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid rgba(234, 179, 8, 0.6);
  background: rgba(234, 179, 8, 0.14);
  color: #FDE68A;
  font-weight: 600;
  cursor: pointer;
}

.tile-pop__btn:hover { background: rgba(234, 179, 8, 0.26); }

.tile-pop__btn--admin {
  border-color: rgba(34, 211, 238, 0.6);
  background: rgba(34, 211, 238, 0.12);
  color: #A5F3FC;
}

.tile-pop__note {
  margin: 0;
  font-size: 0.75rem;
  color: #64748B;
  text-align: left;
}

@media (prefers-reduced-motion: reduce) {
  .board-center__flow-line,
  .pawn.is-current .pawn__hop { animation: pawn-hop 0.27s ease-out; }
  .pawn.is-current .pawn__halo,
  .dice-tray.is-rollable { animation: none; }
}
</style>
