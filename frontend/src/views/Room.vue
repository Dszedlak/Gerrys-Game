<template>
  <div id="app">
    <b-container class="bv-example-row">
      <b-row class="itemRow">
        <b-col>
          <div class="top-actions">
            <b-button-group class="top-actions-group">
              <b-button class="butt" @click="openLeaveModal">Leave Room?</b-button>
              <b-button v-if="isAdmin" class="butt" variant="danger" @click="openRemoveModal">End Game?</b-button>
              <b-button v-if="isAdmin" class="butt" variant="info" @click="openWheelSpinner">Spin Wheel</b-button>
            </b-button-group>
          </div>
        </b-col>
      </b-row>
      <b-row class="itemRow">
        <b-col>
          <h1>Clock</h1>
          <!-- FIX: correct component tag -->
          <ClickToEdit id="clock" :value="clock" action="updateClock" />
        </b-col>
      </b-row>
      <b-row>
        <b-col>
          <div class="clock-controls">
            <b-button-group class="mx-1">
              <b-button class="addremovebuttonClock" @click="uClock(-60)">-1h</b-button>
              <b-button class="addremovebuttonClock" @click="uClock(-30)">-30</b-button>
              <b-button class="addremovebuttonClock" @click="uClock(-20)">-20</b-button>
              <b-button class="addremovebuttonClock" @click="uClock(-10)">-10</b-button>
            </b-button-group>
            <b-button-group class="mx-1">
              <b-button class="addremovebuttonClock" @click="uClock(10)">+10</b-button>
              <b-button class="addremovebuttonClock" @click="uClock(20)">+20</b-button>
              <b-button class="addremovebuttonClock" @click="uClock(30)">+30</b-button>
              <b-button class="addremovebuttonClock" @click="uClock(60)">+1h</b-button>
            </b-button-group>
          </div>
        </b-col>
        <b-col></b-col>
      </b-row>

      <!-- The Market Section (above the table) -->
      <b-row class="mt-4">
        <b-col>
          <div class="center-row">
            <h3>The Market</h3>
          </div>
          <div class="market-controls mt-2">
            <b-button class="market-btn" variant="success" @click="sellConsumable">Sell a Consumable (+30m)</b-button>
            <b-button class="market-btn" variant="primary" @click="sellTimeCounter">Sell a Time Counter (+2.5h)</b-button>
          </div>
        </b-col>
      </b-row>

      <!-- Centered dropdowns for Government and Job -->
      <b-row class="mt-3 mb-4">  <!-- add bottom margin under the dropdowns -->
        <b-col>
          <div class="center-row dropdowns">
            <div class="control-group">
              <label for="govSelect" class="mr-2">Government:</label>
              <select
                id="govSelect"
                v-model="selectedGovernmentId"
                class="dropdown-w form-control"
                :disabled="!isAdmin"
                @change="onGovernmentChange"
              >
                <option :value="null">Select a government</option>
                <option v-for="g in displayGovernments" :key="g.id" :value="g.id">
                  {{ g.name }}
                </option>
              </select>
            </div>

            <div class="job-controls">
              <label for="jobSelect" class="mr-2">Job:</label>
              <select
                id="jobSelect"
                v-model="selectedJobId"
                class="dropdown-w form-control"
              >
                <option :value="null">Select a job</option>
                <option v-for="j in jobs" :key="j.id" :value="j.id">
                  {{ j.tier ? `${j.name} (Tier ${j.tier})` : j.name }}
                </option>
              </select>
              <b-button
                class="btn-paid"
                variant="warning"
                :disabled="isPaying"
                @click="getPaid"
                title="Request pay based on your current job"
              >
                {{ isPaying ? 'Getting Paid…' : 'Get Paid' }}
              </b-button>
            </div>

            <div class="perk-controls">
              <span class="perk-label">Perk:</span>
              <button 
                class="perk-btn" 
                :class="{ active: selectedPerk === null }"
                @click="selectedPerk = null"
                type="button"
              >
                None
              </button>
              <button 
                class="perk-btn" 
                :class="{ active: selectedPerk === 'Manager' }"
                @click="selectedPerk = 'Manager'"
                type="button"
                title="Manager (+10 mins)"
              >
                <img src="/manager.png" alt="M" class="perk-btn-icon" />
              </button>
              <button 
                class="perk-btn" 
                :class="{ active: selectedPerk === 'Senior' }"
                @click="selectedPerk = 'Senior'"
                type="button"
                title="Senior (+20 mins)"
              >
                <img src="/senior.png" alt="S" class="perk-btn-icon" />
              </button>
              <button 
                class="perk-btn" 
                :class="{ active: selectedPerk === 'Executive' }"
                @click="selectedPerk = 'Executive'"
                type="button"
                title="Executive (+30 mins)"
              >
                <img src="/executive.png" alt="E" class="perk-btn-icon" />
              </button>
            </div>
          </div>
        </b-col>
      </b-row>

      <!-- Participants table -->
      <b-row class="itemRowPlayers mt-4"> <!-- add top margin above the table -->
        <b-col></b-col>
        <b-col cols="1.4">
          <table class="table table-sm table-bordered" style="width:100%">
            <thead>
              <tr>
                <th>Username</th>
                <th>Job Title</th>
                <th class="bleed-header">
                  <!-- wrap in a flex container for perfect centering -->
                  <div class="bleed-header-inner">
                    <b-button
                      size="sm"
                      class="bleed-btn bleed-btn-minus"
                      variant="danger"
                      @click="changeBleed(-1)"
                      aria-label="Decrease bleed"
                    >-</b-button>
                    <span class="mx-1 bleed-label">Bleed</span>
                    <b-button
                      size="sm"
                      class="bleed-btn bleed-btn-plus"
                      variant="success"
                      @click="changeBleed(1)"
                      aria-label="Increase bleed"
                    >+</b-button>
                  </div>
                </th>
                <th class="heat-header">
                  <div class="heat-header-inner">
                    <b-button
                      size="sm"
                      class="heat-btn heat-btn-minus"
                      variant="danger"
                      @click="changeHeat(-1)"
                      aria-label="Decrease heat"
                    >-</b-button>
                    <span class="mx-1 heat-label">Heat</span>
                    <b-button
                      size="sm"
                      class="heat-btn heat-btn-plus"
                      variant="success"
                      @click="changeHeat(1)"
                      aria-label="Increase heat"
                    >+</b-button>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in activePlayers" :key="p.user_id || p.userId || p.id">
                <td>
                  {{ p.username }}
                  <img
                    v-if="iconForParticipant(p)"
                    :src="iconForParticipant(p)"
                    class="gov-icon"
                    alt=""
                  />
                </td>
                <td>
                  {{ p.job_name }}
                  <img
                    v-if="perkIconForParticipant(p)"
                    :src="perkIconForParticipant(p)"
                    class="perk-icon"
                    :alt="p.perk"
                  />
                </td>
                <td>{{ p.bleed }}</td>
                <td>{{ p.heat }}</td>
              </tr>
              <tr v-if="!activePlayers.length">
                <td colspan="4" class="text-center">No participants yet</td>
              </tr>
            </tbody>
          </table>
        </b-col>
        <b-col></b-col>
      </b-row>

      <!-- Dropped Players table -->
      <b-row v-if="droppedPlayers.length > 0" class="itemRowPlayers mt-3">
        <b-col></b-col>
        <b-col cols="1.4">
          <h5 class="text-muted">Dropped Players</h5>
          <table class="table table-sm table-bordered dropped-table" style="width:100%">
            <thead>
              <tr>
                <th>Username</th>
                <th>Job Title</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in droppedPlayers" :key="p.user_id || p.userId || p.id" class="dropped-row">
                <td>
                  {{ p.username }}
                  <img
                    v-if="iconForParticipant(p)"
                    :src="iconForParticipant(p)"
                    class="gov-icon"
                    alt=""
                  />
                </td>
                <td>
                  {{ p.job_name }}
                  <img
                    v-if="perkIconForParticipant(p)"
                    :src="perkIconForParticipant(p)"
                    class="perk-icon"
                    :alt="p.perk"
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </b-col>
        <b-col></b-col>
      </b-row>

      <!-- Leave Room modal -->
      <b-modal
        id="LeaveRoomModal"
        ref="leaveRoomModal"
        title="Leave Room:"
        hide-footer
      >
        Are you sure you want to Leave room: {{ roomname }}
        <template #footer>
          <b-button size="sm" variant="secondary" :disabled="isLeaving" @click="leaveRoomModal?.hide()">
            No
          </b-button>
          <b-button size="sm" variant="success" :disabled="isLeaving" @click="confirmLeave">
            {{ isLeaving ? 'Leaving…' : 'Yes' }}
          </b-button>
        </template>
      </b-modal>

      <!-- End Game modal -->
      <b-modal
        id="removeRoomModal"
        ref="removeRoomModal"
        title="End Game:"
        hide-footer
      >
        Are you sure you want to end the game: {{ roomname }}
        <template #footer>
          <b-button size="sm" variant="secondary" :disabled="isRemoving" @click="removeRoomModal?.hide()">
            No
          </b-button>
          <b-button size="sm" variant="success" :disabled="isRemoving" @click="confirmRemove">
            {{ isRemoving ? 'Ending…' : 'Yes' }}
          </b-button>
        </template>
      </b-modal>

      <!-- Game History Graph modal -->
      <b-modal
        id="historyGraphModal"
        ref="historyGraphModal"
        title="Game History"
        size="xl"
      >
        <div v-if="loadingHistory" class="text-center">
          <p>Loading game history...</p>
        </div>
        <div v-else-if="historyError" class="alert alert-danger">
          {{ historyError }}
        </div>
        <div v-else-if="chartData" style="height: 400px;">
          <Line :data="chartData" :options="chartOptions" />
        </div>
        <div v-else class="text-center">
          <p>No history data available</p>
        </div>
        <template #footer>
          <b-button size="sm" variant="secondary" @click="historyGraphModal?.hide()">
            Close
          </b-button>
          <b-button size="sm" variant="danger" :disabled="isRemoving" @click="finalizeRemoveRoom">
            {{ isRemoving ? 'Ending...' : 'End Game & Close Room' }}
          </b-button>
        </template>
      </b-modal>

      <!-- Government role assignment modal (admin only, opened on change) -->
      <b-modal
        id="govAssignModal"
        ref="govAssignModal"
        title="Assign Government Roles"
        hide-footer
      >
        <div v-if="govForm.type === 'Dictatorship'">
          <label for="dictatorSelect" class="mr-2">Select the Dictator:</label>
          <select id="dictatorSelect" v-model="govForm.dictator" class="form-control">
            <option :value="null">Choose a user</option>
            <option v-for="opt in participantOptions" :key="opt.value" :value="opt.value">
              {{ opt.text }}
            </option>
          </select>
        </div>

        <div v-else-if="govForm.type === 'Republic'">
          <div class="mb-3">
            <label for="headSelect" class="mr-2">Head of State:</label>
            <select id="headSelect" v-model="govForm.head_of_state" class="form-control">
              <option :value="null">Choose a user</option>
              <option v-for="opt in participantOptions" :key="opt.value" :value="opt.value">
                {{ opt.text }}
              </option>
            </select>
          </div>
          <div>
            <label for="advisorSelect" class="mr-2">Advisors (2):</label>
            <select
              id="advisorSelect"
              v-model="govForm.advisors"
              class="form-control"
              multiple
              size="5"
            >
              <option v-for="opt in participantOptions" :key="opt.value" :value="opt.value">
                {{ opt.text }}
              </option>
            </select>
            <small class="text-muted">Hold Ctrl (Cmd on Mac) to select two advisors.</small>
          </div>
        </div>

        <div v-else-if="govForm.type === 'Communism'">
          <label for="politburoSelect" class="mr-2">Politburo members (3):</label>
          <select
            id="politburoSelect"
            v-model="govForm.politburo"
            class="form-control"
            multiple
            size="6"
          >
            <option v-for="opt in participantOptions" :key="opt.value" :value="opt.value">
              {{ opt.text }}
            </option>
          </select>
          <small class="text-muted">Hold Ctrl (Cmd on Mac) to select three members.</small>
        </div>

        <div v-else>
          <p class="text-muted">No roles required for {{ govForm.type }}.</p>
        </div>

        <div class="text-danger mt-2" v-if="govError">{{ govError }}</div>

        <div class="d-flex justify-content-end mt-3">
          <b-button size="sm" variant="secondary" :disabled="isSubmittingGov" @click="govAssignModal?.hide()">
            Cancel
          </b-button>
          <b-button size="sm" class="ml-2" variant="primary" :disabled="isSubmittingGov" @click="submitGovernment">
            {{ isSubmittingGov ? 'Saving…' : 'Save' }}
          </b-button>
        </div>
      </b-modal>

      <!-- Wheel Spinner Component -->
      <WheelSpinner ref="wheelSpinnerRef" :participants="participants" />

      <!-- Politburo Wheel Selection Modal -->
      <b-modal
        id="politburoWheelModal"
        ref="politburoWheelModal"
        title="Select Politburo Members (Spin 3 Times)"
        size="xl"
        hide-footer
      >
        <div class="politburo-selection">
          <div class="mb-3">
            <label class="form-check-label">
              <input type="checkbox" v-model="balanceBooksOnSave" class="form-check-input" />
              Balance the books after selecting politburo
            </label>
          </div>

          <div class="selected-members mb-3">
            <h5>Selected Politburo Members ({{ politburoMembers.length }}/3):</h5>
            <div v-if="politburoMembers.length === 0" class="text-muted">No members selected yet</div>
            <div v-else class="member-list">
              <span v-for="(memberId, idx) in politburoMembers" :key="idx" class="badge bg-primary me-2">
                {{ participantOptions.find(p => p.value === memberId)?.text || 'Unknown' }}
              </span>
            </div>
          </div>

          <div class="wheel-container-politburo mb-3">
            <WheelSpinner ref="politburoWheelRef" :participants="availablePolitburoCandidates" :show-custom-actions="true">
              <template #winner-actions>
                <b-button 
                  variant="success" 
                  size="lg"
                  @click="addToPolitburo"
                  class="me-2"
                >
                  Add to Politburo
                </b-button>
                <b-button 
                  variant="warning" 
                  size="lg"
                  @click="spinAgain"
                >
                  Spin Again
                </b-button>
              </template>
            </WheelSpinner>
          </div>

          <div v-if="showWheelResult && currentWheelWinner" class="wheel-result mb-3">
            <div class="alert alert-info">
              <h5>Wheel Result: {{ currentWheelWinner.username }}</h5>
              <div class="result-actions mt-2">
                <b-button 
                  variant="success" 
                  @click="addToPolitburo"
                  class="me-2"
                >
                  Add to Politburo
                </b-button>
                <b-button 
                  variant="warning" 
                  @click="spinAgain"
                >
                  Spin Again
                </b-button>
              </div>
            </div>
          </div>

          <div class="politburo-actions">
            <b-button 
              variant="primary" 
              :disabled="isSpinningPolitburo || politburoMembers.length >= 3"
              @click="spinForNextMember"
              class="me-2"
            >
              Politburo Spin The Wheel
            </b-button>
            <b-button 
              variant="warning" 
              :disabled="politburoMembers.length === 0"
              @click="resetPolitburoSelection"
              class="me-2"
            >
              Choose Again?
            </b-button>
            <b-button 
              variant="success" 
              :disabled="politburoMembers.length !== 3 || isSubmittingGov"
              @click="savePolitburoSelection"
              class="me-2"
            >
              {{ isSubmittingGov ? 'Saving...' : 'Save' }}
            </b-button>
            <b-button 
              variant="secondary" 
              @click="cancelPolitburoSelection"
            >
              Cancel
            </b-button>
          </div>

          <div class="text-danger mt-2" v-if="govError">{{ govError }}</div>
        </div>
      </b-modal>
    </b-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { useSocket } from '@/composables/useSocket'
import ClickToEdit from '@/components/helpers/ClickToEdit.vue'
import RoomListService from '@/services/RoomListService'
import WheelSpinner from '@/components/SpinWheel.vue'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js'

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

const store = useStore()
const router = useRouter()
const { socket } = useSocket()

const clock = ref('')
const newComponent = ref(false)
const hover = ref(false)
const roomname = ref('test')
const participants = ref([])
const activePlayers = computed(() => {
  const active = participants.value.filter(p => {
    // Check if clock is "00•00•00" (out of time)
    const isDead = p.clock && p.clock === '00•00•00'
    if (p.clock === '00•00•00') {
      console.log('[activePlayers] Player', p.username, 'has clock:', p.clock, 'isDead:', isDead)
    }
    return !isDead
  })
  console.log('[activePlayers] Computed:', active.length, 'active players')
  return active
})
const droppedPlayers = computed(() => {
  const dropped = participants.value.filter(p => {
    // Dropped if clock is "00•00•00"
    const isDead = p.clock && p.clock === '00•00•00'
    if (isDead) {
      console.log('[droppedPlayers] Player', p.username, 'has clock:', p.clock, 'typeof:', typeof p.clock)
    }
    return isDead
  })
  console.log('[droppedPlayers] Computed:', dropped.length, 'dropped players')
  return dropped
})

// FIX: add missing refs
const roomGovernment = ref(null)
const selectedGovernmentId = ref(null)
const selectedJobId = ref(null)
const selectedPerk = ref(null)

// NEW: track room owner/creator
const roomOwnerId = ref(null)

// History graph modal
const historyGraphModal = ref(null)
const loadingHistory = ref(false)
const historyError = ref(null)
const chartData = ref(null)
const chartOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
    },
    title: {
      display: true,
      text: 'Player Clocks Over Time'
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      title: {
        display: true,
        text: 'Time (minutes)'
      }
    },
    x: {
      title: {
        display: true,
        text: 'Game Time'
      }
    }
  }
})

// Defaults
const defaultGovernments = [
  { id: 1, name: 'Democracy' },
  { id: 2, name: 'Republic' },
  { id: 3, name: 'Dictatorship' },
  { id: 4, name: 'Communism' },
  { id: 5, name: 'Anarchy' }
]

// State
const governments = ref([...defaultGovernments])
const jobs = ref([]) // ensure this exists

// ADD: paying state
const isPaying = ref(false)

// Normalize label for backend or defaults
function govLabel(g) {
  return String(g?.name ?? g?.type ?? g?.label ?? '').trim()
}

// Always provide items with a name for rendering
const displayGovernments = computed(() => {
  const list = governments.value?.length ? governments.value : defaultGovernments
  return list.map((g, idx) => ({
    id: g.id ?? g.value ?? idx + 1,
    name: govLabel(g) || 'Unnamed'
  }))
})

const governmentOptionsDisplay = computed(() => {
  const list = governments.value?.length ? governments.value : defaultGovernments
  return [{ value: null, text: 'Select a government' }, ...list.map(g => ({ value: g.id, text: g.name }))]
})

// ADD: modal refs and busy flags (fixes ReferenceError)
const leaveRoomModal = ref(null)
const removeRoomModal = ref(null)
const wheelSpinnerRef = ref(null)
const politburoWheelModal = ref(null)
const isLeaving = ref(false)
const isRemoving = ref(false)

// Politburo wheel state
const politburoMembers = ref([])
const isSpinningPolitburo = ref(false)
const balanceBooksOnSave = ref(false)
const currentWheelWinner = ref(null)
const showWheelResult = ref(false)

// Available candidates for politburo wheel (exclude already selected members)
const availablePolitburoCandidates = computed(() => {
  return participants.value.filter(p => !politburoMembers.value.includes(p.user_id))
})

// Build select options
const governmentOptions = computed(() => [
  { value: null, text: 'Select a government' },
  ...governments.value.map(g => ({ value: g.id, text: g.name }))
])
const jobOptions = computed(() => [
  { value: null, text: 'Select a job' },
  ...jobs.value.map(j => ({
    value: j.id,
    text: j.tier ? `${j.name} (Tier ${j.tier})` : j.name
  }))
])

// Socket event handlers
socket.on('updateClock', async (data) => {
  // Handle both JSON-encoded and plain string formats
  let newClock
  if (typeof data.data === 'string') {
    try {
      newClock = String(JSON.parse(data.data))
    } catch {
      // If JSON parsing fails, it's already a plain string
      newClock = data.data
    }
  } else {
    newClock = String(data.data)
  }
  
  clock.value = newClock
  
  // Also update the clock in the participants array for the current user
  const currentUserIndex = participants.value.findIndex(p => p.user_id === currentUserId.value)
  if (currentUserIndex !== -1) {
    const updated = [...participants.value]
    updated[currentUserIndex] = {
      ...updated[currentUserIndex],
      clock: newClock
    }
    participants.value = updated
    
    await nextTick()
    console.log('[updateClock] Updated participant clock for current user:', newClock)
    console.log('[updateClock] Participant object:', participants.value[currentUserIndex])
  }
})
socket.on('updateAllClocks', (data) => {
  // Update the current user's clock from the clocks dict
  const clocks = data.clocks
  if (clocks && clocks[currentUserId.value]) {
    clock.value = clocks[currentUserId.value]
    
    // Also update in participants array
    const currentUserIndex = participants.value.findIndex(p => p.user_id === currentUserId.value)
    if (currentUserIndex !== -1) {
      participants.value[currentUserIndex].clock = clocks[currentUserId.value]
    }
  }
  
  // Update all other participants' clocks too
  participants.value.forEach((p, index) => {
    if (clocks[p.user_id]) {
      participants.value[index].clock = clocks[p.user_id]
    }
  })
})
socket.on('userClockUpdate', (data) => {
  // Update any participant's clock when it changes
  const participantIndex = participants.value.findIndex(p => p.user_id === data.user_id)
  if (participantIndex !== -1) {
    participants.value[participantIndex] = {
      ...participants.value[participantIndex],
      clock: data.clock
    }
    // Force reactivity by creating a new array
    participants.value = [...participants.value]
    console.log('[userClockUpdate] Updated clock for user', data.user_id, ':', data.clock)
  }
  
  // If it's the current user, also update their main clock display
  if (data.user_id === currentUserId.value) {
    clock.value = data.clock
  }
})

// Handle targeted job updates
socket.on('userJobUpdate', (data) => {
  const participantIndex = participants.value.findIndex(p => p.user_id === data.user_id)
  if (participantIndex !== -1) {
    participants.value[participantIndex] = {
      ...participants.value[participantIndex],
      job_name: data.job_name,
      job_tier: data.job_tier
    }
    participants.value = [...participants.value]
    console.log('[userJobUpdate] Updated job for user', data.user_id)
  }
})

// Handle targeted perk updates
socket.on('userPerkUpdate', (data) => {
  const participantIndex = participants.value.findIndex(p => p.user_id === data.user_id)
  if (participantIndex !== -1) {
    participants.value[participantIndex] = {
      ...participants.value[participantIndex],
      perk: data.perk
    }
    participants.value = [...participants.value]
    console.log('[userPerkUpdate] Updated perk for user', data.user_id)
  }
})

socket.on('updateRoomId', (data) => {
  store.commit('auth/setRoomId', { id: data.data })
})
socket.on('setUserId', (data) => {
  store.commit('auth/setUserId', data.data)
})
socket.on('UpdateUserStatus', (data) => {
  // backend sends JSON string here
  const room = JSON.parse(data.data)
  participants.value = Array.isArray(room.participants) ? room.participants.map(p => ({
    user_id: p.user_id,
    username: p.username ?? 'Unknown',
    job_name: p.job_name ?? '-',
    job_tier: p.job_tier ?? '-',
    clock: p.clock ?? '00•00•00',
    bleed: p.bleed ?? 0,
    heat: p.heat ?? 0,
    perk: p.perk ?? nullif 
  })) : []
})

// Socket diagnostics: see what arrives
socket.onAny((event, ...args) => {
  if (event === 'userClockUpdate') {
    console.log('[socket:onAny] userClockUpdate received:', args[0])
  }
  console.debug('[socket:onAny] Event received:', event, args)
  if (event === 'updateCollectionData') {
    console.debug('[socket:onAny] updateCollectionData payload:', args[0])
  }
  if (event === 'updateClock') {
    console.debug('[socket:onAny] updateClock payload:', args[0])
  }
})

// Receive collections from server
socket.on('updateCollectionData', (payload) => {
  try {
    const raw = payload?.data ?? payload
    const data = typeof raw === 'string' ? JSON.parse(raw) : raw
    const govs = Array.isArray(data?.governments) ? data.governments : []
    const jbs  = Array.isArray(data?.jobs) ? data.jobs : []

    if (govs.length) {
      // Map to ensure each item has a name
      governments.value = govs.map((g, idx) => ({
        id: g.id ?? g.value ?? idx + 1,
        name: govLabel(g)
      }))
    }
    jobs.value = jbs
  } catch (e) {
    console.error('updateCollectionData parse error', e)
  }
})

socket.on('room_state', (payload) => {
  const room = typeof payload === 'string' ? JSON.parse(payload) : payload
  roomname.value = room?.name || roomname.value

  // NEW: capture owner/creator id from common field names
  roomOwnerId.value =
    room?.owner_id ??
    room?.creator_id ??
    room?.created_by ??
    room?.createdBy ??
    null

  participants.value = Array.isArray(room?.participants) ? room.participants.map(p => ({
    user_id: p.user_id,
    username: p.username ?? 'Unknown',
    job_name: p.job_name ?? '-',
    job_tier: p.job_tier ?? '-',
    clock: p.clock ?? '00•00•00',
    bleed: p.bleed ?? 0,
    heat: p.heat ?? 0,
    perk: p.perk ?? null
  })) : []
  
  // Debug: Check for dropped players
  const dropped = participants.value.filter(p => p.clock === '00•00•00')
  if (dropped.length > 0) {
    console.log('[room_state] Dropped players detected:', dropped.map(p => p.username))
  }
  
  roomGovernment.value = room?.government || null

  // Sync dropdown to current government type if we have collections
  const syncId = findGovernmentIdByName(roomGovernment.value?.type)
  if (syncId !== undefined) selectedGovernmentId.value = syncId

  // Sync current user's perk
  const currentUser = participants.value.find(p => p.user_id === currentUserId.value)
  if (currentUser) {
    selectedPerk.value = currentUser.perk
  }

  console.debug('[room_state] owner:', room?.owner_id || room?.created_by, 'government:', room?.government)
})

onMounted(async () => {
  window.addEventListener('beforeunload', leaveRoom)
  if (!store.state.auth.roomId) {
    router.push({ name: 'Rooms' })
    return
  }

  // Optionally ensure HTTP join is idempotent
  try {
    await RoomListService.joinRoom({ roomId: Number(store.state.auth.roomId) })
  } catch (e) {
    // Already joined or backend will handle; safe to continue
  }

  // IMPORTANT: emit socket "join" so server adds you to the room and broadcasts room_state
  if (socket.connected) {
    console.log('[Room] Emitting socket join')
    socket.emit('join')
  } else {
    socket.once('connect', () => {
      console.log('[Room] Emitting socket join after connect')
      socket.emit('join')
    })
  }

  // Fallback: if collections didn’t arrive shortly after mount, provide defaults
  setTimeout(() => {
    if (!governments.value.length) {
      governments.value = defaultGovernments
    }
  }, 1000)

  // Remove navbar event listeners
  // bus.on('room:leave', openLeaveModal)
  // bus.on('room:end', () => isAdmin.value && openRemoveModal())
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', leaveRoom)
  socket.disconnect()
  // bus.off('room:leave', openLeaveModal)
  // bus.off('room:end')
})

// Open modals
function openLeaveModal() {
  leaveRoomModal.value && leaveRoomModal.value.show()
}
function openRemoveModal() {
  removeRoomModal.value && removeRoomModal.value.show()
}
function openWheelSpinner() {
  wheelSpinnerRef.value?.open()
}

// Replace custom buttons logic with OK handlers that keep the modal open during async
function onLeaveOk(evt) {
  // Keep modal open while we run the async confirmLeave
  if (evt && evt.preventDefault) evt.preventDefault()
  if (isLeaving.value) return
  confirmLeave()
}

function onRemoveOk(evt) {
  if (evt && evt.preventDefault) evt.preventDefault()
  if (isRemoving.value) return
  confirmRemove()
}

// Confirm actions from modals
async function confirmLeave() {
  if (isLeaving.value) return
  const roomId = store.state.auth.roomId
  console.log('[LeaveRoom] OK clicked -> payload:', { roomId })
  isLeaving.value = true
  try {
    socket.emit('leave')
    const resp = await RoomListService.leaveRoom({ roomId })
    console.log('[LeaveRoom] Response:', resp?.status, resp?.data)
    store.commit('auth/leaveRoomId')
    leaveRoomModal.value && leaveRoomModal.value.hide()
    router.push({ name: 'Rooms' })
  } catch (e) {
    console.error('[LeaveRoom] Failed:', e)
  } finally {
    isLeaving.value = false
  }
}

async function confirmRemove() {
  // Instead of immediately removing, fetch history and show graph
  if (isRemoving.value) return
  const roomId = store.state.auth.roomId
  console.log('[RemoveRoom] Fetching game history...')
  
  // Hide the confirmation modal
  removeRoomModal.value && removeRoomModal.value.hide()
  
  // Show history graph modal
  loadingHistory.value = true
  historyError.value = null
  chartData.value = null
  historyGraphModal.value && historyGraphModal.value.show()
  
  try {
    const resp = await RoomListService.getRoomHistory(roomId)
    console.log('[RoomHistory] Response:', resp?.data)
    
    if (resp?.data?.history && resp.data.history.length > 0) {
      // Process history data for Chart.js
      const history = resp.data.history
      
      // Generate color palette for players
      const colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
        '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'
      ]
      
      // Helper function to convert minutes to DD•HH•MM format
      const formatClock = (minutes) => {
        const days = Math.floor(minutes / 1440) // 1440 minutes in a day
        const hours = Math.floor((minutes % 1440) / 60)
        const mins = minutes % 60
        return `${String(days).padStart(2, '0')}•${String(hours).padStart(2, '0')}•${String(mins).padStart(2, '0')}`
      }
      
      const datasets = history.map((playerData, index) => ({
        label: playerData.username,
        data: playerData.snapshots.map(s => ({
          x: new Date(s.timestamp).toLocaleTimeString(),
          y: s.clock_minutes
        })),
        borderColor: colors[index % colors.length],
        backgroundColor: colors[index % colors.length] + '40',
        tension: 0.4
      }))
      
      chartData.value = {
        datasets: datasets
      }
      
      // Update chart options with custom Y-axis formatter
      chartOptions.value = {
        ...chartOptions.value,
        scales: {
          ...chartOptions.value.scales,
          y: {
            ...chartOptions.value.scales.y,
            ticks: {
              callback: function(value) {
                return formatClock(value)
              }
            }
          }
        }
      }
    } else {
      historyError.value = 'No history data available for this game'
    }
  } catch (e) {
    console.error('[RoomHistory] Failed:', e)
    historyError.value = 'Failed to load game history'
  } finally {
    loadingHistory.value = false
  }
}

async function finalizeRemoveRoom() {
  // Actually remove the room after viewing graph
  if (isRemoving.value) return
  const roomId = store.state.auth.roomId
  console.log('[RemoveRoom] Finalizing room removal:', { roomId })
  isRemoving.value = true
  try {
    const resp = await RoomListService.removeRoom({ roomId })
    console.log('[RemoveRoom] Response:', resp?.status, resp?.data)
    store.commit('auth/leaveRoomId')
    historyGraphModal.value && historyGraphModal.value.hide()
    router.push({ name: 'Rooms' })
  } catch (e) {
    console.error('[RemoveRoom] Failed:', e)
  } finally {
    isRemoving.value = false
  }
}

// Keep for beforeunload safety (silent best-effort)
function leaveRoom() {
  try {
    const data = { roomId: store.state.auth.roomId }
    socket.emit('leave')
    store.commit('auth/leaveRoomId')
    RoomListService.leaveRoom(data).catch(() => {})
  } catch {}
}

function changeComponent() {
  newComponent.value = !newComponent.value
}
function uClock(time) {
  socket.emit('updateClock', JSON.stringify(time))
}
function handleHover(s) {
  hover.value = s
}

// Computed
const username = computed(() => store.state.auth.username)
const currentRoomId = computed(() => store.state.auth.roomId)
const currentUserId = computed(() => store.state.auth.userId)

// Admin check: ONLY the room creator can change gov (or leave superuser id 1 if you want)
const isAdmin = computed(() => {
  if (!roomOwnerId.value) return false
  return currentUserId.value === roomOwnerId.value
  // If you also want to allow global admin (id === 1), use:
  // return currentUserId.value === roomOwnerId.value || currentUserId.value === 1
})

const isCommunist = computed(() => {
  const govType = roomGovernment.value?.type
  return govType && String(govType).toLowerCase() === 'communism'
})

// Market actions
function sellConsumable() {
  socket.emit('updateClock', JSON.stringify(30))
}
function sellTimeCounter() {
  socket.emit('updateClock', JSON.stringify(150))
}

// ADD: Get Paid handler -> emits "balanceChange"
function getPaid() {
  if (isPaying.value) return
  isPaying.value = true
  try {
    console.log('[GetPaid] emit balanceChange')
    socket.emit('balanceChange') // no payload needed
  } catch (e) {
    console.error('[GetPaid] emit failed', e)
  } finally {
    setTimeout(() => { isPaying.value = false }, 600)
  }
}

// Government assignment state
const govAssignModal = ref(null)
const isSubmittingGov = ref(false)
const govError = ref('')
const govForm = ref({
  type: null,
  dictator: null,
  head_of_state: null,
  advisors: [],
  politburo: []
})

// Options for selects based on current participants
const participantOptions = computed(() =>
  (participants.value || []).map(p => ({
    value: p.user_id ?? p.userId ?? p.id,
    text: p.username || `User ${p.user_id || p.id}`
  }))
)

// When admin changes government dropdown
function onGovernmentChange() {
  if (!isAdmin.value) {
    selectedGovernmentId.value = findGovernmentIdByName(roomGovernment.value?.type)
    return
  }
  const sel =
    displayGovernments.value.find(g => g.id === selectedGovernmentId.value) ||
    governments.value.find(g => g.id === selectedGovernmentId.value)
  const typeName = govLabel(sel)
  if (!typeName) return

  if (typeName === 'Democracy' || typeName === 'Anarchy') {
    socket.emit('updateGovernment', JSON.stringify({ type: typeName }))
    return
  }

  if (typeName === 'Communism') {
    // Open special politburo wheel modal
    govForm.value = {
      type: 'Communism',
      dictator: null,
      head_of_state: null,
      advisors: [],
      politburo: []
    }
    govError.value = ''
    politburoWheelModal.value && politburoWheelModal.value.show()
    return
  }

  govForm.value = {
    type: typeName,
    dictator: null,
    head_of_state: null,
    advisors: [],
    politburo: []
  }
  govError.value = ''
  govAssignModal.value && govAssignModal.value.show()
}

// IMPORTANT: remove the old watcher that auto-emitted updateGovernment.
// It bypassed the isAdmin check. Keep only job watcher.

watch(selectedJobId, (v) => {
  if (v != null) {
    socket.emit('updateJob', JSON.stringify({ job_id: v }))
  }
})

// Watch for perk changes
watch(selectedPerk, (v) => {
  socket.emit('updatePerk', JSON.stringify({ perk: v }))
})

// Build and emit payload based on govForm
function submitGovernment() {
  if (!isAdmin.value) return
  govError.value = ''

  const t = govForm.value.type
  let payload = { type: t }

  if (t === 'Dictatorship') {
    if (!govForm.value.dictator) {
      govError.value = 'Please select a dictator.'
      return
    }
    payload.dictator = Number(govForm.value.dictator)
  } else if (t === 'Republic') {
    if (!govForm.value.head_of_state || (govForm.value.advisors || []).length !== 2) {
      govError.value = 'Select a head of state and exactly 2 advisors.'
      return
    }
    payload.head_of_state = Number(govForm.value.head_of_state)
    payload.advisors = govForm.value.advisors.slice(0, 2).map(Number)
    // prevent duplicates
    const all = [payload.head_of_state, ...payload.advisors]
    if (new Set(all).size !== 3) {
      govError.value = 'Head of state and advisors must be different people.'
      return
    }
  } else if (t === 'Communism') {
    if ((govForm.value.politburo || []).length !== 3) {
      govError.value = 'Select exactly 3 politburo members.'
      return
    }
    payload.politburo = govForm.value.politburo.slice(0, 3).map(Number)
    if (new Set(payload.politburo).size !== 3) {
      govError.value = 'Politburo members must be different people.'
      return
    }
  }

  isSubmittingGov.value = true
  try {
    socket.emit('updateGovernment', JSON.stringify(payload))
    govAssignModal.value && govAssignModal.value.hide()
  } finally {
    isSubmittingGov.value = false
  }
}

// Find by name OR type (from room_state.government.type)
function findGovernmentIdByName(name) {
  if (!name) return null
  const target = String(name).toLowerCase()
  const g = governments.value.find(x => {
    const a = x?.name ? String(x.name).toLowerCase() : ''
    const b = x?.type ? String(x.type).toLowerCase() : ''
    return a === target || b === target
  })
  return g ? g.id ?? null : null
}

// Map participants helper (tolerant of shapes)
function mapParticipants(list) {
  return Array.isArray(list)
    ? list.map(p => ({
        user_id: p.user_id ?? p.userId ?? p.id,
        username: p.username ?? (p.user && p.user.username) ?? '(unknown)',
        job_name: p.job_name ?? (p.job && p.job.name) ?? '-',
        bleed: p.bleed ?? 0
      }))
    : []
}

// Normalize government payload from backend into role-based sets
function normalizeGovernment(g) {
  const out = {
    type: g?.type ? String(g.type) : null,
    dictator: null,
    head_of_state: null,
    advisors: new Set(),
    politburo: new Set(),
    members: new Set()
  }
  if (!g) return out

  // Common flat fields
  out.dictator = g.leader_id ?? g.leaderId ?? g.dictator_id ?? g.dictatorId ?? null
  out.head_of_state = g.head_of_state_id ?? g.headOfStateId ?? null

  // Generic member ids
  const mIds = g.member_ids ?? g.memberUserIds
  if (Array.isArray(mIds)) mIds.forEach(id => out.members.add(Number(id)))

  // roles map object variants
  const rolesMap = g.roles ?? g.roleMap ?? g.membersByRole
  if (rolesMap) {
    if (rolesMap.dictator != null) out.dictator = Number(rolesMap.dictator)
    const hs = rolesMap.head_of_state ?? rolesMap.headOfState
    if (hs != null) out.head_of_state = Number(hs)
    const adv = rolesMap.advisors ?? rolesMap.advisor ?? []
    ;(Array.isArray(adv) ? adv : [adv]).forEach(id => out.advisors.add(Number(id)))
    const pb = rolesMap.politburo ?? []
    ;(Array.isArray(pb) ? pb : [pb]).forEach(id => out.politburo.add(Number(id)))
  }

  // members array of objects/numbers
  if (Array.isArray(g.members)) {
    for (const m of g.members) {
      if (m && typeof m === 'object') {
        const uid = Number(m.user_id ?? m.userId ?? m.id)
        const role = String(m.role ?? '').toLowerCase()
        if (!Number.isNaN(uid)) {
          out.members.add(uid)
          if (role === 'dictator') out.dictator = uid
          else if (role === 'head_of_state' || role === 'headofstate') out.head_of_state = uid
          else if (role === 'advisor') out.advisors.add(uid)
          else if (role === 'politburo') out.politburo.add(uid)
        }
      } else if (typeof m === 'number' || typeof m === 'string') {
        out.members.add(Number(m))
      }
    }
  }

  return out
}

// Return the correct icon for a participant based on type + role
function iconForParticipant(p) {
  const g = normalizeGovernment(roomGovernment.value)
  if (!g.type) return null

  const type = g.type.toLowerCase()
  const uid = Number(p.user_id ?? p.userId ?? p.id)

  if (type === 'dictatorship') {
    // Only the dictator
    return g.dictator === uid ? '/dictator.png' : null
  }

  if (type === 'republic') {
    // Head of state has its own icon; advisors use republic.png
    if (g.head_of_state === uid) return '/headOfState.png'
    if (g.advisors.has(uid)) return '/republic.png'
    // Fallback: if no roles provided but member flagged, show republic icon
    if (g.members.has(uid)) return '/republic.png'
    return null
  }

  if (type === 'communism') {
    // Politburo members
    if (g.politburo.has(uid)) return '/communism.png'
    // Fallback: if only generic members are provided, treat as politburo for icon purposes
    if (g.members.has(uid) && g.politburo.size === 0) return '/communism.png'
    return null
  }

  // No icons for Democracy/unknown
  return null
}

// Change Bleed (+/- 1) for the current user
function changeBleed(delta) {
  // Get current user's bleed value
  const currentUserData = participants.value.find(p => p.user_id === currentUserId.value)
  if (!currentUserData) return
  
  const currentBleed = typeof currentUserData.bleed === 'number' ? currentUserData.bleed : 0
  const newBleed = currentBleed + delta
  
  console.log('[Bleed] Current:', currentBleed, 'Delta:', delta, 'New would be:', newBleed)
  
  // Enforce strict min/max bounds
  if (newBleed < 0) {
    console.log('[Bleed] Cannot go below 0')
    return
  }
  if (newBleed > 64) {
    console.log('[Bleed] Cannot exceed maximum (64)')
    return
  }
  
  // Backend handles target user; just send the delta
  try {
    socket.emit('updateBleed', JSON.stringify(Number(delta)))
  } catch (e) {
    console.error('[Bleed] emit failed', e)
  }
}

// Change Heat (+/- 1) for the current user
function changeHeat(delta) {
  // Get current user's heat value
  const currentUserData = participants.value.find(p => p.user_id === currentUserId.value)
  if (!currentUserData) return
  
  const currentHeat = typeof currentUserData.heat === 'number' ? currentUserData.heat : 0
  const newHeat = currentHeat + delta
  
  console.log('[Heat] Current:', currentHeat, 'Delta:', delta, 'New would be:', newHeat)
  
  // Enforce strict min/max bounds
  if (newHeat < 0) {
    console.log('[Heat] Cannot go below 0')
    return
  }
  if (newHeat > 10) {
    console.log('[Heat] Cannot exceed maximum (10)')
    return
  }
  
  try {
    socket.emit('updateHeat', JSON.stringify(Number(delta)))
  } catch (e) {
    console.error('[Heat] emit failed', e)
  }
}

// Return perk icon for a participant
function perkIconForParticipant(p) {
  const perk = p.perk
  if (!perk) return null
  
  if (perk === 'Manager') return '/manager.png'
  if (perk === 'Senior') return '/senior.png'
  if (perk === 'Executive') return '/executive.png'
  
  return null
}

// Politburo wheel functions
const politburoWheelRef = ref(null)

function spinForNextMember() {
  if (politburoMembers.value.length >= 3 || isSpinningPolitburo.value) return
  
  if (!politburoWheelRef.value) {
    console.error('[Politburo] Wheel ref not available')
    return
  }
  
  isSpinningPolitburo.value = true
  
  // Open the wheel modal and trigger the spin
  politburoWheelRef.value.open()
  
  // Small delay to ensure modal is open, then trigger spin
  setTimeout(() => {
    politburoWheelRef.value.spinWheel()
    isSpinningPolitburo.value = false
  }, 100)
}

function addToPolitburo() {
  // Get the winner directly from the wheel component
  const winnerName = politburoWheelRef.value?.winner
  if (!winnerName) return
  
  const participant = participants.value.find(p => 
    p.username === winnerName || 
    (p.username && p.username.toString() === winnerName.toString())
  )
  
  if (!participant || !participant.user_id) {
    console.error('[Politburo] Could not find participant for winner:', winnerName)
    return
  }
  
  // Avoid duplicates
  if (!politburoMembers.value.includes(participant.user_id)) {
    politburoMembers.value.push(participant.user_id)
    console.log('[Politburo] Added member:', participant.username, 'ID:', participant.user_id)
  } else {
    console.log('[Politburo] Member already in list:', participant.username)
  }
  
  // Close the wheel modal
  politburoWheelRef.value?.wheelModal?.hide()
}

function spinAgain() {
  // Close current wheel modal and spin again
  politburoWheelRef.value?.wheelModal?.hide()
  
  setTimeout(() => {
    spinForNextMember()
  }, 300)
}

function resetPolitburoSelection() {
  politburoMembers.value = []
  balanceBooksOnSave.value = false
  govError.value = ''
  showWheelResult.value = false
  currentWheelWinner.value = null
}

function cancelPolitburoSelection() {
  resetPolitburoSelection()
  politburoWheelModal.value && politburoWheelModal.value.hide()
}

function savePolitburoSelection() {
  if (politburoMembers.value.length !== 3) {
    govError.value = 'Must select exactly 3 politburo members'
    return
  }
  
  isSubmittingGov.value = true
  govError.value = ''
  
  const payload = {
    type: 'Communism',
    politburo: politburoMembers.value
  }
  
  try {
    socket.emit('updateGovernment', JSON.stringify(payload))
    
    // If balance books is checked, wait for government update then balance
    if (balanceBooksOnSave.value) {
      // Wait longer to ensure government is saved first
      setTimeout(() => {
        console.log('[Politburo] Triggering balance books')
        socket.emit('balanceBooks')
      }, 1000)
    }
    
    politburoWheelModal.value && politburoWheelModal.value.hide()
    
    // Don't reset immediately if we're balancing books
    if (!balanceBooksOnSave.value) {
      resetPolitburoSelection()
    } else {
      // Reset after balance books completes
      setTimeout(() => {
        resetPolitburoSelection()
      }, 1500)
    }
  } catch (e) {
    console.error('[Politburo] Save failed', e)
    govError.value = 'Failed to save politburo selection'
  } finally {
    setTimeout(() => {
      isSubmittingGov.value = false
    }, balanceBooksOnSave.value ? 1500 : 0)
  }
}

function shareTheWealth() {
  if (!isCommunist.value) return
  socket.emit('balanceBooks')
}
</script>

<style>
.dropped-table {
  opacity: 0.6;
}

.dropped-row {
  text-decoration: line-through;
  background-color: #f8f9fa !important;
}

.emptyButton{
  width: 62px;
  height: 45px;
  text-align: left;
}

.addremovebutton
{
  width: 52px;
  height: 45px;
  text-align: left;
}

.addremovebuttonClock{
  width: 52px;
  height: 45px;
  text-align: left;
  margin-right:0px
}

.itemRow{
  height: 118px;
  text-align: center;
}

.itemRowButtons{
  height: 75px;
}

.itemRowButtonsClock{
  height: 75px;
}

.itemRowPlayers{
  height: 150px;
  padding-right:40px;
  padding-left:40px;
  margin-top: 40px; /* adjust to taste: 16–32px */
}

/* Fixed header row height */
.table thead tr {
  height: 50px;
}

.table thead th {
  vertical-align: middle;
  height: 50px;
}

.intselect {
  text-align: center;
}
ul {
  list-style-type: none;
  text-align: center;
}

.clock-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px; /* space between button groups */
  margin-top: 16px;
  margin-bottom: 16px;
}

.center-row {
  display: flex;
  justify-content: center;
  align-items: center;
}
.dropdowns {
  flex-wrap: wrap;
  gap: 12px;
}
.dropdown-w {
  min-width: 240px;   /* existing size, unchanged */
}

/* Keep both groups aligned and same spacing */
.control-group,
.job-controls,
.perk-controls {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.control-group { margin-right: 12px; }
.job-controls { margin-right: 12px; }

.perk-label {
  font-weight: 500;
  font-size: 14px;
  margin: 0;
  line-height: 38px;
}

.perk-btn {
  padding: 8px 12px;
  border: 2px solid #ddd;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: #555;
  height: 38px;
  min-width: 38px;
}

.perk-btn:hover {
  border-color: #999;
  background: #f8f9fa;
  transform: translateY(-1px);
}

.perk-btn.active {
  border-color: #007bff;
  background: #007bff;
  color: white;
  font-weight: 600;
}

.perk-btn-icon {
  height: 22px;
  width: auto;
  vertical-align: middle;
}

/* Optional: make labels align visually with the 38px control height */
.dropdowns label {
  margin: 0;
  line-height: 38px;
}

.market-controls {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-bottom: 24px;
}
.market-btn { min-width: 200px; }

/* Icons next to usernames (slightly larger) */
.gov-icon {
  height: 28px; /* increased size */
  width: auto;
  margin-left: 6px;
  vertical-align: middle;
  display: inline-block;
}

@media (min-width: 1200px) {
  .gov-icon { height: 40px; } /* a bit larger on big screens */
}

/* Optional: tiny baseline tweak for better alignment */
td > .gov-icon { transform: translateY(-1px); }

.btn-paid {
  min-width: 130px;
  width: 130px;       /* fixed width prevents layout shift */
  height: 38px;       /* align with select height */
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.bleed-header,
.heat-header {
  text-align: center;
  vertical-align: middle;
}
.bleed-header-inner,
.heat-header-inner {
  display: inline-flex;          /* keeps width snug while centered in th */
  align-items: center;           /* vertical alignment */
  justify-content: center;       /* horizontal centering */
  gap: 8px;                      /* space around label */
}

.bleed-label,
.heat-label {
  font-weight: 700;
  line-height: 28px;             /* match button height for perfect baseline */
}

.bleed-btn,
.heat-btn {
  width: 28px;
  height: 28px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  font-weight: 700;
  border-width: 1px;
}

/* optional: small spacing tweaks */
.bleed-btn-minus { margin-right: 2px; }
.bleed-btn-plus  { margin-left: 2px; }
.heat-btn-minus { margin-right: 2px; }
.heat-btn-plus  { margin-left: 2px; }

/* center the values in the Bleed and Heat columns */
.table td:nth-child(3) { text-align: center; }
.table td:nth-child(4) { text-align: center; }

/* Fixed row height for consistent sizing */
.table tbody tr {
  height: 60px;
}

.table tbody td {
  vertical-align: middle;
  height: 60px;
}

/* Fixed column widths to prevent resizing */
.table th:nth-child(1),
.table td:nth-child(1) {
  width: 200px;
  min-width: 200px;
}

.table th:nth-child(2),
.table td:nth-child(2) {
  width: 250px;
  min-width: 250px;
}

.table th:nth-child(3),
.table td:nth-child(3) {
  width: 120px;
  min-width: 120px;
}

.table th:nth-child(4),
.table td:nth-child(4) {
  width: 120px;
  min-width: 120px;
}

/* Perk icons inline with job titles */
.perk-icon {
  height: 40px;
  width: auto;
  margin-right: 8px;
  vertical-align: middle;
  display: inline-block;
}

@media (min-width: 1200px) {
  .perk-icon { height: 40px; }
}

/* optional: small spacing tweak */
.bleed-btn-minus { margin-right: 2px; }
.bleed-btn-plus  { margin-left: 2px; }

.top-actions {
  display: flex;
  justify-content: center;
  align-items: center;
}

/* Space between the buttons */
.top-actions-group { gap: 10px; } /* modern browsers */
.top-actions-group > .btn + .btn { margin-left: 10px; } /* fallback */

/* Politburo selection modal styles */
.politburo-selection {
  padding: 20px;
}

.wheel-container-politburo {
  display: flex;
  justify-content: center;
  min-height: 400px;
}

.selected-members {
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.member-list {
  margin-top: 10px;
}

.politburo-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}

.wheel-result {
  text-align: center;
}

.wheel-result .alert {
  margin: 0;
}

.result-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
}
</style>