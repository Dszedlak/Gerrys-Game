<template>
  <!-- One grid for the whole HUD, so the income block shares the clock's
       column and always spans exactly the clock's width. -->
  <div class="room-hud">
    <!-- Row 1: the clock, flanked by the controls that change it -->
    <div class="room-hud__adjuster-group room-hud__area--minus">
      <button
        v-for="n in [-60, -30, -20, -10]"
        :key="n"
        type="button"
        class="room-hud__adjust room-hud__adjust--negative"
        @click="$emit('adjust-clock', n)"
      >
        {{ n === -60 ? '-1h' : n }}
      </button>
    </div>

    <div class="room-hud__clock room-hud__area--clock" :title="`Your time bank: ${clock}`">
      {{ clock }}
    </div>

    <div class="room-hud__adjuster-group room-hud__area--plus">
      <button
        v-for="n in [10, 20, 30, 60]"
        :key="n"
        type="button"
        class="room-hud__adjust room-hud__adjust--positive"
        @click="$emit('adjust-clock', n)"
      >
        {{ n === 60 ? '+1h' : `+${n}` }}
      </button>
    </div>

    <!-- Row 2: Jail / Black Market on the left, income under the clock,
         government / collectables on the right. -->
    <div class="room-hud__stack room-hud__area--left">
      <button
        type="button"
        class="room-hud__action-btn room-hud__action-btn--jail"
        :disabled="isLoadingJail"
        @click="$emit('get-out-of-jail')"
        :title="`Pay the jail fee of ${jailFeeHours} hours`"
      >
        <span class="room-hud__chip-icon">🔓</span>
        {{ isLoadingJail ? 'Paying…' : `Jail: Buy Freedom (${jailFeeHours})` }}
      </button>

      <button
        type="button"
        class="room-hud__action-btn room-hud__action-btn--market"
        :disabled="isLoadingBlackMarket"
        @click="$emit('buy-black-market')"
        title="Buy a collectable from the Black Market (2.5 hours)"
      >
        <span class="room-hud__chip-icon">🕶️</span>
        {{ isLoadingBlackMarket ? 'Buying…' : 'Black Market (2.5)' }}
      </button>
    </div>

    <div class="room-hud__income-pair room-hud__area--income">
      <button
        type="button"
        class="room-hud__collect"
        :disabled="isLoadingPay"
        @click="$emit('get-paid')"
        :title="`Collect your income for this turn (${incomeLabel})`"
        aria-label="Collect income"
      >
        <span class="room-hud__collect-glyph">{{ isLoadingPay ? '…' : '+' }}</span>
      </button>
      <RoomIncomeBar
        class="room-hud__income"
        :player="player"
        :jobs="jobs"
        :government="government"
        :allPlayers="allPlayers"
      />
    </div>

    <div class="room-hud__stack room-hud__area--right">
      <div class="room-hud__chip">
        <span class="room-hud__chip-icon">🏛</span>
        <span class="room-hud__chip-label">Government: {{ governmentName }}</span>
      </div>

      <div class="room-hud__chip">
        <span class="room-hud__chip-icon">🎴</span>
        <span class="room-hud__chip-label">Max {{ maxCollectables }} collectables</span>
      </div>
    </div>

    <!-- Row 3: notices span the whole HUD underneath -->
    <div v-if="isDoctorInPlay" class="room-hud__notices room-hud__area--notices">
      <div
        class="room-hud__chip room-hud__chip--warning"
        title="A Doctor is in play — Hospital items cost 60 minutes each (doubled). This applies to the Doctor too."
      >
        <span class="room-hud__chip-icon">🏥</span>
        <span class="room-hud__chip-label">Hospital ×2 (Doctor in play)</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import RoomIncomeBar from '@/components/room/RoomIncomeBar.vue'
import { useIncome } from '@/composables/useIncome'

const props = defineProps({
  clock: { type: String, default: '00•00•00' },
  maxCollectables: { type: Number, default: 5 },
  governmentName: { type: String, default: '—' },
  isDoctorInPlay: { type: Boolean, default: false },
  isLoadingPay: { type: Boolean, default: false },
  isLoadingJail: { type: Boolean, default: false },
  isLoadingBlackMarket: { type: Boolean, default: false },
  // Income breakdown inputs
  player: { type: Object, default: null },
  jobs: { type: Array, default: () => [] },
  government: { type: Object, default: null },
  allPlayers: { type: Array, default: () => [] }
})

// Leave Room / Admin Controls now live in the navbar (see useRoomChrome.js)
defineEmits([
  'adjust-clock',
  'get-paid',
  'get-out-of-jail',
  'buy-black-market'
])

const { computeIncomeBreakdown, formatMinutes } = useIncome()

// Mirrors getOutOfJail in sockets.py: 480 minutes, or 720 under Dictatorship
const jailFeeHours = computed(() =>
  (props.governmentName === 'Dictatorship' ? 12 : 8).toFixed(1)
)

const incomeLabel = computed(() => {
  const { net } = computeIncomeBreakdown(props.player, {
    jobs: props.jobs,
    government: props.government,
    allPlayers: props.allPlayers
  })
  return formatMinutes(net)
})
</script>

<style scoped>
/* The whole HUD is one grid. The clock and the income block share the
   centre column, so the income block always matches the clock's width;
   the side columns take what is left and hug the centre. */
.room-hud {
  --hud-income-height: 72px;

  display: grid;
  grid-template-columns: 1fr auto 1fr;
  grid-template-areas:
    "minus   clock  plus"
    "left    income right"
    "notices notices notices";
  column-gap: 16px;
  row-gap: 12px;
  align-items: center;
  padding: 14px 16px 12px 16px;
  border-bottom: 1px solid rgba(34, 211, 238, 0.2);
}

.room-hud__area--minus   { grid-area: minus;   justify-self: end; }
.room-hud__area--clock   { grid-area: clock; }
.room-hud__area--plus    { grid-area: plus;    justify-self: start; }
.room-hud__area--left    { grid-area: left;    justify-self: end; }
.room-hud__area--income  { grid-area: income; justify-self: center; align-self: stretch; }
.room-hud__area--right   { grid-area: right;   justify-self: start; }
.room-hud__area--notices { grid-area: notices; }

/* ---------- Row 1: clock centred, adjusters flanking it ---------- */
.room-hud__clock {
  font-family: 'Barlow Condensed', monospace;
  font-size: 3.9em;
  font-weight: 700;
  line-height: 1.1;
  color: #00ff00;
  background: radial-gradient(ellipse at center, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.9) 100%);
  border: 3px solid #000;
  border-radius: 14px;
  padding: 8px 34px;
  letter-spacing: 8px;
  white-space: nowrap;
  text-align: center;
}

.room-hud__adjuster-group {
  display: flex;
  align-items: center;
  gap: 5px;
}

.room-hud__adjust {
  min-width: 54px;
  height: 42px;
  padding: 0 10px;
  background: #1A1F2E;
  border: 2px solid #22D3EE;
  border-radius: 8px;
  color: #F1F5F9;
  font-weight: 700;
  font-size: 0.95rem;
  transition: all 0.2s ease;
  cursor: pointer;
}

.room-hud__adjust--negative {
  border-color: rgba(248, 113, 113, 0.6);
  color: #FCA5A5;
}

.room-hud__adjust--positive {
  border-color: rgba(74, 222, 128, 0.6);
  color: #86EFAC;
}

.room-hud__adjust:hover {
  transform: translateY(-2px);
  border-color: #EAB308;
  color: #EAB308;
}

/* ---------- Row 2: actions left, income centre, status right ---------- */
/* The side stacks set the row's height; their two items split it evenly
   and share a width so their edges line up. */
.room-hud__stack {
  display: grid;
  grid-template-rows: 1fr 1fr;
  gap: 6px;
}

.room-hud__notices {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 6px;
}

/* The collect button and the income chip butt together as one control,
   two thirds the width of the clock and centred beneath it. It stretches
   to the full row, so its top and bottom line up with the side stacks. */
.room-hud__income-pair {
  width: calc(100% * 2 / 3);
  display: flex;
  align-items: stretch;
  gap: 0;
  min-height: var(--hud-income-height);
}

/* A perfect square: as wide as the block is tall, whatever that is */
.room-hud__collect {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  aspect-ratio: 1 / 1;
  padding: 0;
  background: #1A1F2E;
  border: 1px solid rgba(34, 211, 238, 0.45);
  border-right: none;
  border-radius: 8px 0 0 8px;
  color: #22D3EE;
  cursor: pointer;
  transition: all 0.18s ease;
}

/* Own line box, so the glyph sits on the exact vertical centre */
.room-hud__collect-glyph {
  display: block;
  font-size: 2.6rem;
  font-weight: 900;
  line-height: 1;
  /* '+' renders slightly below the em-box centre in this face */
  transform: translateY(-2px);
}

.room-hud__collect:hover:not(:disabled) {
  border-color: #22D3EE;
  background: rgba(34, 211, 238, 0.12);
}

.room-hud__collect:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Square off the chip's left edge so the pair reads as one unit, and let
   it fill the two-row centre cell. */
.room-hud__income {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
}

.room-hud__income :deep(.room-income-bar__summary) {
  flex: 1 1 auto;
  height: 100%;
  border-radius: 0 8px 8px 0;
}

/* Chips and action buttons fill their grid cell, so each column's edges
   line up flush with the one above and below it. */
.room-hud__chip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 7px 16px;
  background: #1A1F2E;
  border: 1px solid rgba(34, 211, 238, 0.45);
  border-radius: 8px;
  color: #F1F5F9;
  font-weight: 600;
  font-size: 1rem;
  white-space: nowrap;
}

.room-hud__chip-icon {
  font-size: 1.15rem;
  line-height: 1;
}

.room-hud__chip-label {
  letter-spacing: 0.02em;
}

.room-hud__chip--warning {
  background: rgba(244, 114, 128, 0.12);
  border-color: rgba(244, 114, 128, 0.5);
}

/* Clickable secondary actions, sized to match the chips */
.room-hud__action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 7px 18px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 1rem;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.2s ease;
}

.room-hud__action-btn--jail {
  background: rgba(231, 76, 60, 0.14);
  border: 1px solid rgba(231, 76, 60, 0.55);
  color: #FCA5A5;
}

/* No lift on hover here — these sit in a grid and must stay flush */
.room-hud__action-btn--jail:hover:not(:disabled) {
  background: rgba(231, 76, 60, 0.24);
  border-color: #e74c3c;
  color: #fff;
}

.room-hud__action-btn--market {
  background: linear-gradient(135deg, #1a0a2e 0%, #2d1b4e 100%);
  border: 1px solid #8b5cf6;
  color: #e2d9f3;
}

.room-hud__action-btn--market:hover:not(:disabled) {
  border-color: #a78bfa;
  background: linear-gradient(135deg, #24103d 0%, #3b2466 100%);
}

.room-hud__action-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

/* ---------- Responsive ---------- */
@media (max-width: 900px) {
  .room-hud {
    --hud-income-height: 64px;
  }

  .room-hud__clock {
    font-size: 3em;
    letter-spacing: 4px;
    padding: 6px 24px;
  }

  .room-hud__adjust {
    min-width: 46px;
    height: 38px;
    font-size: 0.85rem;
  }
}

/* Phones: clock on its own row, adjusters beneath, then income, then the
   two side stacks side by side. */
@media (max-width: 600px) {
  .room-hud {
    --hud-income-height: 56px;

    grid-template-columns: 1fr 1fr;
    grid-template-areas:
      "clock   clock"
      "minus   plus"
      "income  income"
      "left    right"
      "notices notices";
    column-gap: 8px;
    row-gap: 10px;
    padding: 10px 10px 0 10px;
  }

  /* Too narrow to shorten here; the income block takes the full row */
  .room-hud__income-pair {
    width: auto;
  }

  .room-hud__area--income,
  .room-hud__area--minus,
  .room-hud__area--plus,
  .room-hud__area--left,
  .room-hud__area--right {
    justify-self: stretch;
  }

  .room-hud__clock {
    font-size: 2.5em;
    padding: 5px 14px;
  }

  .room-hud__adjust {
    min-width: 0;
    flex: 1;
  }

  .room-hud__chip,
  .room-hud__action-btn {
    font-size: 0.75rem;
    padding: 5px 9px;
  }
}
</style>
