<template>
  <div class="room-participants-table__wrapper">
    <table class="room-participants-table__table">
      <thead>
        <tr>
          <!-- Username Header -->
          <th class="room-participants-table__header room-participants-table__header--username">
            Username
          </th>

          <!-- Job Title Header with Dropdown -->
          <th class="room-participants-table__header room-participants-table__header--job-title">
            <select
              id="jobSelect"
              v-model="jobIdModel"
              class="room-participants-table__header-select"
            >
              <option :value="null">Select a job</option>
              <option v-for="j in jobs" :key="j.id" :value="j.id">
                {{ j.tier ? `${j.name} (Tier ${j.tier})` : j.name }}
              </option>
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
          <td class="room-participants-table__cell room-participants-table__cell--username">
            {{ p.username }}
            <img
              v-if="getGovernmentIcon(p)"
              :src="getGovernmentIcon(p)"
              class="room-participants-table__gov-icon"
              alt="Government Role"
            />
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
          <td :colspan="7" class="room-participants-table__cell--empty">
            No participants yet
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, computed } from 'vue'

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
  }
})

const getGovernmentIcon = (participant) => {
  return props.governmentIcon(participant)
}

const getPerkIcon = (participant) => {
  return props.perkIcon(participant)
}

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
  margin-top: 30px;
  margin-bottom: 30px;
}

.room-participants-table__table {
  width: 95%;
  max-width: 1400px;
  background: #1A1F2E !important;
  border: 1px solid rgba(241, 245, 249, 0.3) !important;
  border-radius: 12px;
  overflow: hidden;
  margin-top: 20px;
  table-layout: fixed;
}

/* Table Header Styling */
.room-participants-table__table thead {
  background: #0B0F19 !important;
  border-bottom: 2px solid #22D3EE !important;
}

.room-participants-table__table thead tr {
  height: 50px;
  background: #0B0F19 !important;
  overflow: hidden;
  max-height: 50px;
}

.room-participants-table__header {
  vertical-align: middle;
  height: 50px;
  border: 1px solid #22D3EE !important;
  color: #EAB308 !important;
  font-weight: 700 !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-align: center !important;
  font-family: 'Barlow Condensed' !important;
  font-size: 1.15em !important;
  background: #1A1F2E !important;
  padding: 4px 13px !important;
  line-height: 20px;
  overflow: hidden;
  max-height: 50px;
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

.room-participants-table__header-text {
  display: block;
  color: #EAB308 !important;
  font-weight: 700 !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-family: 'Barlow Condensed' !important;
  font-size: 1.15em !important;
  padding: 15px !important;
  text-align: center !important;
  line-height: 20px;
}

.room-participants-table__header-arrow {
  margin-left: 4px;
  font-size: 0.9em;
}

/* Header Specific */
.room-participants-table__header--username {
  width: 100px;
  min-width: 100px;
  max-width: 100px;
}

.room-participants-table__header--job-title {
  width: 130px;
  min-width: 130px;
  max-width: 130px;
  position: relative;
  padding: 0 !important;
  cursor: pointer;
  overflow: hidden;
  max-height: 50px;
}

.room-participants-table__header--perk-title {
  width: 100px;
  min-width: 100px;
  max-width: 100px;
  position: relative;
  padding: 0 !important;
  cursor: pointer;
  overflow: hidden;
  max-height: 50px;
}

.room-participants-table__header--approval-title {
  width: 100px;
  min-width: 100px;
  max-width: 100px;
  position: relative;
  padding: 0 !important;
  cursor: pointer;
  overflow: hidden;
  max-height: 50px;
}

.room-participants-table__header--vote-title {
  width: 100px;
  min-width: 100px;
  max-width: 100px;
  position: relative;
  padding: 0 !important;
  cursor: pointer;
  overflow: hidden;
  max-height: 50px;
}

.room-participants-table__header--bleed {
  width: 110px;
  min-width: 110px;
  max-width: 110px;
  text-align: center;
  vertical-align: middle;
  overflow: visible !important;
  max-height: none !important;
}

.room-participants-table__header--heat {
  width: 110px;
  min-width: 110px;
  max-width: 110px;
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

.room-participants-table__cell {
  border-color: rgba(241, 245, 249, 0.15) !important;
  padding: 15px !important;
  vertical-align: middle;
  color: #F1F5F9 !important;
  font-weight: 500;
  text-align: center !important;
  font-size: 1.1em !important;
  background: #1A1F2E !important;
  height: 60px !important;
  min-height: 60px !important;
  max-height: 60px !important;
  overflow: hidden !important;
}

.room-participants-table__table tbody tr {
  transition: background-color 0.2s ease;
  background: #1A1F2E !important;
  height: 60px !important;
  min-height: 60px !important;
  max-height: 60px !important;
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

.room-participants-table__cell--job-title {
  width: 130px;
  min-width: 130px;
  max-width: 130px;
}

.room-participants-table__cell--perk {
  width: 100px;
  min-width: 100px;
  max-width: 100px;
  padding: 0 !important;
  background: transparent !important;
  border: none !important;
  position: relative;
}

.room-participants-table__cell--approval {
  width: 100px;
  min-width: 100px;
  max-width: 100px;
  padding: 5px 12px !important;
}

.room-participants-table__cell--vote {
  width: 100px;
  min-width: 100px;
  max-width: 100px;
  padding: 5px 12px !important;
}

.room-participants-table__cell--bleed {
  width: 110px;
  min-width: 110px;
  max-width: 110px;
}

.room-participants-table__cell--heat {
  width: 110px;
  min-width: 110px;
  max-width: 110px;
}

.room-participants-table__cell--empty {
  text-align: center;
  column-span: 7;
}

/* Icons */
.room-participants-table__gov-icon {
  height: 28px;
  width: auto;
  margin-left: 6px;
  vertical-align: middle;
  display: inline-block;
}

@media (min-width: 1200px) {
  .room-participants-table__gov-icon {
    height: 40px;
  }
}

.room-participants-table__perk-icon {
  height: 40px;
  width: 40px;
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
