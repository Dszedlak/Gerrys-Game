<template>
  <!-- What you can do on the tile you landed on (shown in the action pop-up) -->
  <div v-if="tile" class="tile-action" :class="`tile-action--${tone}`">
    <div class="tile-action__head">
      <strong class="tile-action__name">{{ tile.label }}</strong>
      <button
        v-if="isShopTile"
        type="button"
        class="tile-action__info"
        :class="{ 'is-open': showRules }"
        :aria-expanded="showRules"
        :title="showRules ? 'Hide the rules for this tile' : 'What happens on this tile?'"
        @click="showRules = !showRules"
      >ⓘ</button>
      <slot name="head" />
    </div>
    <p v-if="showRules || !isShopTile" class="tile-action__text">{{ description }}</p>
    <p v-if="dealtText" class="tile-action__dealt">🎴 {{ dealtText }}</p>
    <p v-else-if="turn.dealt_note" class="tile-action__text">{{ turn.dealt_note }}</p>
    <p v-if="turn.no_access && !remoteSenate" class="tile-action__warn">
      You haven't left this building since your last turn, so you get no access this time{{ tile.kind === 'senate_virus' ? ' (the Time Virus still works)' : '' }}.
    </p>
    <p v-if="remoteSenate" class="tile-action__remote">
      📡 Remote Access: you can use the Senate from here this turn, as if you were standing in it.
    </p>

    <!-- Scenario tile: the card drawn on landing; swap it for another -->
    <template v-if="tile.kind === 'scenario' && turn.scenario">
      <button type="button" class="tile-action__btn tile-action__wide" @click="$emit('open-card')">
        🃏 {{ state?.event && !state.event.done ? 'Back to the card in play' : 'Show the card again' }}
      </button>
      <button type="button" class="tile-action__btn tile-action__wide tile-action__btn--redraw" @click="confirmRedraw">
        🔁 Discard this scenario card &amp; draw another
      </button>
    </template>

    <!-- A card that is waiting on my decision -->
    <button
      v-if="myPending"
      type="button"
      class="tile-action__btn tile-action__btn--primary tile-action__wide"
      @click="$emit('open-card')"
    >
      🃏 {{ myPending.kind === 'replace' ? 'Choose a slip to replace' : 'Choose a target for your card' }}
    </button>

    <!-- Shops: one tidy row per item -->
    <ul v-if="shopItems.length" class="shop">
      <li v-for="item in shopItems" :key="item.kind" class="shop__row" :class="{ 'is-off': item.disabled }">
        <span class="shop__name">
          {{ item.name }}
          <small v-if="item.note" class="shop__note">{{ item.note }}</small>
        </span>
        <span class="shop__price">{{ item.price }}</span>
        <span class="shop__controls">
          <span v-if="item.multi && !item.disabled && item.max > 1" class="shop__qty" role="group" :aria-label="`How many ${item.name.toLowerCase()}s`">
            <button type="button" :disabled="qtyOf(item) <= 1" aria-label="One fewer" @click="setQty(item, qtyOf(item) - 1)">−</button>
            <span class="shop__qty-n">{{ qtyOf(item) }}</span>
            <button type="button" :disabled="qtyOf(item) >= item.max" aria-label="One more" @click="setQty(item, qtyOf(item) + 1)">+</button>
          </span>
          <button
            type="button"
            class="shop__buy"
            :disabled="item.disabled"
            :title="item.disabledReason || (item.choose ? 'Choose a card from the discard pile' : `Buy ${qtyOf(item)} for ${totalPrice(item)}`)"
            @click="buy(item)"
          >{{ buyLabel(item) }}</button>
        </span>
      </li>
    </ul>
    <div v-if="shopLimit" class="shop__tally" :title="`You can buy up to ${shopLimit.max} here this turn`">
      <span class="shop__pips">
        <span v-for="n in shopLimit.max" :key="n" class="shop__pip" :class="{ 'is-on': n <= shopLimit.used }" />
      </span>
      <span>{{ shopLimit.used }} of {{ shopLimit.max }} bought</span>
    </div>

    <!-- Time Virus (tile 6, and the third Senate tile) -->
    <div v-if="isVirusTile" class="virus">
      <div class="virus__head">
        <span class="virus__title">🦠 Time Virus</span>
        <span class="virus__rule">They lose 30m per pip · 1 = 30m … 6 = 3h</span>
      </div>
      <p v-if="turn.virus_used" class="virus__done">The virus has been released this turn.</p>
      <template v-else>
        <div class="virus__label">Pick a victim</div>
        <div class="virus__targets" role="radiogroup" aria-label="Time Virus victim">
          <button
            v-for="p in virusTargets"
            :key="p.user_id"
            type="button"
            role="radio"
            class="virus__target"
            :class="{ 'is-on': virusTarget === p.user_id }"
            :style="{ '--pawn': p.color }"
            :aria-checked="virusTarget === p.user_id"
            @click="virusTarget = p.user_id"
          >
            <span class="virus__dot" />
            <span class="virus__name">{{ p.username }}<small v-if="p.isMe"> (you)</small></span>
          </button>
        </div>
        <button
          type="button"
          class="virus__roll"
          :disabled="virusTarget === null"
          @click="releaseVirus"
        >🎲 {{ virusTarget === null ? 'Pick a victim, then roll' : `Roll the virus on ${playersById[virusTarget]?.username}` }}</button>
      </template>
    </div>

    <!-- Senate: your own vote is free; one paid Senate action per visit -->
    <div v-if="isSenateTile" class="tile-action__row">
      <span class="tile-action__label">Your vote (free)</span>
      <div class="tile-action__seg" role="group" aria-label="Your approval">
        <button
          type="button"
          :class="{ 'is-on is-good': me?.approval === 'approve' }"
          :disabled="turn.no_access"
          @click="$emit('set-approval', 'approve')"
        >✓ Approve</button>
        <button
          type="button"
          :class="{ 'is-on is-bad': me?.approval === 'reject' }"
          :disabled="turn.no_access"
          @click="$emit('set-approval', 'reject')"
        >✗ Reject</button>
      </div>
    </div>

    <div v-if="isSenateTile" class="senate-votes">
      <div class="tile-action__label">
        Change another player's vote · {{ senateVoteCost }}
        <template v-if="turn.senate_used"> — you've taken your Senate action</template>
      </div>
      <ul class="senate-votes__list">
        <li v-for="p in voteTargets" :key="p.user_id" class="senate-votes__row">
          <span class="senate-votes__dot" :style="{ background: p.color }" />
          <span class="senate-votes__name">{{ p.username }}</span>
          <span class="senate-votes__now" :class="`is-${p.approval || 'none'}`">
            {{ p.approval === 'approve' ? '✓ approves' : p.approval === 'reject' ? '✗ rejects' : 'no vote' }}
          </span>
          <span class="senate-votes__btns">
            <button
              type="button"
              class="senate-votes__btn is-good"
              :class="{ 'is-current': p.approval === 'approve' }"
              :disabled="senateLocked || p.approval === 'approve'"
              :title="`Make ${p.username} approve (${senateVoteCost})`"
              @click="changeVote(p, 'approve')"
            >✓ Approve</button>
            <button
              type="button"
              class="senate-votes__btn is-bad"
              :class="{ 'is-current': p.approval === 'reject' }"
              :disabled="senateLocked || p.approval === 'reject'"
              :title="`Make ${p.username} reject (${senateVoteCost})`"
              @click="changeVote(p, 'reject')"
            >✗ Reject</button>
          </span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { askConfirm } from '@/composables/useConfirm'
import { ref, reactive, computed, watch } from 'vue'
import { tileTheme, tileDescription, formatPrice, PURCHASE_LIMIT, dealtSummary } from '@/components/board/boardLayout'

const props = defineProps({
  board: { type: Object, required: true },
  state: { type: Object, default: null },
  playersById: { type: Object, default: () => ({}) },
  myUserId: { type: [Number, String], default: null },
  doctorInPlay: { type: Boolean, default: false },
  // 2 under Democracy ("All purchases are double in price")
  priceMultiplier: { type: Number, default: 1 },
  governmentName: { type: String, default: 'Democracy' }
})

// `rolled`: a die was rolled from here (Time Virus), so the board should be in view
const emit = defineEmits(['open-card', 'open-discard', 'set-approval', 'rolled'])

const turn = computed(() => props.state?.turn || {})
const me = computed(() => props.playersById[props.myUserId] || null)

const tile = computed(() => {
  const pos = props.state?.positions?.[String(props.myUserId)]
  return pos === undefined || pos === null || pos < 0 ? null : props.state?.tiles?.[pos] || null
})

const myPending = computed(() => {
  const p = props.state?.pending
  return p && p.user_id === props.myUserId ? p : null
})

const tone = computed(() => tileTheme(tile.value?.kind).tone)
const dealtText = computed(() => dealtSummary(turn.value))
const description = computed(() => tileDescription(tile.value, { doctorInPlay: props.doctorInPlay }))
const isVirusTile = computed(() => ['time_virus', 'senate_virus'].includes(tile.value?.kind))
const onSenateTile = computed(() => ['senate', 'senate_virus'].includes(tile.value?.kind))
// Remote Access: the Senate from anywhere, this turn
const remoteSenate = computed(() => Boolean(turn.value.remote_senate) && !onSenateTile.value)
const isSenateTile = computed(() => onSenateTile.value || remoteSenate.value)

const showRules = ref(false)
watch(() => tile.value?.index, () => { showRules.value = false })

async function confirmRedraw() {
  if (await askConfirm('Discard this turn\'s scenario card and draw another? What it has already done is not undone.')) {
    props.board.redrawScenario()
  }
}

// --- Shops -----------------------------------------------------------------
function bought(kind) {
  return turn.value.purchases?.[kind] || 0
}
// Collectables: as many as you like (the hand limit is checked when you end your turn)
const collectablesInDeck = computed(() => {
  const d = props.state?.decks?.collectable
  return d ? d.draw + d.discard : 50
})
const hospitalLeft = computed(() => PURCHASE_LIMIT - bought('hospital'))

const unitMinutes = (minutes) => minutes * props.priceMultiplier
const price = (minutes) => formatPrice(unitMinutes(minutes))

const shopItems = computed(() => {
  const items = tileShopItems.value
  // Remote Access on a tile with its own shop: add the Senate's oppression row
  if (remoteSenate.value && !items.some(i => i.kind === 'oppression')) return [...items, ...oppressionRows()]
  return items
})

function oppressionRows() {
  // Introducing an oppression is a Senate action (not a purchase, so never doubled),
  // for members of a government that uses oppressions
  const gov = String(props.governmentName || '').toLowerCase()
  const noGov = !['communism', 'dictatorship', 'republic'].includes(gov)
  if (noGov || !me.value?.govRole) return []
  const inPlay = props.state?.oppressions?.length || 0
  const max = props.state?.max_oppressions || 4
  const used = Boolean(turn.value.senate_used)
  const noAccess = turn.value.no_access && !turn.value.remote_senate
  return [{
    kind: 'oppression', name: 'Government oppression', note: `${inPlay}/${max} in play`,
    price: formatPrice(props.state?.oppression_cost || 120), done: used, doneLabel: 'Done', buyLabel: 'Introduce',
    disabled: used || noAccess || inPlay >= max,
    disabledReason: used ? "You've taken your Senate action" : noAccess ? "You haven't left the Senate"
      : inPlay >= max ? `${max} oppressions are already in play` : '',
    action: () => props.board.introduceOppression()
  }]
}

const tileShopItems = computed(() => {
  const kind = tile.value?.kind
  const noAccess = turn.value.no_access
  if (kind === 'collectables') {
    const promoDone = bought('promotion') >= 1
    const empty = collectablesInDeck.value <= 0
    return [
      {
        kind: 'collectable', name: 'Collectable', note: bought('collectable') ? `${bought('collectable')} bought this turn` : 'buy as many as you like',
        price: price(60), minutes: unitMinutes(60), multi: true, max: Math.max(1, Math.min(50, collectablesInDeck.value)),
        disabled: empty, disabledReason: empty ? 'The collectable deck is empty' : ''
      },
      {
        kind: 'promotion', name: 'Promotion card', note: 'max 1', price: price(120), minutes: unitMinutes(120), done: promoDone,
        disabled: promoDone, disabledReason: promoDone ? 'Only one promotion card per visit' : ''
      }
    ]
  }
  if (kind === 'hospital') {
    const full = hospitalLeft.value <= 0
    const each = props.doctorInPlay ? 60 : 30
    return [{
      kind: 'hospital', name: 'Hospital item', note: props.doctorInPlay ? 'Doctor: ×2' : '',
      price: price(each), minutes: unitMinutes(each), multi: true, max: hospitalLeft.value,
      disabled: noAccess || full,
      disabledReason: noAccess ? "You haven't left the Hospital" : full ? `You have bought ${PURCHASE_LIMIT} this turn` : ''
    }]
  }
  if (kind === 'senate' || kind === 'senate_virus') return oppressionRows()
  if (kind === 'black_market') {
    const market = props.state?.decks?.collectable
    const done = bought('black_market') >= 1
    const empty = !market?.discard
    return [{
      kind: 'black_market', name: 'Used collectable', price: price(150), done, choose: true,
      note: market?.discard ? `${market.discard} for sale on the discard pile` : 'none for sale yet',
      disabled: done || empty, disabledReason: done ? 'One per visit' : empty ? 'Nobody has used a collectable yet' : ''
    }]
  }
  return []
})

const isShopTile = computed(() => shopItems.value.length > 0)

const shopLimit = computed(() => {
  const kind = tile.value?.kind
  if (kind === 'hospital') return { max: PURCHASE_LIMIT, used: bought('hospital') }
  return null
})

// How many to buy in one go, per item (collectables and hospital items)
const qty = reactive({})
function qtyOf(item) {
  if (!item.multi) return 1
  return Math.max(1, Math.min(qty[item.kind] || 1, item.max || 1))
}
function setQty(item, n) {
  qty[item.kind] = Math.max(1, Math.min(n, item.max || 1))
}
watch(() => tile.value?.index, () => { Object.keys(qty).forEach(k => delete qty[k]) })

function totalPrice(item) {
  return item.minutes ? formatPrice(item.minutes * qtyOf(item)) : item.price
}

function buyLabel(item) {
  if (item.done) return item.doneLabel || 'Bought'
  if (item.choose) return 'Choose…'
  if (item.buyLabel) return item.buyLabel
  const n = qtyOf(item)
  return n > 1 ? `Buy ${n} · ${totalPrice(item)}` : 'Buy'
}

function buy(item) {
  if (item.action) return item.action()
  if (item.choose) return emit('open-discard')
  const n = qtyOf(item)
  props.board.purchase(item.kind, null, n)
  qty[item.kind] = 1
}

// --- Senate: change another player's vote ----------------------------------
const SENATE_VOTE_MINUTES = 60
const senateVoteCost = formatPrice(SENATE_VOTE_MINUTES)
const voteTargets = computed(() => Object.values(props.playersById).filter(p => p.alive && p.user_id !== props.myUserId))
const senateLocked = computed(() => Boolean(turn.value.senate_used || (turn.value.no_access && !turn.value.remote_senate)))

async function changeVote(p, status) {
  if (!p) return
  const verdict = status === 'approve' ? 'approve' : 'reject'
  if (await askConfirm(`Pay ${senateVoteCost} to change ${p.username}'s vote to ${verdict}? This is your Senate action for this visit.`)) {
    props.board.senateVote(p.user_id, status)
  }
}

// --- Time Virus ------------------------------------------------------------
const virusTarget = ref(null)
const virusTargets = computed(() => Object.values(props.playersById).filter(p => p.alive))
watch(() => turn.value.user_id, () => { virusTarget.value = null })
function releaseVirus() {
  if (virusTarget.value === null) return
  props.board.timeVirus(virusTarget.value)
  emit('rolled', tile.value?.kind)
}
</script>

<style scoped>
.tile-action {
  --tone: #94A3B8;
  color: #E2E8F0;
  text-align: left;
}

.tile-action--collectables { --tone: #2DD4BF; }
.tile-action--assignment { --tone: #FB923C; }
.tile-action--scenario { --tone: #A78BFA; }
.tile-action--virus { --tone: #A3E635; }
.tile-action--jump,
.tile-action--job { --tone: #EC4899; }
.tile-action--senate { --tone: #3B82F6; }
.tile-action--hospital { --tone: #EAB308; }
.tile-action--start { --tone: #34D399; }
.tile-action--market { --tone: #EAB308; }

.tile-action__head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: 'Barlow Condensed', sans-serif;
}

.tile-action__name {
  flex: 1;
  font-size: 1.6rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: color-mix(in srgb, var(--tone) 70%, #fff);
}

.tile-action__info {
  width: 26px;
  height: 26px;
  padding: 0;
  border-radius: 50%;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: transparent;
  color: #94A3B8;
  font-size: 0.9rem;
  line-height: 1;
  cursor: pointer;
}

.tile-action__info:hover,
.tile-action__info.is-open { color: #FDE68A; border-color: #EAB308; }

.tile-action__text {
  margin: 6px 0 8px;
  font-size: 0.92rem;
  line-height: 1.5;
  color: #CBD5E1;
}

.tile-action__warn {
  margin: 4px 0 8px;
  padding: 6px 10px;
  border-radius: 6px;
  background: rgba(234, 179, 8, 0.12);
  color: #FDE68A;
  font-size: 0.82rem;
}

.tile-action__btn {
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: rgba(148, 163, 184, 0.08);
  color: #E2E8F0;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
}

.tile-action__btn:hover { border-color: #EAB308; }

.tile-action__btn--primary {
  background: linear-gradient(180deg, #EAB308, #CA8A04);
  border-color: #EAB308;
  color: #1c1917;
  font-weight: 800;
}

.tile-action__wide { width: 100%; margin-top: 8px; }

.tile-action__dealt {
  margin: 6px 0 4px;
  padding: 7px 10px;
  border-radius: 8px;
  background: rgba(45, 212, 191, 0.12);
  border: 1px solid rgba(45, 212, 191, 0.45);
  color: #99F6E4;
  font-size: 0.88rem;
  font-weight: 600;
}

.tile-action__remote {
  margin: 6px 0 2px;
  padding: 6px 10px;
  border-radius: 8px;
  background: rgba(59, 130, 246, 0.14);
  border: 1px solid rgba(59, 130, 246, 0.5);
  color: #BFDBFE;
  font-size: 0.85rem;
}

.tile-action__btn--redraw { border-color: rgba(167, 139, 250, 0.6); color: #DDD6FE; }

.tile-action__row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 8px;
  margin-top: 10px;
}

/* Small caption on its own line above the controls */
.tile-action__label {
  flex: 0 0 100%;
  font-size: 0.76rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #A5B4C8;
}

.tile-action__select {
  flex: 1;
  min-width: 0;
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: #0B0F19;
  color: #E2E8F0;
}

.tile-action__seg {
  display: flex;
  flex: 1;
  border-radius: 7px;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.3);
}

.tile-action__seg button {
  flex: 1;
  padding: 7px 0;
  border: 0;
  background: transparent;
  color: #CBD5E1;
  font-size: 0.86rem;
  font-weight: 700;
  cursor: pointer;
}

.tile-action__seg button + button { border-left: 1px solid rgba(148, 163, 184, 0.3); }
/* Senate: change another player's vote, one row per player */
.senate-votes { margin-top: 10px; }
.senate-votes__list { margin: 4px 0 0; padding: 0; list-style: none; }

.senate-votes__row {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
}

.senate-votes__dot { width: 10px; height: 10px; border-radius: 50%; }

.senate-votes__name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 1rem;
  font-weight: 700;
  color: #F8FAFC;
}

.senate-votes__now { font-size: 0.84rem; font-weight: 600; color: #A5B4C8; white-space: nowrap; }
.senate-votes__now.is-approve { color: #86EFAC; }
.senate-votes__now.is-reject { color: #FCA5A5; }

.senate-votes__btns { display: inline-flex; gap: 4px; }

.senate-votes__btn {
  padding: 5px 11px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.5);
  background: rgba(148, 163, 184, 0.08);
  color: #F1F5F9;
  font-size: 0.84rem;
  font-weight: 700;
  white-space: nowrap;
  cursor: pointer;
}

.senate-votes__btn.is-good:hover:not(:disabled) { border-color: #4ADE80; background: rgba(74, 222, 128, 0.14); color: #BBF7D0; }
.senate-votes__btn.is-bad:hover:not(:disabled) { border-color: #F87171; background: rgba(248, 113, 113, 0.14); color: #FECACA; }
.senate-votes__btn:disabled { opacity: 0.4; cursor: not-allowed; }
/* Their current vote: shown as set, not as a faded button */
.senate-votes__btn.is-current { opacity: 1; cursor: default; }
.senate-votes__btn.is-good.is-current { border-color: rgba(74, 222, 128, 0.6); background: rgba(74, 222, 128, 0.18); color: #BBF7D0; }
.senate-votes__btn.is-bad.is-current { border-color: rgba(248, 113, 113, 0.6); background: rgba(248, 113, 113, 0.18); color: #FECACA; }
.tile-action__seg button:disabled { opacity: 0.4; cursor: not-allowed; }
.tile-action__seg button.is-on.is-good { background: rgba(74, 222, 128, 0.16); color: #86EFAC; }
.tile-action__seg button.is-on.is-bad { background: rgba(248, 113, 113, 0.16); color: #FCA5A5; }

/* Shop rows */
.shop {
  margin: 8px 0 0;
  padding: 0;
  list-style: none;
  border-top: 1px solid rgba(148, 163, 184, 0.12);
}

.shop__row {
  display: grid;
  grid-template-columns: 1fr auto auto;
  align-items: center;
  gap: 12px;
  padding: 9px 0;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
}

.shop__name {
  min-width: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #E2E8F0;
}

.shop__note {
  display: block;
  font-size: 0.76rem;
  font-weight: 400;
  color: #64748B;
}

.shop__price {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.1rem;
  font-weight: 700;
  color: #FDE68A;
}

.shop__row.is-off .shop__name,
.shop__row.is-off .shop__price { opacity: 0.5; }

.shop__controls {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

/* − n + */
.shop__qty {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  overflow: hidden;
}

.shop__qty button {
  width: 28px;
  height: 28px;
  border: 0;
  background: transparent;
  color: #CBD5E1;
  font-size: 1.05rem;
  font-weight: 700;
  line-height: 1;
  cursor: pointer;
}

.shop__qty button:hover:not(:disabled) { background: rgba(148, 163, 184, 0.14); }
.shop__qty button:disabled { opacity: 0.3; cursor: not-allowed; }

.shop__qty-n {
  min-width: 22px;
  text-align: center;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.1rem;
  font-weight: 800;
  color: #F8FAFC;
}

.shop__buy {
  min-width: 70px;
  padding: 5px 14px;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--tone) 70%, transparent);
  background: color-mix(in srgb, var(--tone) 14%, transparent);
  color: color-mix(in srgb, var(--tone) 60%, #fff);
  font-size: 0.88rem;
  font-weight: 700;
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.15s ease, transform 0.12s ease;
}

.shop__buy:hover:not(:disabled) {
  background: color-mix(in srgb, var(--tone) 28%, transparent);
  transform: translateY(-1px);
}

.shop__buy:disabled { opacity: 0.4; cursor: not-allowed; }

.shop__buy--virus { --tone: #A3E635; }

.shop__tally {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
  font-size: 0.8rem;
  color: #64748B;
}

.shop__pips { display: inline-flex; gap: 3px; }

.shop__pip {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(148, 163, 184, 0.2);
}

.shop__pip.is-on { background: var(--tone); }

@media (max-width: 480px) {
  .shop__row { grid-template-columns: 1fr auto; }
  .shop__controls { grid-column: 1 / -1; }
}

/* Time Virus ------------------------------------------------------------ */
.virus {
  margin-top: 8px;
  padding: 10px 12px 12px;
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(163, 230, 53, 0.1), rgba(163, 230, 53, 0.03));
  border: 1px solid rgba(163, 230, 53, 0.4);
}

.virus__head { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 4px 10px; }

.virus__title {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.2rem;
  font-weight: 800;
  color: #D9F99D;
}

.virus__rule { font-size: 0.8rem; color: #BEF264; }

.virus__label {
  margin: 10px 0 6px;
  font-size: 0.76rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #CBD5E1;
}

.virus__targets { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 6px; }

.virus__target {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 9px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: rgba(15, 23, 42, 0.7);
  color: #F1F5F9;
  font-size: 0.92rem;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.virus__target:hover { border-color: rgba(163, 230, 53, 0.7); }
.virus__target.is-on { border-color: #A3E635; background: rgba(163, 230, 53, 0.18); box-shadow: 0 0 0 1px #A3E635; }

.virus__dot { width: 11px; height: 11px; flex: 0 0 11px; border-radius: 50%; background: var(--pawn); box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.25); }
.virus__name { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.virus__name small { color: #94A3B8; font-weight: 400; }

.virus__roll {
  width: 100%;
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #A3E635;
  background: linear-gradient(180deg, #84CC16, #4D7C0F);
  color: #F7FEE7;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.15rem;
  font-weight: 800;
  letter-spacing: 0.03em;
  cursor: pointer;
}

.virus__roll:hover:not(:disabled) { background: linear-gradient(180deg, #A3E635, #65A30D); }
.virus__roll:disabled { border-color: rgba(148, 163, 184, 0.25); background: rgba(148, 163, 184, 0.08); color: #94A3B8; cursor: not-allowed; }

.virus__done { margin: 8px 0 0; color: #D9F99D; font-size: 0.88rem; }
</style>
