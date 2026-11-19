<template>
  <div ref="root" class="room-income-bar">
    <button
      type="button"
      class="room-income-bar__summary"
      :aria-expanded="expanded"
      @click="expanded = !expanded"
    >
      <span class="room-income-bar__label">Income</span>
      <span class="room-income-bar__value">
        <span
          class="room-income-bar__net"
          :class="net >= 0 ? 'room-income-bar__net--positive' : 'room-income-bar__net--negative'"
        >
          {{ formatMinutes(net) }}
        </span>
        <span class="room-income-bar__chevron">{{ expanded ? '▲' : '▼' }}</span>
      </span>
    </button>

    <div v-if="expanded" class="room-income-bar__details">
      <div
        v-for="(line, i) in lines"
        :key="i"
        class="room-income-bar__row"
      >
        <span class="room-income-bar__row-label">{{ line.label }}</span>
        <span
          class="room-income-bar__row-value"
          :class="line.minutes >= 0 ? 'room-income-bar__row-value--positive' : 'room-income-bar__row-value--negative'"
        >
          {{ formatSignedMinutes(line.minutes) }}
        </span>
      </div>

      <div class="room-income-bar__row room-income-bar__row--total">
        <span class="room-income-bar__row-label">NET PER TURN</span>
        <span
          class="room-income-bar__row-value"
          :class="net >= 0 ? 'room-income-bar__row-value--positive' : 'room-income-bar__row-value--negative'"
        >
          {{ formatSignedMinutes(net) }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useIncome } from '@/composables/useIncome'

const props = defineProps({
  player: {
    type: Object,
    default: null
  },
  jobs: {
    type: Array,
    default: () => []
  },
  government: {
    type: Object,
    default: null
  },
  allPlayers: {
    type: Array,
    default: () => []
  }
})

const { computeIncomeBreakdown, formatMinutes, formatSignedMinutes } = useIncome()

const expanded = ref(false)
const root = ref(null)

// The breakdown overlays the page, so dismiss it on an outside click
function onDocumentClick(e) {
  if (expanded.value && root.value && !root.value.contains(e.target)) {
    expanded.value = false
  }
}

onMounted(() => document.addEventListener('click', onDocumentClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocumentClick))

const breakdown = computed(() =>
  computeIncomeBreakdown(props.player, {
    jobs: props.jobs,
    government: props.government,
    allPlayers: props.allPlayers
  })
)

const lines = computed(() => breakdown.value.lines)
const net = computed(() => breakdown.value.net)
</script>

<style scoped>
/* Sits in the HUD strip as a chip; the breakdown overlays rather than
   reflowing the page, so expanding it never pushes the roster down. */
.room-income-bar {
  position: relative;
}

.room-income-bar__summary {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  background: #1A1F2E;
  border: 1px solid rgba(34, 211, 238, 0.45);
  border-radius: 8px;
  padding: 6px 14px;
  color: #F1F5F9;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.room-income-bar__summary:hover {
  border-color: #EAB308;
}

.room-income-bar__label {
  text-align: center;
  letter-spacing: 0.08em;
  font-size: 0.9rem;
  line-height: 1.1;
  text-transform: uppercase;
  opacity: 0.8;
}

/* Value and chevron share the second line */
.room-income-bar__value {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  line-height: 1.1;
}

.room-income-bar__net {
  font-size: 1.55rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.room-income-bar__net--positive,
.room-income-bar__row-value--positive {
  color: #4ADE80;
}

.room-income-bar__net--negative,
.room-income-bar__row-value--negative {
  color: #F87171;
}

.room-income-bar__chevron {
  color: #22D3EE;
  font-size: 0.85rem;
}

.room-income-bar__details {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: 1200;
  min-width: 320px;
  background: #1A1F2E;
  border: 2px solid #22D3EE;
  border-radius: 8px;
  padding: 8px 15px 10px 15px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.55);
}

.room-income-bar__row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 4px 0;
  color: #F1F5F9;
  font-size: 0.85rem;
}

.room-income-bar__row-label {
  text-align: left;
}

.room-income-bar__row-value {
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.room-income-bar__row--total {
  border-top: 1px solid rgba(34, 211, 238, 0.35);
  margin-top: 6px;
  padding-top: 8px;
  font-weight: 700;
  letter-spacing: 0.05em;
}

@media (max-width: 575px) {
  .room-income-bar__label {
    font-size: 0.75rem;
  }

  .room-income-bar__row {
    font-size: 0.78rem;
  }
}
</style>
