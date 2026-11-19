<template>
  <div class="room-participants-table__wrapper">
    <table class="room-participants-table__table">
      <thead>
        <tr>
          <!-- Username Header -->
          <th class="room-participants-table__header room-participants-table__header--username">
            Username
          </th>

          <!-- Income Header -->
          <th class="room-participants-table__header room-participants-table__header--income">
            Income
          </th>

          <!-- Job Title Header with Dropdown -->
          <th class="room-participants-table__header room-participants-table__header--job-title">
            <select
              id="jobSelect"
              v-model="jobIdModel"
              class="room-participants-table__header-select"
            >
              <option :value="null">Select a job</option>
              <optgroup
                v-for="group in groupedJobs"
                :key="group.tier"
                :label="group.label"
              >
                <option
                  v-for="j in group.jobs"
                  :key="j.id"
                  :value="j.id"
                  :disabled="j.takenBy !== null"
                >
                  {{ j.takenBy ? `${j.name} — taken by ${j.takenBy}` : j.name }}
                </option>
              </optgroup>
            </select>
            <span class="room-participants-table__header-text">
              Job Title 
              <span class="room-participants-table__header-arrow">▼</span>
            </span>
          </th>

          <!-- Perk Header with Dropdown -->
          <th class="room-participants-table__header room-participants-table__header--perk-title">
            <select
              id="perkSelect"
              v-model="perkModel"
              class="room-participants-table__header-select"
            >
              <option :value="null">None</option>
              <option value="Manager">Manager</option>
              <option value="Senior">Senior</option>
              <option value="Executive">Executive</option>
            </select>
            <span class="room-participants-table__header-text">
              Perk 
              <span class="room-participants-table__header-arrow">▼</span>
            </span>
          </th>

          <!-- Approval Status Header -->
          <th class="room-participants-table__header room-participants-table__header--approval-title">
            <select
              id="approvalHeaderSelect"
              v-model="approvalModel"
              @change="$emit('header-approval-changed')"
              class="room-participants-table__header-select"
            >
              <option :value="null">Select status</option>
              <option value="approve">Approve</option>
              <option value="reject">Reject</option>
            </select>
            <span class="room-participants-table__header-text">
              Approval 
              <span class="room-participants-table__header-arrow">▼</span>
            </span>
          </th>

          <!-- Bleed Header -->
          <th class="room-participants-table__header room-participants-table__header--bleed">
            <div class="room-participants-table__bleed-header-inner">
              <b-button
                size="sm"
                class="room-participants-table__bleed-button room-participants-table__bleed-button--minus"
                @click="$emit('bleed-changed', -1)"
                aria-label="Decrease bleed"
              >
                -
              </b-button>
              <span class="room-participants-table__bleed-label">Bleed</span>
              <b-button
                size="sm"
                class="room-participants-table__bleed-button room-participants-table__bleed-button--plus"
                @click="$emit('bleed-changed', 1)"
                aria-label="Increase bleed"
              >
                +
              </b-button>
            </div>
          </th>

          <!-- Heat Header -->
          <th class="room-participants-table__header room-participants-table__header--heat">
            <div class="room-participants-table__heat-header-inner">
              <b-button
                size="sm"
                class="room-participants-table__heat-button room-participants-table__heat-button--minus"
                @click="$emit('heat-changed', -1)"
                aria-label="Decrease heat"
              >
                -
              </b-button>
              <span class="room-participants-table__heat-label">Heat</span>
              <b-button
                size="sm"
                class="room-participants-table__heat-button room-participants-table__heat-button--plus"
                @click="$emit('heat-changed', 1)"
                aria-label="Increase heat"
              >
                +
              </b-button>
            </div>
          </th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="p in activePlayers" :key="p.user_id || p.userId || p.id">
          <!-- Username Column -->
          <td
            class="room-participants-table__cell room-participants-table__cell--username"
            :class="{ 'room-participants-table__cell--state-enemy': isStateEnemy(p) }"
          >
            <span v-if="isStateEnemy(p)" class="room-participants-table__enemy-icon">⚔️</span>
            {{ p.username }}
            <img
              v-if="getGovernmentIcon(p)"
              :src="getGovernmentIcon(p)"
              class="room-participants-table__gov-icon"
              alt="Government Role"
            />
          </td>

          <!-- Income Column -->
          <td class="room-participants-table__cell room-participants-table__cell--income">
            {{ playerIncomeMap[p.user_id || p.userId || p.id] || '+00:00' }}
          </td>

          <!-- Job Title Column -->
          <td class="room-participants-table__cell room-participants-table__cell--job-title">
            {{ p.job_name }}
          </td>

          <!-- Perk Column -->
          <td class="room-participants-table__cell room-participants-table__cell--perk">
            <img
              v-if="getPerkIcon(p)"
              :src="getPerkIcon(p)"
              class="room-participants-table__perk-icon"
              :alt="p.perk"
            />
          </td>

          <!-- Approval Status Column -->
          <td class="room-participants-table__cell room-participants-table__cell--approval">
            <span 
              v-if="p.approval_status && p.user_id === currentUserId"
              @click="$emit('clear-approval')"
              class="room-participants-table__badge room-participants-table__badge--approval"
              :class="`room-participants-table__badge--approval-${p.approval_status}`"
              style="cursor: pointer;"
            >
              {{ p.approval_status }}
            </span>
            <span 
              v-else-if="p.approval_status"
              class="room-participants-table__badge room-participants-table__badge--approval"
              :class="`room-participants-table__badge--approval-${p.approval_status}`"
            >
              {{ p.approval_status }}
            </span>
            <span v-else class="room-participants-table__badge room-participants-table__badge--approval-empty">
              —
            </span>
          </td>

          <!-- Bleed Column -->
          <td class="room-participants-table__cell room-participants-table__cell--bleed">
            {{ p.bleed }}
          </td>

          <!-- Heat Column -->
          <td class="room-participants-table__cell room-participants-table__cell--heat">
            {{ p.heat }}
          </td>
        </tr>

        <!-- Empty State -->
        <tr v-if="!activePlayers.length">
          <td :colspan="8" class="room-participants-table__cell--empty">
            No participants yet
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, computed } from 'vue'
import { useIncome } from '@/composables/useIncome'

const { computeIncomeBreakdown, formatMinutes } = useIncome()

const props = defineProps({
  activePlayers: {
    type: Array,
    required: true
  },
  jobs: {
    type: Array,
    required: true
  },
  selectedJobId: {
    type: [String, Number],
    default: null
  },
  selectedPerk: {
    type: String,
    default: null
  },
  selectedHeaderApproval: {
    type: String,
    default: null
  },
  selectedHeaderVote: {
    type: String,
    default: null
  },
  currentUserId: {
    type: [String, Number],
    required: true
  },
  governmentIcon: {
    type: Function,
    required: true
  },
  perkIcon: {
    type: Function,
    required: true
  },
  roomGovernment: {
    type: Object,
    default: null
  },
  stateEnemies: {
    type: Array,
    default: () => []
  }
})

const getGovernmentIcon = (participant) => {
  return props.governmentIcon(participant)
}

const isStateEnemy = (participant) => {
  const id = participant.user_id || participant.userId || participant.id
  return props.stateEnemies.some(e => e.user_id === id)
}

const getPerkIcon = (participant) => {
  return props.perkIcon(participant)
}

// Jobs chunked by tier, alphabetical within each chunk.
// Tier 3 jobs are unique per game, so any already held by another living
// player is shown as taken and cannot be picked (the server enforces this
// too — see _tier3_job_taken in sockets.py).
const TIER_LABELS = {
  0: 'Unemployed',
  1: 'Tier 1',
  2: 'Tier 2',
  3: 'Tier 3 — one player each'
}

const groupedJobs = computed(() => {
  const currentId = props.currentUserId
  const byTier = new Map()

  for (const j of props.jobs) {
    const tier = j.tier || 0
    let takenBy = null
    if (tier === 3) {
      const holder = props.activePlayers.find(p => {
        const pid = p.user_id || p.userId || p.id
        return p.job_name === j.name && pid !== currentId
      })
      if (holder) takenBy = holder.username
    }
    if (!byTier.has(tier)) byTier.set(tier, [])
    byTier.get(tier).push({ ...j, takenBy })
  }

  return [...byTier.keys()]
    .sort((a, b) => a - b)
    .map(tier => ({
      tier,
      label: TIER_LABELS[tier] || `Tier ${tier}`,
      jobs: byTier.get(tier).sort((a, b) => a.name.localeCompare(b.name))
    }))
})

const playerIncomeMap = computed(() => {
  const map = {}
  for (const p of props.activePlayers) {
    const id = p.user_id || p.userId || p.id
    const { net } = computeIncomeBreakdown(p, {
      jobs: props.jobs,
      government: props.roomGovernment,
      allPlayers: props.activePlayers
    })
    map[id] = formatMinutes(net)
  }
  return map
})

// Two-way bindings for parent state
const emit = defineEmits([
  'update:selectedJobId',
  'update:selectedPerk',
  'update:selectedHeaderApproval',
  'update:selectedHeaderVote',
  'header-approval-changed',
  'header-vote-changed',
  'bleed-changed',
  'heat-changed',
  'clear-approval',
  'clear-vote'
])

const jobIdModel = computed({
  get() {
    return props.selectedJobId
  },
  set(value) {
    emit('update:selectedJobId', value)
  }
})

const perkModel = computed({
  get() {
    return props.selectedPerk
  },
  set(value) {
    emit('update:selectedPerk', value)
  }
})

const approvalModel = computed({
  get() {
    return props.selectedHeaderApproval
  },
  set(value) {
    emit('update:selectedHeaderApproval', value)
  }
})

const voteModel = computed({
  get() {
    return props.selectedHeaderVote
  },
  set(value) {
    emit('update:selectedHeaderVote', value)
  }
})
</script>

<style scoped>
.room-participants-table__wrapper {
  display: flex;
  justify-content: center;
  width: 100%;
  margin-top: 10px;
  margin-bottom: 12px;
  padding: 0 16px;
}

/* Below ~900px the seven columns can no longer share the width without
   crushing the bleed/heat controls, so scroll the table instead of
   clipping it. */
@media (max-width: 900px) {
  .room-participants-table__wrapper {
    display: block;
    overflow-x: auto;
    padding: 0 10px;
  }

  .room-participants-table__table {
    min-width: 720px;
  }
}

.room-participants-table__table {
  width: 100%;
  /* Capped so the roster doesn't sprawl on very wide monitors and leave the
     centred HUD looking lost above it. */
  max-width: 1500px;
  background: #1A1F2E !important;
  border: 1px solid rgba(241, 245, 249, 0.3) !important;
  border-radius: 12px;
  overflow: hidden;
  table-layout: fixed;
}

/* Table Header Styling */
.room-participants-table__table thead {
  background: #0B0F19 !important;
  border-bottom: 2px solid #22D3EE !important;
}

.room-participants-table__table thead tr {
  height: 40px;
  background: #0B0F19 !important;
  overflow: hidden;
  max-height: 40px;
}

/* NOTE: header height is 40px = 10px + 20px line-height + 10px.
   The same sum is repeated on .room-participants-table__header-text,
   because the three dropdown headers delegate their padding to that
   inner span. Change one and you must change the other. */
.room-participants-table__header {
  vertical-align: middle;
  height: 40px;
  border: 1px solid #22D3EE !important;
  color: #EAB308 !important;
  font-weight: 700 !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-align: center !important;
  font-family: 'Barlow Condensed' !important;
  font-size: 1.05em !important;
  background: #1A1F2E !important;
  padding: 4px 10px !important;
  line-height: 20px;
  overflow: hidden;
  max-height: 40px;
}

.room-participants-table__header-select {
  position: absolute;
  opacity: 0;
  width: 100%;
  height: 100%;
  cursor: pointer;
  margin: 0;
  padding: 0;
  border: none;
  top: 0;
  left: 0;
  z-index: 10;
}

/* 10 + 20 + 10 = the 40px header height above. Keep these in sync. */
.room-participants-table__header-text {
  display: block;
  color: #EAB308 !important;
  font-weight: 700 !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-family: 'Barlow Condensed' !important;
  font-size: 1.05em !important;
  padding: 10px !important;
  text-align: center !important;
  line-height: 20px;
}

.room-participants-table__header-arrow {
  margin-left: 4px;
  font-size: 0.9em;
}

/* Header Specific.
   The table is table-layout:fixed at width:100%, so these act as
   proportions. Username and Job Title get the width freed by removing
   the old 1400px cap; Bleed/Heat only need room for two 28px buttons. */
.room-participants-table__header--username {
  width: 18%;
}

.room-participants-table__header--income {
  width: 11%;
}

.room-participants-table__header--job-title {
  width: 21%;
  position: relative;
  padding: 0 !important;
  cursor: pointer;
  overflow: hidden;
  max-height: 40px;
}

.room-participants-table__header--perk-title {
  width: 11%;
  position: relative;
  padding: 0 !important;
  cursor: pointer;
  overflow: hidden;
  max-height: 40px;
}

.room-participants-table__header--approval-title {
  width: 14%;
  position: relative;
  padding: 0 !important;
  cursor: pointer;
  overflow: hidden;
  max-height: 40px;
}

.room-participants-table__header--vote-title {
  width: 11%;
  position: relative;
  padding: 0 !important;
  cursor: pointer;
  overflow: hidden;
  max-height: 40px;
}

.room-participants-table__header--bleed {
  width: 12%;
  text-align: center;
  vertical-align: middle;
  overflow: visible !important;
  max-height: none !important;
}

.room-participants-table__header--heat {
  width: 12%;
  text-align: center;
  vertical-align: middle;
  overflow: visible !important;
  max-height: none !important;
}

/* Bleed/Heat Header Inner */
.room-participants-table__bleed-header-inner,
.room-participants-table__heat-header-inner {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.room-participants-table__bleed-label,
.room-participants-table__heat-label {
  font-weight: 700 !important;
  font-size: 1.15em !important;
  font-family: 'Barlow Condensed' !important;
  line-height: 28px;
  color: #EAB308 !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.room-participants-table__bleed-button,
.room-participants-table__heat-button {
  width: 28px;
  height: 28px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  font-weight: 700;
  border-width: 2px;
  background: #1A1F2E !important;
  border-color: #22D3EE !important;
  color: #F1F5F9 !important;
  transition: all 0.2s ease;
}

.room-participants-table__bleed-button:hover,
.room-participants-table__heat-button:hover {
  border-color: #EAB308 !important;
  color: #EAB308 !important;
  transform: translateY(-1px);
}

/* Table Body Styling */
.room-participants-table__table tbody {
  background: #1A1F2E !important;
}

/* Rows are 44px. The floor is the perk icon (32px) plus padding. */
.room-participants-table__cell {
  border-color: rgba(241, 245, 249, 0.15) !important;
  padding: 6px 10px !important;
  vertical-align: middle;
  color: #F1F5F9 !important;
  font-weight: 500;
  text-align: center !important;
  font-size: 1em !important;
  background: #1A1F2E !important;
  height: 44px !important;
  min-height: 44px !important;
  max-height: 44px !important;
  overflow: hidden !important;
}

.room-participants-table__table tbody tr {
  transition: background-color 0.2s ease;
  background: #1A1F2E !important;
  height: 44px !important;
  min-height: 44px !important;
  max-height: 44px !important;
  overflow: hidden !important;
}

.room-participants-table__table tbody tr:hover {
  background-color: rgba(241, 245, 249, 0.1) !important;
}

/* Column Specific */
.room-participants-table__cell--username {
  width: 100px;
  min-width: 100px;
  max-width: 100px;
}

.room-participants-table__cell--state-enemy {
  color: #ef4444 !important;
  font-weight: 700;
}

.room-participants-table__enemy-icon {
  margin-right: 2px;
}

/* Column widths come from the <th> rules above (table-layout: fixed uses
   the first row), so cells only carry appearance, not sizing. */
.room-participants-table__cell--income {
  font-family: 'Courier New', monospace;
  font-weight: 600;
}

.room-participants-table__cell--perk {
  padding: 0 !important;
  background: transparent !important;
  border: none !important;
  position: relative;
}

.room-participants-table__cell--approval {
  padding: 4px 10px !important;
}

.room-participants-table__cell--vote {
  padding: 4px 10px !important;
}

.room-participants-table__cell--empty {
  text-align: center;
  column-span: 7;
}

/* Icons — sized to fit a 44px row (was 40px, which forced 60px rows) */
.room-participants-table__gov-icon {
  height: 26px;
  width: auto;
  margin-left: 6px;
  vertical-align: middle;
  display: inline-block;
}

@media (min-width: 1200px) {
  .room-participants-table__gov-icon {
    height: 32px;
  }
}

.room-participants-table__perk-icon {
  height: 32px;
  width: 32px;
  object-fit: contain;
  position: absolute !important;
  top: 50% !important;
  left: 50% !important;
  transform: translate(-50%, -50%) !important;
  margin: 0 !important;
}

/* Badges */
.room-participants-table__badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.85em;
  font-weight: 600;
  min-width: 60px;
  border: 1px solid rgba(241, 245, 249, 0.3);
  background: transparent;
}

.room-participants-table__badge--approval {
  /* approval-specific class */
}

.room-participants-table__badge--approval-empty,
.room-participants-table__badge--vote-empty {
  color: #666;
  background: rgba(241, 245, 249, 0.05);
  border-color: rgba(241, 245, 249, 0.2);
}

.room-participants-table__badge--approval-approve {
  background: rgba(241, 245, 249, 0.2);
  color: #F1F5F9;
  border-color: rgba(241, 245, 249, 0.5);
}

.room-participants-table__badge--approval-reject {
  background: rgba(255, 68, 68, 0.2);
  color: #ff4444;
  border-color: rgba(255, 68, 68, 0.5);
}

.room-participants-table__badge--approval-abstain {
  background: rgba(255, 200, 0, 0.2);
  color: #ffcc00;
  border-color: rgba(255, 200, 0, 0.5);
}

.room-participants-table__badge--vote {
  /* vote-specific class */
}

.room-participants-table__badge--vote-yes {
  background: rgba(241, 245, 249, 0.2);
  color: #F1F5F9;
  border-color: rgba(241, 245, 249, 0.5);
}

.room-participants-table__badge--vote-no {
  background: rgba(255, 68, 68, 0.2);
  color: #ff4444;
  border-color: rgba(255, 68, 68, 0.5);
}

.room-participants-table__badge--vote-abstain {
  background: rgba(255, 200, 0, 0.2);
  color: #ffcc00;
  border-color: rgba(255, 200, 0, 0.5);
}
</style>
