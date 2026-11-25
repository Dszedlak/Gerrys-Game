<template>
  <!-- Until the first board update arrives, don't guess (it used to flash the board) -->
  <div v-if="phase === 'loading'" class="board-view board-view--loading" aria-busy="true">
    <div class="board-view__joining">Joining the room…</div>
  </div>

  <!-- Before the game: the waiting lobby -->
  <div v-else-if="phase === 'lobby'" class="board-view board-view--lobby">
    <BoardLobby
      :board="board"
      :state="boardState"
      :players="ledgerPlayers"
      :myUserId="currentUserId"
      :hostId="hostId"
      :isAdmin="isAdmin"
      :roomName="roomName"
      :versionName="boardState?.game_version_name || ''"
    />
  </div>

  <div v-else class="board-view">
    <PlayerLedger :players="ledgerPlayers" />

    <div class="board-view__main">
      <div class="board-view__stage">
        <div class="board-view__fit">
          <GameBoard
            :state="boardState"
            :players="ledgerPlayers"
            :myUserId="currentUserId"
            :isAdmin="isAdmin"
            :doctorInPlay="isDoctorInPlay"
            :jailFeeHours="jailFee"
            :serverOffsetMs="serverOffsetMs"
            :canRoll="canRoll"
            :canBuyCollectable="canBuyCollectable"
            :collectablePrice="collectablePrice"
            @roll="onDieClick"
            @open-collectable-deck="deckMenu = 'collectable'"
            @open-card="openCard"
            @open-discard="openDiscard('collectable')"
            @open-scenario-deck="deckMenu = 'scenario'"
            @move-token="({ userId, tile }) => board.moveToken(userId, tile)"
            @landed="(id) => { landedRollId = id }"
          />
        </div>

        <!-- Your tile's actions, over the board (minimise it to see the board) -->
        <ActionPopup
          :open="actionOpen && !revealShowing && !eventShowing && !moving"
          :minimised="actionMinimised"
          :board="board"
          :state="boardState"
          :playersById="playersById"
          :myUserId="currentUserId"
          :doctorInPlay="isDoctorInPlay"
          :priceMultiplier="purchaseMultiplier(governmentName)"
          :governmentName="governmentName"
          @minimise="actionMinimised = true"
          @restore="actionMinimised = false"
          @rolled="onActionRolled"
          @open-card="openCard"
          @open-discard="openDiscard('collectable')"
          @set-approval="(s) => $emit('set-approval', s)"
        />

        <!-- Ending your turn with too many cards -->
        <HandLimitModal
          :open="limitOpen"
          :board="board"
          :hand="hand"
          :handLimit="maxCollectables"
          :others="ledgerPlayers.filter(p => p.user_id !== currentUserId)"
          @close="limitOpen = false"
        />

        <!-- The discard piles, face up -->
        <DiscardPile
          :open="discardOpen"
          :board="board"
          :discards="boardState?.discards || {}"
          :myPicks="myPicks"
          :canBuy="canBuyAtMarket"
          :isAdmin="isAdmin"
          :players="ledgerPlayers"
          :initialTab="discardTab"
          @close="discardOpen = false"
        />

        <!-- Clicking a deck: draw/buy, shuffle, the discard pile -->
        <DeckMenu
          :open="Boolean(deckMenu)"
          :deck="deckMenu || 'scenario'"
          :board="board"
          :state="boardState"
          :playersById="playersById"
          :myUserId="currentUserId"
          :isAdmin="isAdmin"
          :canBuy="canBuyCollectable"
          :unitMinutes="60 * purchaseMultiplier(governmentName)"
          @close="deckMenu = null"
          @show-discards="openDiscard(deckMenu); deckMenu = null"
          @show-event="deckMenu = null; scenarioRef?.open()"
        />

        <!-- A scenario card in play, for the whole table -->
        <ScenarioEvent
          ref="scenarioRef"
          :event="boardState?.event || null"
          :lastRoll="boardState?.last_roll"
          :moving="moving"
          :board="board"
          :playersById="playersById"
          :myUserId="currentUserId"
          :isAdmin="isAdmin"
          :hand="hand"
          @visible="(v) => { eventShowing = v }"
          @pick-job="openJobPrompt"
        />

        <!-- Cards drawn/played, shown to everyone over the board -->
        <CardReveal
          ref="revealRef"
          :ready="Boolean(boardState)"
          :holdBack="moving"
          :reveal="boardState?.reveal"
          :pending="boardState?.pending"
          :lastRoll="boardState?.last_roll"
          :assignments="boardState?.assignments || []"
          :playersById="playersById"
          :myUserId="currentUserId"
          :board="board"
          :turnScenario="boardState?.turn?.scenario || null"
          :turnUserId="boardState?.turn?.user_id ?? null"
          :isAdmin="isAdmin"
          @visible="(v) => { revealShowing = v }"
        />

        <!-- The last player standing wins -->
        <WinnerModal
          :open="Boolean(winner) && winnerDismissed !== winner.user_id"
          :player="winner"
          :myUserId="currentUserId"
          :isAdmin="isAdmin"
          @close="winnerDismissed = winner?.user_id ?? null"
          @end-game="winnerDismissed = winner?.user_id ?? null; $emit('end-game')"
        />

        <!-- Peasant's Revolt: on the same tile as a government leader (any turn) -->
        <RevoltPrompt v-if="!moving" :board="board" :targets="revoltTargets" />

        <!-- "X's turn", whenever the turn passes on -->
        <TurnBanner
          :state="boardState"
          :phase="phase"
          :playersById="playersById"
          :myUserId="currentUserId"
        />

        <!-- Jobs (to change job, or an Executive's ability) and titles -->
        <JobsModal
          :open="Boolean(jobsMode)"
          :secondary="jobsMode === 'secondary'"
          :reference="boardState?.reference?.jobs || []"
          :jobs="jobs"
          :players="ledgerPlayers"
          :myUserId="currentUserId"
          :secondaryJobs="boardState?.secondary_jobs || {}"
          :allowed="jobsMode === 'card' ? (jobPrompt?.options || []).map(o => o.key) : null"
          :keepable="jobsMode === 'card' && Boolean(jobPrompt?.keep)"
          :cardName="jobsMode === 'card' ? jobPrompt?.card || '' : ''"
          :cardQuestion="jobsMode === 'card' ? jobPrompt?.question || '' : ''"
          @close="closeJobs"
          @keep="answerJob('keep')"
          @choose="onJobChosen"
          @choose-secondary="(name) => { board.chooseSecondaryJob(name); jobsMode = null }"
        />
        <TitlesModal
          :open="Boolean(titlesOpen)"
          :alert="titlesOpen === 'alert'"
          :titles="titleInfo.titles"
          :myTitle="me?.perk || null"
          :isMyTurn="myTurnNow"
          :isAdmin="isAdmin"
          :board="board"
          @close="closeTitles"
          @set-title="(v) => $emit('update-perk', v)"
        />

        <!-- Then everyone chooses a Tier 1 job -->
        <JobPickModal
          :state="boardState"
          :phase="phase"
          :jobs="jobs"
          :playersById="playersById"
          :myUserId="currentUserId"
          :isAdmin="isAdmin"
          :board="board"
        />

        <!-- Everyone rolls for the first turn, one at a time -->
        <InitiativeModal
          :state="boardState"
          :phase="phase"
          :playersById="playersById"
          :myUserId="currentUserId"
          :isAdmin="isAdmin"
          :board="board"
        />
      </div>

      <!-- One scrolling rail beside the board; on wide screens it dissolves
           into two columns, either side of the board. -->
      <div class="board-view__rail">
        <aside class="board-view__side">
          <MyPlayerCard
            :player="me"
            :participants="participants"
            :jobs="jobs"
            :clock="clock"
            :myUserId="currentUserId"
            :isDoctorInPlay="isDoctorInPlay"
            :secondaryJob="mySecondaryJob"
            :titleReady="titleInfo.ready && myTurnNow"
            @open-jobs="jobsMode = 'change'"
            @open-titles="titlesOpen = 'browse'"
            @adjust-clock="(n) => $emit('adjust-clock', n)"
            @update-job="(id) => $emit('update-job', id)"
            @update-perk="(v) => $emit('update-perk', v)"
            @bleed-changed="(d) => $emit('bleed-changed', d)"
            @heat-changed="(d) => $emit('heat-changed', d)"
            @set-approval="(s) => $emit('set-approval', s)"
          />

          <TurnPanel
            :priceMultiplier="purchaseMultiplier(governmentName)"
            :governmentName="governmentName"
            :board="board"
            :state="boardState"
            :playersById="playersById"
            :myUserId="currentUserId"
            :isAdmin="isAdmin"
            :incomeNet="myIncomeNet"
            :doctorInPlay="isDoctorInPlay"
            :jailFeeHours="jailFee"
            :serverOffsetMs="serverOffsetMs"
            :handSize="limitedHandSize"
            :handLimit="maxCollectables"
            :abilities="myAbilities"
            @get-out-of-jail="$emit('get-out-of-jail')"
            @set-approval="(s) => $emit('set-approval', s)"
            @open-card="openCard"
            @open-discard="openDiscard('collectable')"
            @over-limit="limitOpen = true"
            @open-actions="showActions"
          />
        </aside>

        <!-- Assignments, government, your collectables and the game log:
             left of the board on wide screens, under the turn panel otherwise. -->
        <aside class="board-view__left">
          <AssignmentBoard
            :board="board"
            :assignments="boardState?.assignments || []"
            :max="boardState?.max_assignments || 6"
            :playersById="playersById"
            :myUserId="currentUserId"
            :started="Boolean(boardState?.started)"
            :claimedThisTurn="claimedThisTurn"
            :bounty="boardState?.bounty || null"
          />

          <!-- Scenario cards still in play: debts, Income Tax, the Bounty Board -->
          <OngoingCards
            :board="board"
            :state="boardState"
            :playersById="playersById"
            :myUserId="currentUserId"
          />

          <section class="gov-card" :aria-label="`Government: ${governmentName}`">
            <button type="button" class="gov-card__head" :aria-expanded="!govCollapsed" @click="toggleGov">
              <span class="gov-card__chevron" :class="{ 'is-open': !govCollapsed }">▸</span>
              <img v-if="govCard.image" :src="govCard.image" alt="" class="gov-card__img" />
              <span v-else class="gov-card__icon">{{ govCard.icon }}</span>
              <span class="gov-card__title">
                <span class="gov-card__eyebrow">Government</span>
                <span class="gov-card__name">{{ governmentName }}</span>
              </span>
              <span v-if="govCollapsed && leaders.length" class="gov-card__count">
                {{ leaders.length }} {{ leaders.length === 1 ? 'leader' : 'leaders' }}
              </span>
            </button>
            <template v-if="!govCollapsed">
            <p v-if="govCard.summary" class="gov-card__text">{{ govCard.summary }}</p>
            <!-- Who governs -->
            <ul v-if="leaders.length" class="gov-card__members">
              <li v-for="l in leaders" :key="`${l.role}-${l.user_id}`" class="gov-card__member">
                <span class="gov-card__dot" :style="{ background: playersById[l.user_id]?.color }" />
                <span class="gov-card__who">{{ l.user_id === currentUserId ? 'You' : l.username }}</span>
                <span class="gov-card__role">{{ l.role }}</span>
              </li>
            </ul>
            <p v-else-if="governmentName !== 'Democracy'" class="gov-card__none">No leaders chosen yet.</p>
            </template>
          </section>

          <OppressionBoard
            :board="board"
            :oppressions="boardState?.oppressions || []"
            :max="boardState?.max_oppressions || 4"
            :uses="boardState?.oppression_uses || null"
            :turnSeq="boardState?.turn_seq ?? null"
            :governmentType="governmentName"
            :leaders="leaderInfo"
            :stateEnemies="stateEnemies"
            :playersById="playersById"
            :myUserId="currentUserId"
            :isMyTurn="Boolean(boardState?.started) && boardState?.turn?.user_id === currentUserId"
            :isAdmin="isAdmin"
          />

          <!-- Your collectables, under the government -->
          <HandPanel
            :board="board"
            :hand="hand"
            :equipped="myEquipped"
            :slips="mySlips"
            :playersById="playersById"
            :myUserId="currentUserId"
            :handLimit="maxCollectables"
            :maxEquipped="boardState?.max_equipped || 2"
            :started="Boolean(boardState?.started)"
            :discardCount="boardState?.decks?.collectable?.discard || 0"
            :picks="myPicks"
            :state="boardState"
            @open-discard="openDiscard('collectable')"
          />

          <BoardLog class="board-view__log" :log="boardState?.log || []" :playersById="playersById" />
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import GameBoard from '@/components/board/GameBoard.vue'
import PlayerLedger from '@/components/board/PlayerLedger.vue'
import TurnPanel from '@/components/board/TurnPanel.vue'
import BoardLog from '@/components/board/BoardLog.vue'
import CardReveal from '@/components/board/CardReveal.vue'
import HandPanel from '@/components/board/HandPanel.vue'
import AssignmentBoard from '@/components/board/AssignmentBoard.vue'
import MyPlayerCard from '@/components/board/MyPlayerCard.vue'
import DiscardPile from '@/components/board/DiscardPile.vue'
import BoardLobby from '@/components/board/BoardLobby.vue'
import HandLimitModal from '@/components/board/HandLimitModal.vue'
import OppressionBoard from '@/components/board/OppressionBoard.vue'
import InitiativeModal from '@/components/board/InitiativeModal.vue'
import JobPickModal from '@/components/board/JobPickModal.vue'
import JobsModal from '@/components/board/JobsModal.vue'
import TitlesModal from '@/components/board/TitlesModal.vue'
import ActionPopup from '@/components/board/ActionPopup.vue'
import TurnBanner from '@/components/board/TurnBanner.vue'
import RevoltPrompt from '@/components/board/RevoltPrompt.vue'
import WinnerModal from '@/components/board/WinnerModal.vue'
import DeckMenu from '@/components/board/DeckMenu.vue'
import ScenarioEvent from '@/components/board/ScenarioEvent.vue'
import OngoingCards from '@/components/board/OngoingCards.vue'
import {
  pawnColor,
  clockToMinutes,
  governmentCard,
  jailFeeHours,
  heatThreshold,
  HAND_LIMIT_DECKS,
  ACTION_TILE_KINDS,
  purchaseMultiplier,
  moveDurationMs,
  formatPrice
} from '@/components/board/boardLayout'
import { useIncome } from '@/composables/useIncome'
import { useGovernment } from '@/composables/useGovernment'
import { useCollapsed } from '@/composables/useCollapsed'

const props = defineProps({
  // Actions from useBoard()
  board: { type: Object, required: true },
  // useBoard().state, unwrapped
  boardState: { type: Object, default: null },
  // My collectables (useBoard().hand, unwrapped)
  hand: { type: Array, default: () => [] },
  serverOffsetMs: { type: Number, default: 0 },
  // Every participant, alive or not
  participants: { type: Array, default: () => [] },
  currentUserId: { type: [Number, String], default: null },
  isAdmin: { type: Boolean, default: false },
  jobs: { type: Array, default: () => [] },
  government: { type: Object, default: null },
  governmentIcon: { type: Function, default: () => null },
  clock: { type: String, default: '' },
  maxCollectables: { type: Number, default: 5 },
  isDoctorInPlay: { type: Boolean, default: false },
  // The room's creator (room id = creator's user id), and the room's name, for the lobby
  hostId: { type: [Number, String], default: null },
  roomName: { type: String, default: '' },
  // Republic: enemies of the state (oppressions can only target them)
  stateEnemies: { type: Array, default: () => [] }
})

const emit = defineEmits([
  'switch-view',
  'adjust-clock',
  'update-job',
  'update-perk',
  'bleed-changed',
  'heat-changed',
  'get-out-of-jail',
  'set-approval',
  'end-game'
])

const { computeIncomeBreakdown } = useIncome()
const { normalizeGovernment } = useGovernment()

const isAlive = (p) => String(p?.clock || '').trim() !== '00•00•00'
const alivePlayers = computed(() => props.participants.filter(isAlive))

const governmentName = computed(() => props.government?.type || 'Democracy')
// Collapsed by default, like the assignments and oppressions
const { collapsed: govCollapsed, toggle: toggleGov } = useCollapsed('government.v2', true)
const govCard = computed(() => governmentCard(governmentName.value))
const jailFee = computed(() => jailFeeHours(governmentName.value, roleOf(Number(props.currentUserId)) === 'Dictator'))

const ROLE_LABELS = {
  dictator: 'Dictator',
  head_of_state: 'Head of State',
  advisor: 'Advisor',
  politburo: 'Politburo'
}

function roleOf(uid) {
  const g = normalizeGovernment(props.government)
  if (g.dictator === uid) return 'Dictator'
  if (g.head_of_state === uid) return 'Head of State'
  if (g.advisors.has(uid)) return 'Advisor'
  if (g.politburo.has(uid)) return 'Politburo'
  return null
}

// Who leads the government, for who can use oppressions
const leaderInfo = computed(() => normalizeGovernment(props.government))

const leaders = computed(() =>
  (props.government?.members || []).map(m => ({
    user_id: m.user_id,
    username: m.username,
    role: ROLE_LABELS[m.role] || m.role
  }))
)

/** The default avatar is a generic placeholder; show initials instead. */
function usablePhoto(url) {
  if (!url || /ui-avatars\.com\/api\/\?name=User$/.test(url)) return null
  return url
}

/**
 * One entry per player, in turn order once the game has started, carrying
 * everything the ledger, the board and the turn panel draw.
 */
const ledgerPlayers = computed(() => {
  const s = props.boardState
  const order = s?.started ? s.turn_order || [] : []
  const rank = (uid) => {
    const i = order.indexOf(uid)
    return i === -1 ? Number.MAX_SAFE_INTEGER : i
  }
  const jobsByName = Object.fromEntries(props.jobs.map(j => [j.name, j]))

  return [...props.participants]
    .sort((a, b) => rank(a.user_id) - rank(b.user_id) || a.user_id - b.user_id)
    .map(p => {
      const income = computeIncomeBreakdown(p, {
        jobs: props.jobs,
        government: props.government,
        allPlayers: alivePlayers.value
      })
      const job = jobsByName[p.job_name]
      const i = order.indexOf(p.user_id)
      // A card debt (RNLI) is repaid from each turn's income
      const debt = s?.debts?.[String(p.user_id)] || null
      const repay = debt ? Math.min(debt.plan || 60, debt.minutes) : 0
      const incomeLines = [
        ...income.lines,
        ...(repay ? [{ label: `${debt.title} repayment`, minutes: -repay }] : [])
      ]
      return {
        user_id: p.user_id,
        username: p.username,
        color: pawnColor(s?.colors?.[String(p.user_id)]),
        colorName: s?.colors?.[String(p.user_id)] || null,
        piece: 'pawn',
        profilePic: usablePhoto(p.profile_pic),
        clock: p.clock,
        clockMinutes: clockToMinutes(p.clock),
        alive: isAlive(p),
        jailed: Boolean(p.is_in_jail),
        incomeNet: income.net - repay,
        incomeLines,
        debt: debt ? { title: debt.title, minutes: debt.minutes, repay } : null,
        bleed: p.bleed || 0,
        heat: p.heat || 0,
        heatMax: heatThreshold(p.perk),
        jobName: p.job_name && p.job_name !== '-' ? p.job_name : 'Unemployed',
        jobTier: job?.tier || 0,
        jobFaction: job?.type || null,
        perk: p.perk || null,
        approval: p.approval_status || null,
        govIcon: props.governmentIcon(p),
        govRole: roleOf(Number(p.user_id)),
        isCurrent: Boolean(s?.started) && s?.turn?.user_id === p.user_id,
        isMe: p.user_id === props.currentUserId,
        turnNo: i === -1 ? null : i + 1,
        handCount: s?.hand_counts?.[String(p.user_id)] || 0,
        // Assignment slips aimed at this player
        targetedBy: (s?.assignments || []).filter(a => a.target === p.user_id).length,
        slipCount: s?.slips?.[String(p.user_id)]?.length || 0,
        equipped: s?.equipped?.[String(p.user_id)] || []
      }
    })
})

const playersById = computed(() => Object.fromEntries(ledgerPlayers.value.map(p => [p.user_id, p])))

// The last player standing (the server marks it in state.finished; clocks can also show it first)
const winnerDismissed = ref(null)
const winner = computed(() => {
  const s = props.boardState
  if (!s?.started) return null
  if (s.finished?.winner != null) return playersById.value[s.finished.winner] || null
  const players = ledgerPlayers.value
  const alive = players.filter(p => p.alive)
  return players.length >= 2 && alive.length === 1 ? alive[0] : null
})

// Peasant's Revolt: a peasant on the same tile as a government leader (once per leader per turn)
const REVOLT_LEADERS = ['Dictator', 'Head of State', 'Politburo']
const revoltTargets = computed(() => {
  const s = props.boardState
  if (!s?.started || governmentName.value === 'Democracy') return []
  const mine = ledgerPlayers.value.find(p => p.user_id === props.currentUserId)
  if (!mine || !mine.alive || mine.jailed || mine.govRole) return []
  const pos = s.positions?.[String(props.currentUserId)]
  if (pos === undefined || pos === null || pos === s.jail) return []
  const used = s.revolts?.turn_seq === s.turn_seq ? (s.revolts.pairs || []) : []
  return ledgerPlayers.value.filter(p => REVOLT_LEADERS.includes(p.govRole) && p.alive && !p.jailed &&
    s.positions?.[String(p.user_id)] === pos && !used.includes(`${props.currentUserId}:${p.user_id}`))
})
const me = computed(() => playersById.value[props.currentUserId] || null)
const myIncomeNet = computed(() => me.value?.incomeNet || 0)
const myEquipped = computed(() => me.value?.equipped || [])
const mySlips = computed(() => props.boardState?.slips?.[String(props.currentUserId)] || [])

const claimedThisTurn = computed(() => {
  const s = props.boardState
  const mine = s?.claims?.[String(props.currentUserId)]
  return mine != null && mine === s?.turn_seq
})

// Click the die on your turn to roll it
// lobby -> initiative (everyone rolls for the first turn) -> playing
const phase = computed(() => {
  const s = props.boardState
  if (!s) return 'loading'
  return s.phase || (s.started ? 'playing' : 'lobby')
})

// Still to roll for the first turn
const canRollInitiative = computed(() => {
  const init = props.boardState?.initiative
  return phase.value === 'initiative' && Boolean(init) &&
    (init.contenders || []).includes(props.currentUserId) &&
    !(String(props.currentUserId) in (init.rolls || {}))
})

// Click the die on your turn (or when it's your go to roll for the first turn)
const canRoll = computed(() => {
  const s = props.boardState
  if (canRollInitiative.value) return true
  return Boolean(s?.started) && s?.turn?.user_id === props.currentUserId && !s?.turn?.rolled &&
    !me.value?.jailed
})

function onDieClick() {
  if (canRollInitiative.value) props.board.initiativeRoll()
  else props.board.roll()
}

// Discard pile viewer, and the hand-limit prompt at the end of a turn
const discardOpen = ref(false)
const discardTab = ref('collectable')
// Which deck's menu is open ('scenario' / 'collectable'), and the scenario card in play
const deckMenu = ref(null)
const scenarioRef = ref(null)
const eventShowing = ref(false)
function openDiscard(tab) {
  discardTab.value = tab
  discardOpen.value = true
}
const limitOpen = ref(false)
const myPicks = computed(() => props.boardState?.discard_picks?.[String(props.currentUserId)] || 0)
const canBuyAtMarket = computed(() => {
  const s = props.boardState
  const pos = s?.positions?.[String(props.currentUserId)]
  return Boolean(s?.started) && s?.turn?.user_id === props.currentUserId && Boolean(s?.turn?.rolled || s?.turn?.landed) &&
    s?.tiles?.[pos]?.kind === 'black_market' && !(s?.turn?.purchases?.black_market >= 1)
})
// Every card in your hand counts towards the hand limit
const limitedHandSize = computed(() => props.hand.filter(c => HAND_LIMIT_DECKS.includes(c.deck || 'collectable')).length)

const revealRef = ref(null)
function openCard() {
  // The scenario card in play (or just played) first; otherwise the last card revealed
  if (!scenarioRef.value?.open()) revealRef.value?.open()
}

// --- Step 3 as a pop-up --------------------------------------------------------
const myTurnNow = computed(() => {
  const s = props.boardState
  return phase.value === 'playing' && Boolean(s?.started) && s?.turn?.user_id === props.currentUserId
})
// --- Jobs, titles and abilities -------------------------------------------------
const jobsMode = ref(null)     // 'change' | 'secondary' | null
const titlesOpen = ref(null)   // 'browse' | 'alert' | null
const mySecondaryJob = computed(() => {
  const sec = props.boardState?.secondary_jobs?.[String(props.currentUserId)]
  return sec && me.value?.perk === 'Executive' ? sec : null
})

// My Tier 3 abilities, for the turn panel
const myAbilities = computed(() => {
  const ref = props.boardState?.reference?.jobs || []
  const used = props.boardState?.turn?.abilities_used || {}
  // A new Tier 3 job's ability works from the next turn (see board_jobs.ability_ready)
  const since = props.boardState?.job_since?.[String(props.currentUserId)] || {}
  const seq = props.boardState?.turn_seq
  const out = []
  const add = (slot, job) => {
    const info = ref.find(j => j.name === job)
    const s = since[slot] ?? -1
    out.push({ slot, job, text: info?.ability || '', automatic: info?.automatic || null, used: Boolean(used[slot]),
      notYet: s >= 0 && s === seq })
  }
  if (me.value?.jobTier === 3) add('primary', me.value.jobName)
  if (mySecondaryJob.value) add('secondary', mySecondaryJob.value)
  return out
})

// Titles: what each needs, and whether I can take the next one
const TITLE_ORDER = ['Manager', 'Senior', 'Executive']
const TITLE_QUANTITY = { Manager: 6, Senior: 4, Executive: 2 }
const titleInfo = computed(() => {
  const m = me.value
  const ref = props.boardState?.reference?.titles || []
  const next = !m || m.perk === 'Executive' ? null : TITLE_ORDER[TITLE_ORDER.indexOf(m.perk) + 1] || 'Manager'
  const hasPromotion = props.hand.some(c => c.deck === 'promotion')
  const titles = TITLE_ORDER.map(name => {
    const info = ref.find(t => t.name === name) || { name, pay: 0, abilities: '' }
    const quantity = info.quantity || TITLE_QUANTITY[name]
    const held = ledgerPlayers.value.filter(p => p.perk === name && p.user_id !== props.currentUserId).length
    const checks = [{ ok: m?.jobTier === 3, text: 'Hold a Tier 3 job' }]
    if (name === 'Manager') checks.push({ ok: mySlips.value.length > 0, text: 'A completed assignment slip (traded in)' })
    if (name === 'Senior') {
      checks.push({ ok: hasPromotion, text: 'A Promotion card in your hand (used)' })
      checks.push({ ok: !m?.bleed, text: 'No bleeding' })
    }
    if (name === 'Executive') {
      checks.push({ ok: !m?.bleed, text: 'No bleeding' })
      checks.push({ ok: !m?.heat, text: 'No heat' })
      checks.push({ ok: myEquipped.value.length > 0, text: 'At least one equipped collectable' })
    }
    checks.push({ ok: held < quantity, text: held < quantity ? 'A title is free' : 'All taken' })
    return {
      ...info, name, quantity, left: Math.max(0, quantity - held), checks,
      mine: m?.perk === name, isNext: name === next, ready: checks.every(c => c.ok)
    }
  })
  return { titles, next, ready: Boolean(titles.find(t => t.isNext)?.ready) }
})

// "New title available" on my turn, once per turn
let titleAlertSeq = null
watch(() => [myTurnNow.value, titleInfo.value.ready, props.boardState?.turn_seq], ([mine, ready, seq]) => {
  if (mine && ready && seq !== titleAlertSeq && !titlesOpen.value) {
    titleAlertSeq = seq
    titlesOpen.value = 'alert'
  }
})
function closeTitles() { titlesOpen.value = null }

// A new Executive chooses their executive ability (asked once per turn until they do)
let secondaryAskSeq = null
watch(() => [me.value?.perk, mySecondaryJob.value, myTurnNow.value, props.boardState?.turn_seq], ([perk, sec, mine, seq]) => {
  if (perk === 'Executive' && !sec && mine && seq !== secondaryAskSeq && !jobsMode.value) {
    secondaryAskSeq = seq
    jobsMode.value = 'secondary'
  }
})
function closeJobs() { jobsMode.value = null }

// A card asking for a job (Promotion, Careers Advisor, Job Opportunity) uses the jobs list
const jobPrompt = ref(null)
function openJobPrompt(prompt) {
  jobPrompt.value = prompt
  jobsMode.value = 'card'
}
function answerJob(value) {
  if (jobPrompt.value) props.board.eventAnswer(jobPrompt.value.id, String(value))
  jobsMode.value = null
}
function onJobChosen(id) {
  if (jobsMode.value === 'card') answerJob(id)
  else {
    emit('update-job', id)
    jobsMode.value = null
  }
}
// Open it straight away for the player whose card it is
watch(() => props.boardState?.event?.prompt, (p) => {
  if (p?.kind === 'job' && p.user_id === props.currentUserId && jobPrompt.value?.id !== p.id) openJobPrompt(p)
  if (jobsMode.value === 'card' && (!p || p.kind !== 'job')) jobsMode.value = null
})

const myTileNow = computed(() => {
  const s = props.boardState
  const pos = s?.positions?.[String(props.currentUserId)]
  return pos === undefined || pos === null || pos < 0 ? null : s?.tiles?.[pos] || null
})
const myTileHasActions = computed(() => {
  const s = props.boardState
  const pending = s?.pending && s.pending.user_id === props.currentUserId
  if (!myTurnNow.value || !me.value?.alive || me.value?.jailed) return false
  // Remote Access works from anywhere, before or after rolling
  if (s?.turn?.remote_senate) return true
  return Boolean((s?.turn?.rolled || s?.turn?.landed) && (ACTION_TILE_KINDS.includes(myTileNow.value?.kind) || pending))
})

// A pawn is still hopping to its tile: its pop-ups wait until it lands
const MOVE_KINDS = ['move', 'card_move']
const landedRollId = ref(null)
let landFallback = null
watch(() => props.boardState?.last_roll?.id, () => {
  clearTimeout(landFallback)
  const r = props.boardState?.last_roll
  // In case the board never reports it (tab in the background...), stop waiting eventually
  if (r && MOVE_KINDS.includes(r.kind)) landFallback = setTimeout(() => { landedRollId.value = r.id }, moveDurationMs(r) + 2500)
})
const moving = computed(() => {
  const r = props.boardState?.last_roll
  return Boolean(r && MOVE_KINDS.includes(r.kind) && landedRollId.value !== r.id)
})

const actionOpen = ref(false)
const actionMinimised = ref(false)
// The card pop-up goes first; the actions wait until it's closed
const revealShowing = ref(false)
let actionTimer = null

function showActions() {
  clearTimeout(actionTimer)
  actionOpen.value = true
  actionMinimised.value = false
}

// Pops up once the pawn has finished moving after your roll
watch(() => [props.boardState?.turn_seq, Boolean(props.boardState?.turn?.rolled || props.boardState?.turn?.landed), myTileHasActions.value,
  myTileNow.value?.index, Boolean(props.boardState?.turn?.remote_senate)],
  ([seq, rolled, has, tile, remote], old) => {
    const [oldSeq, oldRolled, , oldTile, oldRemote] = old || []
    if (!has) {
      clearTimeout(actionTimer)
      actionOpen.value = false
      return
    }
    // Just rolled onto it, moved there by a card, or got Remote Access
    // (on joining mid-turn, show it straight away)
    const justRolled = (rolled && (!oldRolled || seq !== oldSeq || (old && tile !== oldTile))) || (remote && !oldRemote)
    if (!justRolled && actionOpen.value) return
    if (!old) return showActions()
    if (!justRolled) return
    clearTimeout(actionTimer)
    actionTimer = setTimeout(showActions, moveDurationMs(props.boardState?.last_roll) + 400)
  }, { immediate: true })

onBeforeUnmount(() => {
  clearTimeout(actionTimer)
  clearTimeout(landFallback)
})

// Rolled from the pop-up (Time Virus): get out of the way so the die on the board
// can be seen. Tile 6 has nothing else to do; the Senate's Time Virus tile does.
function onActionRolled(kind) {
  if (kind === 'time_virus') actionOpen.value = false
  else actionMinimised.value = true
}

// --- Clicking the piles --------------------------------------------------------
// No limit on collectables: the hand limit is checked when the turn ends
const canBuyCollectable = computed(() => {
  const t = props.boardState?.turn
  return myTurnNow.value && Boolean(t?.rolled || t?.landed) && myTileNow.value?.kind === 'collectables' && !me.value?.jailed
})
const collectablePrice = computed(() => formatPrice(60 * purchaseMultiplier(governmentName.value)))
</script>

<style scoped>
.board-view--lobby {
  overflow-y: auto;
}

.board-view--loading {
  display: grid;
  place-items: center;
}

.board-view__joining {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.3rem;
  letter-spacing: 0.08em;
  color: #64748B;
  animation: joining 1.4s ease-in-out infinite;
}

@keyframes joining { 50% { opacity: 0.4; } }

.board-view {
  /* Fill the screen under the 64px navbar (+1px border) */
  height: calc(100vh - 65px);
  min-height: 640px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px 16px 16px;
  box-sizing: border-box;
  background:
    radial-gradient(1200px 700px at 38% 55%, rgba(34, 211, 238, 0.06), transparent 70%),
    radial-gradient(900px 600px at 80% 0%, rgba(234, 179, 8, 0.05), transparent 70%),
    #0B0F19;
}

.board-view__main {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  grid-template-areas: "stage rail";
  gap: 12px 16px;
}

.board-view__rail {
  grid-area: rail;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  scrollbar-width: thin;
  padding-right: 2px;
}

.board-view__rail .board-view__side,
.board-view__rail .board-view__left {
  overflow: visible;
  flex: 0 0 auto;
}

@media (min-width: 1500px) {
  .board-view__main {
    /* Same width either side, so the board stays in the middle of the screen */
    --side: clamp(380px, 24vw, 480px);
    grid-template-columns: var(--side) minmax(0, 1fr) var(--side);
    grid-template-areas: "left stage side";
  }

  .board-view__rail { display: contents; }

  .board-view__rail .board-view__side,
  .board-view__rail .board-view__left {
    overflow-y: auto;
  }

  .board-view__rail .board-view__left .board-view__log {
    flex: 1 1 200px;
  }
}

/* The board is as big as the space allows while staying square */
.board-view__stage {
  position: relative;
  grid-area: stage;
  min-width: 0;
  min-height: 0;
  container-type: size;
  display: grid;
  place-items: center;
}

.board-view__fit {
  width: min(100cqw, 100cqh);
}

/* Shorter screens (a bookmarks bar, a laptop): less padding so everything fits */
@media (max-height: 980px) {
  .board-view { gap: 8px; padding: 8px 14px 10px; }
  .board-view__main { gap: 8px 14px; }
  .board-view__side, .board-view__left { gap: 8px; }
}

.board-view__side,
.board-view__left {
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  scrollbar-width: thin;
  padding-right: 2px;
}

.board-view__side { grid-area: side; }
.board-view__left { grid-area: left; }

.board-view__log {
  flex: 1 1 200px;
  min-height: 180px;
}

/* Government card ------------------------------------------------------- */
.gov-card {
  padding: 10px 12px;
  border-radius: 12px;
  background: linear-gradient(180deg, #1A1F2E, #121726);
  border: 1px solid rgba(59, 130, 246, 0.35);
  color: #E2E8F0;
  text-align: left;
}

.gov-card__head {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  margin: 0;
  padding: 0;
  border: 0;
  background: none;
  font: inherit;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.gov-card__chevron {
  display: inline-block;
  width: 12px;
  color: #93C5FD;
  transition: transform 0.15s ease;
}

.gov-card__chevron.is-open { transform: rotate(90deg); }

.gov-card__count { font-size: 0.82rem; color: #94A3B8; white-space: nowrap; }

.gov-card__img {
  width: 28px;
  height: 28px;
  object-fit: contain;
}

.gov-card__icon { font-size: 1.4rem; }

.gov-card__title {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.gov-card__eyebrow {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 0.85rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #93C5FD;
}

.gov-card__name {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.3rem;
  font-weight: 800;
  line-height: 1;
  color: #F8FAFC;
}

.gov-card__text {
  margin: 8px 0 0;
  font-size: 0.8rem;
  line-height: 1.45;
  color: #CBD5E1;
}

.gov-card__members {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 8px 0 0;
  padding: 0;
  list-style: none;
}

.gov-card__member {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px 3px 6px;
  border-radius: 999px;
  background: rgba(59, 130, 246, 0.14);
  border: 1px solid rgba(59, 130, 246, 0.4);
  font-size: 0.85rem;
}

.gov-card__who { font-weight: 700; color: #F8FAFC; }

.gov-card__role {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 0.8rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #93C5FD;
}

.gov-card__none { margin: 6px 0 0; font-size: 0.8rem; color: #64748B; }

.gov-card__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.25);
}

/* Narrow screens: stack the board above the side panel ------------------ */
@media (max-width: 1100px) {
  .board-view {
    height: auto;
    min-height: 0;
  }

  .board-view__main {
    grid-template-columns: minmax(0, 1fr);
    grid-template-areas: "stage" "rail";
  }

  .board-view__rail { overflow: visible; }

  .board-view__stage {
    container-type: inline-size;
  }

  .board-view__fit {
    width: min(100%, 760px);
  }

  .board-view__side,
  .board-view__left {
    overflow: visible;
  }
}
</style>
