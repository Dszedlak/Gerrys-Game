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
          <!-- FIX: correct component tag -->
          <ClickToEdit id="clock" :value="clock" action="updateClock" />
        </b-col>
      </b-row>
      <b-row class="justify-content-center">
        <b-col cols="12">
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
      </b-row>

      <!-- Get Paid Button Section -->
      <b-row class="mt-3 mb-3">
        <b-col>
          <div class="center-row">
            <b-button
              class="btn-get-paid"
              variant="warning"
              :disabled="isPaying"
              @click="getPaid"
              title="Request pay based on your current job"
            >
              {{ isPaying ? 'Getting Paid…' : 'Get Paid' }}
            </b-button>
          </div>
        </b-col>
      </b-row>

      <!-- Senate Controls and Government Selection -->
      <b-row class="mt-2 mb-2 align-items-center">
        <b-col>
          <div class="govt-row dropdowns">
            <div class="control-group">
              <span v-if="!isAdmin" class="govt-label">Government: <strong>{{ currentGovernmentName }}</strong></span>
              <div v-else class="govt-dropdown-wrapper">
                <label for="govSelect" class="mr-2">Government:</label>
                <div class="govt-select-box">
                  <select
                    id="govSelect"
                    v-model="selectedGovernmentId"
                    class="dropdown-w form-control"
                    @change="onGovernmentChange"
                  >
                    <option :value="null">Select a government</option>
                    <option v-for="g in displayGovernments" :key="g.id" :value="g.id">
                      {{ g.name }}
                    </option>
                  </select>
                  <span class="govt-arrow">▼</span>
                </div>
              </div>
            </div>
          </div>
        </b-col>
      </b-row>

      <!-- Participants table -->
      <div style="display: flex; justify-content: center; width: 100%; margin-top: 30px; margin-bottom: 30px;">
        <div style="width: 95%; max-width: 1400px;">
        <table class="table table-sm table-bordered" style="width:100%">
            <thead>
              <tr>
                <th class="username-header">Username</th>
                <th class="job-title-header">
                  <select
                    id="jobSelect"
                    v-model="selectedJobId"
                    class="job-header-select"
                  >
                    <option :value="null">Select a job</option>
                    <option v-for="j in jobs" :key="j.id" :value="j.id">
                      {{ j.tier ? `${j.name} (Tier ${j.tier})` : j.name }}
                    </option>
                  </select>
                  <span class="job-title-text">Job Title <span class="job-title-arrow">▼</span></span>
                </th>
                <th class="perk-title-header">
                  <select
                    id="perkSelect"
                    v-model="selectedPerk"
                    class="perk-header-select"
                  >
                    <option :value="null">None</option>
                    <option value="Manager">Manager</option>
                    <option value="Senior">Senior</option>
                    <option value="Executive">Executive</option>
                  </select>
                  <span class="perk-title-text">Perk <span class="perk-title-arrow">▼</span></span>
                </th>
                <th class="approval-title-header">
                  <select
                    id="approvalHeaderSelect"
                    v-model="selectedHeaderApproval"
                    @change="onHeaderApprovalChange"
                    class="approval-header-select"
                  >
                    <option :value="null">Select status</option>
                    <option value="approve">Approve</option>
                    <option value="disapprove">Disapprove</option>
                    <option value="abstain">Abstain</option>
                  </select>
                  <span class="approval-title-text">Approval <span class="approval-title-arrow">▼</span></span>
                </th>
                <th class="vote-title-header">
                  <select
                    id="voteHeaderSelect"
                    v-model="selectedHeaderVote"
                    @change="onHeaderVoteChange"
                    class="vote-header-select"
                  >
                    <option :value="null">Select vote</option>
                    <option value="yes">Yes</option>
                    <option value="no">No</option>
                    <option value="abstain">Abstain</option>
                  </select>
                  <span class="vote-title-text">Vote <span class="vote-title-arrow">▼</span></span>
                </th>
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
                </td>
                <td class="perk-column">
                  <img
                    v-if="perkIconForParticipant(p)"
                    :src="perkIconForParticipant(p)"
                    class="perk-icon"
                    :alt="p.perk"
                  />
                </td>
                <td class="approval-cell">
                  <span v-if="p.approval_status && p.user_id === currentUserId" @click="clearApprovalStatus" class="approval-badge" :class="'approval-' + p.approval_status" style="cursor: pointer;">{{ p.approval_status }}</span>
                  <span v-else-if="p.approval_status" class="approval-badge" :class="'approval-' + p.approval_status">{{ p.approval_status }}</span>
                  <span v-else class="approval-badge approval-empty">—</span>
                </td>
                <td class="vote-cell">
                  <span v-if="p.gov_vote && p.user_id === currentUserId" @click="clearGovVote" class="vote-badge" :class="'vote-' + p.gov_vote" style="cursor: pointer;">{{ p.gov_vote }}</span>
                  <span v-else-if="p.gov_vote" class="vote-badge" :class="'vote-' + p.gov_vote">{{ p.gov_vote }}</span>
                  <span v-else class="vote-badge vote-empty">—</span>
                </td>
                <td>{{ p.bleed }}</td>
                <td>{{ p.heat }}</td>
              </tr>
              <tr v-if="!activePlayers.length">
                <td colspan="7" class="text-center">No participants yet</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Dropped Players table -->
      <b-row v-if="droppedPlayers.length > 0" class="itemRowPlayers mt-3">
        <b-col></b-col>
        <b-col cols="4">
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

      <!-- Approval Status Modal -->
      <b-modal
        id="approvalStatusModal"
        ref="approvalStatusModal"
        title="Set Approval Status"
        @ok="confirmApprovalStatus"
        ok-title="Submit"
        cancel-title="Cancel"
      >
        <div class="mb-3">
          <label for="approvalSelect" class="form-label">Choose your approval status:</label>
          <select v-model="selectedApprovalOption" id="approvalSelect" class="form-select">
            <option :value="null">-- Select --</option>
            <option value="approve">Approve</option>
            <option value="disapprove">Disapprove</option>
            <option value="abstain">Abstain</option>
          </select>
        </div>
      </b-modal>

      <!-- Government Vote Modal -->
      <b-modal
        id="govVoteModal"
        ref="govVoteModal"
        title="Cast Your Vote"
        @ok="confirmGovVote"
        ok-title="Submit"
        cancel-title="Cancel"
      >
        <div class="mb-3">
          <label for="voteSelect" class="form-label">Choose your vote:</label>
          <select v-model="selectedVoteOption" id="voteSelect" class="form-select">
            <option :value="null">-- Select --</option>
            <option value="yes">Yes</option>
            <option value="no">No</option>
            <option value="abstain">Abstain</option>
          </select>
        </div>
      </b-modal>

      <!-- Dictator Bidding Modal -->
      <b-modal
        id="dictatorBiddingModal"
        ref="dictatorBiddingModal"
        title="Dictator Auction - Place Your Bid"
        hide-footer
        no-close-on-backdrop
        no-close-on-esc
        size="lg"
      >
        <div class="dictator-bid-container">
          <!-- Time Display -->
          <div class="bid-display-section mb-4">
            <p class="bid-instruction">Bid for the right to be the Dictator!</p>
            <div class="bid-time-big">
              {{ String(Math.floor(bidTimeMinutes / 60)).padStart(2, '0') }}:{{ String(bidTimeMinutes % 60).padStart(2, '0') }}
            </div>
          </div>

          <!-- Time Control Buttons -->
          <div class="bid-buttons-section mb-4">
            <div class="bid-button-row mb-2">
              <b-button size="lg" variant="outline-danger" @click="bidTimeMinutes = Math.max(0, bidTimeMinutes - 60)" class="bid-btn">-1h</b-button>
              <b-button size="lg" variant="outline-danger" @click="bidTimeMinutes = Math.max(0, bidTimeMinutes - 30)" class="bid-btn">-30</b-button>
              <b-button size="lg" variant="outline-danger" @click="bidTimeMinutes = Math.max(0, bidTimeMinutes - 20)" class="bid-btn">-20</b-button>
              <b-button size="lg" variant="outline-danger" @click="bidTimeMinutes = Math.max(0, bidTimeMinutes - 10)" class="bid-btn">-10</b-button>
            </div>
            <div class="bid-button-row">
              <b-button size="lg" variant="outline-success" @click="bidTimeMinutes = bidTimeMinutes + 10" class="bid-btn">+10</b-button>
              <b-button size="lg" variant="outline-success" @click="bidTimeMinutes = bidTimeMinutes + 20" class="bid-btn">+20</b-button>
              <b-button size="lg" variant="outline-success" @click="bidTimeMinutes = bidTimeMinutes + 30" class="bid-btn">+30</b-button>
              <b-button size="lg" variant="outline-success" @click="bidTimeMinutes = bidTimeMinutes + 60" class="bid-btn">+1h</b-button>
            </div>
          </div>

          <!-- Place Bid Button -->
          <b-button variant="primary" size="lg" @click="placeDictatorBid" class="w-100 mb-4 place-bid-btn">
            <strong>Place Bid</strong>
          </b-button>

          <!-- Bidding Status -->
          <div class="bidding-status-section">
            <h6 class="mb-3">Bidding Status:</h6>
            <div class="bidding-tally">
              <div v-for="participant in participants" :key="participant.user_id" class="tally-item">
                <span class="participant-name">{{ participant.username }}</span>
                <span v-if="biddingTally[participant.user_id]" class="badge bg-success">✓ Bid Placed</span>
                <span v-else class="badge bg-warning text-dark">⏳ Awaiting Bid</span>
              </div>
            </div>
          </div>

          <!-- Admin Conclude Button -->
          <div v-if="isAdmin" class="admin-section mt-4 pt-4 border-top">
            <b-button variant="success" size="lg" @click="concludeDictatorBidding" class="w-100">
              <strong>Conclude Bidding</strong>
            </b-button>
          </div>
        </div>
      </b-modal>

      <!-- Dictator Bidding Winner Modal -->
      <b-modal
        id="dictatorBiddingWinnerModal"
        ref="dictatorBiddingWinnerModal"
        title="Auction Results"
        hide-footer
        centered
      >
        <div class="text-center">
          <h3 class="mb-3">SOLD!</h3>
          <p class="lead">To the highest bidder:</p>
          <h2 class="text-success mb-4">{{ dictatorWinner }}</h2>
          <p class="text-muted">The winner has been crowned Dictator!</p>
          <div class="mt-4 d-flex justify-content-end">
            <b-button variant="primary" size="sm" @click="dictatorBiddingWinnerModal?.hide()">OK</b-button>
          </div>
        </div>
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
        title="Game History - Clock Tracking (includes Government, Job, Bleed, Heat, Perk)"
        size="xl"
        body-class="p-4"
      >
        <div v-if="loadingHistory" class="text-center">
          <p>Loading game history...</p>
        </div>
        <div v-else-if="historyError" class="alert alert-danger">
          {{ historyError }}
        </div>
        <div v-else-if="chartData" style="height: 500px;">
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
    // Check if clock is "00•00•00" (out of time) or player is dead
    if (!p || !p.clock) return true // include if no clock info
    const isDead = String(p.clock).trim() === '00•00•00'
    return !isDead
  })
  
  // Sort so current user is always at the top
  const sorted = active.sort((a, b) => {
    if (a.user_id === currentUserId.value) return -1
    if (b.user_id === currentUserId.value) return 1
    return 0
  })
  
  console.log('[activePlayers] Filtered:', sorted.length, 'active from', participants.value.length, 'total')
  return sorted
})
const droppedPlayers = computed(() => {
  const dropped = participants.value.filter(p => {
    // Dropped if clock is "00•00•00" or player is dead
    if (!p || !p.clock) return false // exclude if no clock info
    const isDead = String(p.clock).trim() === '00•00•00'
    return isDead
  })
  
  // Sort so current user is always at the top
  const sorted = dropped.sort((a, b) => {
    if (a.user_id === currentUserId.value) return -1
    if (b.user_id === currentUserId.value) return 1
    return 0
  })
  
  console.log('[droppedPlayers] Filtered:', sorted.length, 'dropped players')
  return sorted
})

// FIX: add missing refs
const roomGovernment = ref(null)
const selectedGovernmentId = ref(null)
const selectedJobId = ref(null)
const selectedPerk = ref(null)
const selectedHeaderApproval = ref(null)
const selectedHeaderVote = ref(null)

// NEW: track room owner/creator
const roomOwnerId = ref(null)

// History graph modal
const historyGraphModal = ref(null)
const loadingHistory = ref(false)
const historyError = ref(null)
const chartData = ref(null)
const selectedPlayersForGraph = ref([])
const allGraphPlayers = ref([])
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
const approvalStatusModal = ref(null)
const govVoteModal = ref(null)
const isLeaving = ref(false)
const isRemoving = ref(false)
const showVoteColumn = ref(true)
const selectedApprovalOption = ref(null)
const selectedVoteOption = ref(null)

// Dictator bidding state
const dictatorBiddingModal = ref(null)
const dictatorBiddingWinnerModal = ref(null)
const biddingActive = ref(false)
const biddingTally = ref({}) // { userId: true/false indicating if they've bid }
const currentUserBid = ref(null)
const bidTimeMinutes = ref(0)
const dictatorWinner = ref(null)
const concludeBiddingModal = ref(null)

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
    job_name: p.job_name ?? 'Unemployed',
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

  // Sync current user's perk and clock
  const currentUser = participants.value.find(p => p.user_id === currentUserId.value)
  if (currentUser) {
    selectedPerk.value = currentUser.perk
    clock.value = currentUser.clock // Update the main clock display
  }

  console.debug('[room_state] owner:', room?.owner_id || room?.created_by, 'government:', room?.government)
})

// Senate event listeners
socket.on('approvalStatusUpdated', (data) => {
  console.log('[approvalStatusUpdated]', data)
  // Update participant approval status in the UI
  const participant = participants.value.find(p => p.user_id === data.user_id)
  if (participant) {
    participant.approval_status = data.status
  }
})

socket.on('voteRecorded', (data) => {
  console.log('[voteRecorded]', data)
  // Update participant government vote in the UI
  const participant = participants.value.find(p => p.user_id === data.user_id)
  if (participant) {
    participant.gov_vote = data.vote
  }
})

socket.on('startDictatorBidding', (data) => {
  console.log('[startDictatorBidding] Bidding started')
  biddingActive.value = true
  biddingTally.value = {}
  currentUserBid.value = null
  bidTimeMinutes.value = 0
  
  // Initialize tally with all participants
  participants.value.forEach(p => {
    biddingTally.value[p.user_id] = false
  })
  
  // Open bidding modal for all players
  dictatorBiddingModal.value && dictatorBiddingModal.value.show()
})

socket.on('biddingTallyUpdate', (data) => {
  console.log('[biddingTallyUpdate]', data)
  biddingTally.value = data.tally || {}
})

socket.on('dictatorWinner', (data) => {
  console.log('[dictatorWinner]', data)
  biddingActive.value = false
  dictatorWinner.value = data.winner_name
  dictatorBiddingModal.value && dictatorBiddingModal.value.hide()
  
  // Add a small delay to ensure room_state is processed before showing winner modal
  setTimeout(() => {
    dictatorBiddingWinnerModal.value && dictatorBiddingWinnerModal.value.show()
  }, 100)
})

onMounted(async () => {
  // Don't delete participant data on page refresh/reload - participants should persist
  // window.addEventListener('beforeunload', leaveRoom)
  
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
    console.log('[Room] Emitting socket join with roomId:', store.state.auth.roomId)
    socket.emit('join', { roomId: Number(store.state.auth.roomId) })
  } else {
    socket.once('connect', () => {
      console.log('[Room] Emitting socket join after connect with roomId:', store.state.auth.roomId)
      socket.emit('join', { roomId: Number(store.state.auth.roomId) })
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
  // Don't remove listener since we're not adding it anymore
  // window.removeEventListener('beforeunload', leaveRoom)
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
      
      // Track all players for filter
      allGraphPlayers.value = history.map(h => h.username)
      // Select all players by default
      selectedPlayersForGraph.value = [...allGraphPlayers.value]
      
      // Helper function to convert minutes to DD•HH•MM format
      const formatClock = (minutes) => {
        const days = Math.floor(minutes / 1440) // 1440 minutes in a day
        const hours = Math.floor((minutes % 1440) / 60)
        const mins = minutes % 60
        return `${String(days).padStart(2, '0')}•${String(hours).padStart(2, '0')}•${String(mins).padStart(2, '0')}`
      }
      
      // Calculate game start time from first snapshot
      let gameStartTime = null
      if (history.length > 0 && history[0].snapshots.length > 0) {
        gameStartTime = new Date(history[0].snapshots[0].timestamp).getTime()
      }
      
      const datasets = history.map((playerData, index) => ({
        label: playerData.username,
        data: playerData.snapshots.map((s, idx) => {
          // Calculate relative time in minutes from game start
          const snapshotTime = new Date(s.timestamp).getTime()
          const relativeMinutes = Math.round((snapshotTime - gameStartTime) / 60000)
          return {
            x: `${Math.floor(relativeMinutes / 60)}h ${relativeMinutes % 60}m`,
            y: s.clock_minutes,
            timestamp: s.timestamp,
            bleed: s.bleed,
            heat: s.heat,
            job_name: s.job_name,
            perk: s.perk,
            government_type: s.government_type,
            government_role: s.government_role
          }
        }),
        borderColor: colors[index % colors.length],
        backgroundColor: colors[index % colors.length] + '40',
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 5
      }))
      
      chartData.value = {
        datasets: datasets
      }
      
      // Update chart options with custom Y-axis formatter, tooltip formatter, and zoom plugin
      chartOptions.value = {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false
        },
        plugins: {
          legend: {
            position: 'top',
            labels: {
              usePointStyle: true,
              padding: 15
            }
          },
          title: {
            display: true,
            text: 'Player Clocks Over Time',
            font: { size: 16, weight: 'bold' }
          },
          tooltip: {
            backgroundColor: 'rgba(0,0,0,0.9)',
            padding: 12,
            titleFont: { size: 12, weight: 'bold' },
            bodyFont: { size: 10 },
            displayColors: true,
            callbacks: {
              title: function(context) {
                if (context.length > 0) {
                  return context[0].dataset.label
                }
                return ''
              },
              label: function(context) {
                const timeValue = context.parsed.y
                const minutesValue = Math.round(timeValue)
                const formattedTime = formatClock(minutesValue)
                return `Time: ${formattedTime} (${minutesValue} mins)`
              },
              afterLabel: function(context) {
                const point = context.raw
                const lines = []
                
                // Add real-world time
                if (point.timestamp) {
                  const realTime = new Date(point.timestamp)
                  lines.push(`Real Time: ${realTime.toLocaleTimeString()}`)
                }
                
                // Add government info
                if (point.government_type) {
                  let govInfo = `Gov: ${point.government_type}`
                  if (point.government_role) {
                    govInfo += ` (${point.government_role})`
                  }
                  lines.push(govInfo)
                } else {
                  lines.push('Gov: None')
                }
                
                // Add job info
                lines.push(`Job: ${point.job_name || 'None'}`)
                
                // Add perk info
                lines.push(`Perk: ${point.perk || 'None'}`)
                
                // Add bleed/heat
                lines.push(`Bleed: ${point.bleed}, Heat: ${point.heat}`)
                
                return lines
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Time (DD•HH•MM)'
            },
            ticks: {
              callback: function(value) {
                return formatClock(value)
              }
            }
          },
          x: {
            title: {
              display: true,
              text: 'Game Time'
            },
            ticks: {
              maxRotation: 45,
              minRotation: 0
            }
          }
        },
        animation: {
          duration: 0
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

// Graph filtering and formatting
const filteredChartData = computed(() => {
  if (!chartData.value || !chartData.value.datasets) return chartData.value
  
  const newData = {
    ...chartData.value,
    datasets: chartData.value.datasets.filter(dataset => {
      if (selectedPlayersForGraph.value.length === 0) return true // Show all if none selected
      return selectedPlayersForGraph.value.includes(dataset.label)
    })
  }
  return newData
})

function togglePlayerFilter(playerName) {
  const index = selectedPlayersForGraph.value.indexOf(playerName)
  if (index > -1) {
    selectedPlayersForGraph.value.splice(index, 1)
  } else {
    selectedPlayersForGraph.value.push(playerName)
  }
  selectedPlayersForGraph.value = [...selectedPlayersForGraph.value] // Trigger reactivity
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

const currentGovernmentName = computed(() => {
  const govt = displayGovernments.value?.find(g => g.id === selectedGovernmentId.value)
  return govt?.name || 'Unknown'
})

const isCommunist = computed(() => {
  const govType = roomGovernment.value?.type
  return govType && String(govType).toLowerCase() === 'communism'
})

// Senate actions
function setApprovalStatus() {
  console.log('Opening approval status modal')
  selectedApprovalOption.value = null
  approvalStatusModal.value?.show()
}

function confirmApprovalStatus() {
  if (selectedApprovalOption.value) {
    console.log('Setting approval status to:', selectedApprovalOption.value)
    socket.emit('setApprovalStatus', JSON.stringify({ status: selectedApprovalOption.value }))
    approvalStatusModal.value?.hide()
  }
}

function openApprovalModal() {
  setApprovalStatus()
}

function clearApprovalStatus() {
  console.log('Clearing approval status')
  const participant = participants.value.find(p => p.user_id === currentUserId.value)
  if (participant) {
    participant.approval_status = null
  }
  socket.emit('setApprovalStatus', JSON.stringify({ status: null }))
}

function partakeGovVote() {
  console.log('Opening government vote modal')
  selectedVoteOption.value = null
  showVoteColumn.value = true
  govVoteModal.value?.show()
}

function confirmGovVote() {
  if (selectedVoteOption.value) {
    console.log('Casting vote:', selectedVoteOption.value)
    socket.emit('partakeGovVote', JSON.stringify({ choice: selectedVoteOption.value }))
    govVoteModal.value?.hide()
  }
}

function openVoteModal() {
  partakeGovVote()
}

function clearGovVote() {
  console.log('Clearing government vote')
  const participant = participants.value.find(p => p.user_id === currentUserId.value)
  if (participant) {
    participant.gov_vote = null
  }
  socket.emit('partakeGovVote', JSON.stringify({ choice: null }))
}

function onHeaderApprovalChange() {
  if (selectedHeaderApproval.value) {
    console.log('Setting approval status from header:', selectedHeaderApproval.value)
    socket.emit('setApprovalStatus', JSON.stringify({ status: selectedHeaderApproval.value }))
    const participant = participants.value.find(p => p.user_id === currentUserId.value)
    if (participant) {
      participant.approval_status = selectedHeaderApproval.value
    }
    selectedHeaderApproval.value = null
  }
}

function onHeaderVoteChange() {
  if (selectedHeaderVote.value) {
    console.log('Setting vote from header:', selectedHeaderVote.value)
    socket.emit('partakeGovVote', JSON.stringify({ choice: selectedHeaderVote.value }))
    const participant = participants.value.find(p => p.user_id === currentUserId.value)
    if (participant) {
      participant.gov_vote = selectedHeaderVote.value
    }
    selectedHeaderVote.value = null
  }
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

  if (typeName === 'Dictatorship') {
    // Start dictator bidding process
    biddingActive.value = true
    biddingTally.value = {}
    currentUserBid.value = null
    bidTimeMinutes.value = 0
    
    // Initialize tally with all participants
    participants.value.forEach(p => {
      biddingTally.value[p.user_id] = false
    })
    
    // Broadcast to all players to open bidding modal
    socket.emit('startDictatorBidding', JSON.stringify({ initiatedBy: currentUserId.value }))
    
    // Open bidding modal for admin
    dictatorBiddingModal.value && dictatorBiddingModal.value.show()
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

// Dictator bidding functions
function placeDictatorBid() {
  if (bidTimeMinutes.value <= 0) {
    alert('Please enter a valid bid amount (greater than 0)')
    return
  }
  
  console.log('[placeDictatorBid] Bidding:', bidTimeMinutes.value, 'minutes')
  socket.emit('placeDictatorBid', JSON.stringify({ bid_amount: bidTimeMinutes.value }))
  
  // Reset time input
  bidTimeMinutes.value = 0
}

function concludeDictatorBidding() {
  if (!isAdmin.value) return
  
  // Check if all participants have bid
  const allBiddersCount = Object.values(biddingTally.value).filter(v => v === true).length
  const totalParticipants = participants.value.length
  
  if (allBiddersCount !== totalParticipants) {
    alert('All members must bid before concluding the bidding process')
    return
  }
  
  console.log('[concludeDictatorBidding] Concluding bidding')
  socket.emit('concludeDictatorBidding', JSON.stringify({}))
}

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
  const winnerData = politburoWheelRef.value?.winner
  if (!winnerData) return
  
  // Winner is now an object with {text, value} where value is the user_id
  const userId = winnerData.value || winnerData
  const winnerName = winnerData.text || winnerData
  
  const participant = participants.value.find(p => p.user_id === userId)
  
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
#app {
  background: #0a0e27;
  padding: 0;
}

.bv-example-row {
  width: 100% !important;
  max-width: 100% !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
}

/* Remove nested box styling */
.top-actions {
  display: flex;
  justify-content: center;
  margin-bottom: 0;
  margin-top: 0;
}

.top-actions-group { 
  gap: 10px;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  background: transparent;
  padding: 0;
  box-shadow: none;
}

.top-actions-group .butt {
  background: #0f1535 !important;
  border: 2px solid #00dd33 !important;
  color: #00dd33 !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
  padding: 8px 15px !important;
  box-shadow: 0 0 10px rgba(0, 221, 51, 0.3) !important;
  transition: all 0.2s ease !important;
  height: auto !important;
}

.top-actions-group .butt:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 0 20px rgba(0, 221, 51, 0.6) !important;
  text-shadow: 0 0 8px rgba(0, 221, 51, 0.6) !important;
}

.top-actions-group .butt[variant="danger"] {
  background: #0f1535 !important;
  border: 2px solid #ff4444 !important;
  color: #ff4444 !important;
  box-shadow: 0 0 10px rgba(255, 68, 68, 0.3) !important;
}

.top-actions-group .butt[variant="danger"]:hover {
  box-shadow: 0 0 20px rgba(255, 68, 68, 0.6) !important;
  text-shadow: 0 0 8px rgba(255, 68, 68, 0.6) !important;
}

.top-actions-group .butt[variant="info"] {
  background: #0f1535 !important;
  border: 2px solid #00ccff !important;
  color: #00ccff !important;
  box-shadow: 0 0 10px rgba(0, 204, 255, 0.3) !important;
}

.top-actions-group .butt[variant="info"]:hover {
  box-shadow: 0 0 20px rgba(0, 204, 255, 0.6) !important;
  text-shadow: 0 0 8px rgba(0, 204, 255, 0.6) !important;
}

.dropped-table {
  opacity: 0.6;
}

.dropped-row {
  text-decoration: line-through;
  background-color: rgba(0, 221, 51, 0.05) !important;
  color: #888 !important;
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
  width: auto;
  padding: 1px 18px !important;
  height: 45px;
  text-align: center;
  margin-right: 0;
  background: #0f1535 !important;
  border: 2px solid #00dd33 !important;
  color: #00dd33 !important;
  font-weight: 700 !important;
  border-radius: 8px !important;
  box-shadow: 0 0 10px rgba(0, 221, 51, 0.3) !important;
  transition: all 0.2s ease !important;
  font-size: 1.05em !important;
}

.addremovebuttonClock:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 0 20px rgba(0, 221, 51, 0.6) !important;
  text-shadow: 0 0 8px rgba(0, 221, 51, 0.6) !important;
}

.addremovebuttonClock:active {
  transform: translateY(0) !important;
}

.itemRow{
  height: auto;
  text-align: center;
  padding: 15px 10px;
  margin-bottom: 3px;
  background: transparent;
  border-radius: 0;
  box-shadow: none;
}

.itemRow h1 {
  color: #00dd33;
  font-size: 2em;
  font-weight: 700;
  margin-bottom: 20px;
  text-shadow: 0 0 10px rgba(0, 221, 51, 0.4);
  font-family: 'Barlow Condensed';
}

/* Clock styling with arm background effect */
.itemRow #clock {
  font-size: 4em;
  font-weight: bold;
  color: #00ff00;
  font-family: 'Barlow Condensed', monospace;
  text-shadow: 0 0 10px rgba(0, 255, 0, 0.5),
               0 0 20px rgba(0, 255, 0, 0.3);
  background: radial-gradient(ellipse at center, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.9) 100%);
  border: 3px solid #000;
  border-radius: 15px;
  padding: 26px 44px;
  display: inline-block;
  letter-spacing: 8px;
  box-shadow: 0 0 30px rgba(0, 0, 0, 0.5), inset 0 0 30px rgba(0, 255, 0, 0.1);
}

.itemRowButtons{
  height: auto;
  padding: 20px;
}

.itemRowButtonsClock{
  height: auto;
  padding: 20px;
}

.itemRowPlayers{
  height: auto;
  padding-right: 0;
  padding-left: 0;
  margin-top: 30px;
  margin-bottom: 30px;
  position: relative;
  z-index: 1;
  clear: both;
}

/* Fixed header row height */
.table {
  background: #0f1535 !important;
  border: 1px solid rgba(0, 221, 51, 0.3) !important;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 0 20px rgba(0, 221, 51, 0.3), inset 0 0 15px rgba(0, 221, 51, 0.08) !important;
  margin-top: 20px;
  table-layout: fixed;
  width: 100%;
}

.table thead {
  background: #0a0e27 !important;
  border-bottom: 2px solid rgba(0, 221, 51, 0.4) !important;
}

.table thead tr {
  height: 50px;
  background: #0a0e27 !important;
  overflow: hidden;
  max-height: 50px;
}

.table thead th {
  vertical-align: middle;
  height: 50px;
  border: 1px solid rgba(0, 221, 51, 0.2) !important;
  color: #00dd33 !important;
  font-weight: 700 !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-shadow: 0 0 10px rgba(0, 221, 51, 0.5);
  text-align: center !important;
  font-family: 'Barlow Condensed' !important;
  font-size: 1.15em !important;
  background: #0a0e27 !important;
  padding: 4px 13px !important;
  line-height: 20px;
  overflow: hidden;
  max-height: 50px;
}

.username-header {
  box-shadow: 0 0 25px rgba(255, 204, 0, 0.6), inset 0 0 10px rgba(255, 204, 0, 0.2) !important;
}

.table tbody {
  background: #0f1535 !important;
}

.table tbody td {
  border-color: rgba(0, 221, 51, 0.15) !important;
  padding: 15px !important;
  vertical-align: middle;
  color: #00dd33 !important;
  font-weight: 500;
  text-align: center !important;
  font-size: 1.1em !important;
  background: #0f1535 !important;
  height: 60px !important;
  min-height: 60px !important;
  max-height: 60px !important;
  overflow: hidden !important;
}

.table tbody td:first-child {
  text-shadow: 0 0 10px rgba(0, 221, 51, 0.5), 0 0 20px rgba(255, 204, 0, 0.8), 0 0 30px rgba(255, 204, 0, 0.5);
}

.table tbody tr {
  transition: background-color 0.2s ease;
  background: #0f1535 !important;
  height: 60px !important;
  min-height: 60px !important;
  max-height: 60px !important;
  overflow: hidden !important;
}

.table tbody tr:hover {
  background-color: rgba(0, 221, 51, 0.1) !important;
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
  margin-top: 8px;
  margin-bottom: 16px;
  margin-left: 15px;
}

.center-row {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
}

.govt-row {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
}

.center-row h3 {
  color: #00dd33;
  font-weight: 700;
  text-shadow: 0 0 15px rgba(0, 221, 51, 0.5);
  font-size: 1.5em;
  margin: 0;
}

.dropdowns {
  flex-wrap: wrap;
  gap: 12px;
  background: transparent;
  border-radius: 0;
  padding: 0;
  box-shadow: none;
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

.control-group { }
.job-controls { margin-right: 0px; }

.govt-label {
  color: #00dd33 !important;
  font-weight: 700 !important;
  text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 0 10px rgba(0, 221, 51, 0.5), 0 0 20px rgba(255, 0, 0, 0.8), 0 0 30px rgba(255, 0, 0, 0.5);
  font-family: 'Barlow Condensed' !important;
  font-size: 1.9em !important;
  padding: 13px 18px !important;
  display: inline-block !important;
  letter-spacing: 1px !important;
  text-transform: uppercase;
}

.govt-dropdown-wrapper {
  margin-left: 85px;
  display: inline-flex;
  align-items: center;
  gap: 0;
}

.govt-dropdown-wrapper label {
  color: #00dd33 !important;
  font-weight: 700 !important;
  font-size: 1.8em !important;
  margin: 0 !important;
  text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 0 10px rgba(0, 221, 51, 0.5), 0 0 20px rgba(255, 0, 0, 0.8), 0 0 30px rgba(255, 0, 0, 0.5);
  font-family: 'Barlow Condensed' !important;
  letter-spacing: 1px !important;
  text-transform: uppercase;
}

.govt-dropdown-wrapper select {
  font-size: 1.5em !important;
  font-weight: 700 !important;
  padding: 0 !important;
  color: #00dd33 !important;
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
  font-family: 'Barlow Condensed' !important;
  cursor: pointer !important;
  width: auto !important;
  margin: 0 !important;
}

.govt-select-box {
  display: inline-block;
  position: relative;
}

.govt-select-box select {
  appearance: none !important;
  -webkit-appearance: none !important;
  -moz-appearance: none !important;
  padding: 0 !important;
  margin-left: 10px !important;
  background: transparent !important;
  border: none !important;
  font-size: 1.8em !important;
  font-weight: 700 !important;
  color: #00dd33 !important;
  font-family: 'Barlow Condensed' !important;
  cursor: pointer !important;
  width: auto !important;
  height: auto !important;
  line-height: 1.2 !important;
  vertical-align: middle !important;
  text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 0 10px rgba(0, 221, 51, 0.5), 0 0 20px rgba(255, 0, 0, 0.8), 0 0 30px rgba(255, 0, 0, 0.5);
  text-transform: uppercase !important;
}

.govt-select-box .govt-arrow {
  position: absolute;
  right: 90px;
  top: 11px;
  pointer-events: none;
  font-size: 1.1em;
  color: #00dd33 !important;
  margin: 0 !important;
  line-height: 1.2;
}

.govt-dropdown-wrapper select option {
  background-color: #001535 !important;
  color: #00dd33 !important;
  font-weight: 700 !important;
}

.perk-label {
  font-weight: 600;
  font-size: 14px;
  margin: 0;
  line-height: 38px;
  color: #00dd33;
}

.perk-btn {
  padding: 8px 12px;
  border: 2px solid rgba(0, 221, 51, 0.3);
  background: #0f1535;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: #00dd33;
  height: 38px;
  min-width: 38px;
}

.perk-btn:hover {
  border-color: #00dd33;
  background: rgba(0, 221, 51, 0.1);
  transform: translateY(-1px);
  box-shadow: 0 0 10px rgba(0, 221, 51, 0.3);
}

.perk-btn.active {
  border-color: #00dd33;
  background: rgba(0, 221, 51, 0.2);
  color: #00dd33;
  font-weight: 600;
  box-shadow: 0 0 15px rgba(0, 221, 51, 0.4);
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
  background: transparent;
  border-radius: 0;
  padding: 0;
  box-shadow: none;
  flex-wrap: wrap;
}
.market-btn { 
  min-width: 200px;
  background: #0f1535 !important;
  border: 2px solid #00dd33 !important;
  color: #00dd33 !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
  box-shadow: 0 0 10px rgba(0, 221, 51, 0.3) !important;
  transition: all 0.2s ease !important;
  padding: 12px 20px !important;
}

.market-btn:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 0 20px rgba(0, 221, 51, 0.6) !important;
  text-shadow: 0 0 8px rgba(0, 221, 51, 0.6) !important;
}

.senate-controls {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-bottom: 24px;
  margin-top: 20px;
  flex-wrap: wrap;
  background: transparent;
  border-radius: 0;
  padding: 0;
  box-shadow: none;
}

.senate-controls-inline {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  background: transparent;
  border-radius: 0;
  padding: 0;
  box-shadow: none;
}
.senate-btn { 
  min-width: auto;
  background: #0f1535 !important;
  border: 2px solid #00dd33 !important;
  color: #00dd33 !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
  box-shadow: 0 0 15px rgba(0, 221, 51, 0.4) !important;
  transition: all 0.3s ease !important;
  padding: 10px 16px !important;
  font-size: 0.95em !important;
}

.senate-btn:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 0 25px rgba(0, 221, 51, 0.7) !important;
  text-shadow: 0 0 10px rgba(0, 221, 51, 0.7) !important;
}

/* Special glow for the Show/Hide Senate Tabs button */
.senate-controls .senate-btn:nth-child(3) {
  box-shadow: 0 0 20px rgba(0, 221, 51, 0.5), 0 0 40px rgba(0, 221, 51, 0.3) !important;
  animation: senateBtnGlow 2s ease-in-out infinite;
}

.senate-controls .senate-btn:nth-child(3):hover {
  box-shadow: 0 0 30px rgba(0, 221, 51, 0.8), 0 0 60px rgba(0, 221, 51, 0.5) !important;
  animation: none;
}

@keyframes senateBtnGlow {
  0%, 100% {
    box-shadow: 0 0 20px rgba(0, 221, 51, 0.5), 0 0 40px rgba(0, 221, 51, 0.3) !important;
  }
  50% {
    box-shadow: 0 0 30px rgba(0, 221, 51, 0.7), 0 0 50px rgba(0, 221, 51, 0.4) !important;
  }
}

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
  overflow: visible !important;
  max-height: none !important;
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
  font-weight: 700 !important;
  font-size: 1.15em !important;
  font-family: 'Barlow Condensed' !important;
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

/* center the values in the Perk, Approval, Vote, Bleed and Heat columns */
.table td:nth-child(3) { text-align: center; }
.table td:nth-child(4) { text-align: center; }
.table td:nth-child(5) { text-align: center; }
.table td:nth-child(6) { text-align: center; }
.table td:nth-child(7) { text-align: center; }

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
  width: 100px;
  min-width: 100px;
  max-width: 100px;
}

.table th:nth-child(2),
.table td:nth-child(2) {
  width: 130px;
  min-width: 130px;
  max-width: 130px;
}

.table th:nth-child(3),
.table td:nth-child(3) {
  width: 100px;
  min-width: 100px;
  max-width: 100px;
}

.table th:nth-child(4),
.table td:nth-child(4) {
  width: 100px;
  min-width: 100px;
  max-width: 100px;
}

.table th:nth-child(5),
.table td:nth-child(5) {
  width: 100px;
  min-width: 100px;
  max-width: 100px;
}

.table th:nth-child(6),
.table td:nth-child(6) {
  width: 110px;
  min-width: 110px;
  max-width: 110px;
}

.table th:nth-child(7),
.table td:nth-child(7) {
  width: 110px;
  min-width: 110px;
  max-width: 110px;
}

/* Approval and Vote badges */
.approval-cell,
.vote-cell {
  text-align: center;
  padding: 5px 12px !important;
}

.approval-badge,
.vote-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.85em;
  font-weight: 600;
  min-width: 60px;
  border: 1px solid rgba(0, 221, 51, 0.3);
  background: transparent;
}

.approval-empty,
.vote-empty {
  color: #666;
  background: rgba(0, 221, 51, 0.05);
  border-color: rgba(0, 221, 51, 0.2);
}

.approval-approve {
  background: rgba(0, 221, 51, 0.2);
  color: #00dd33;
  border-color: rgba(0, 221, 51, 0.5);
}

.approval-disapprove {
  background: rgba(255, 68, 68, 0.2);
  color: #ff4444;
  border-color: rgba(255, 68, 68, 0.5);
}

.approval-abstain {
  background: rgba(255, 200, 0, 0.2);
  color: #ffcc00;
  border-color: rgba(255, 200, 0, 0.5);
}

.vote-yes {
  background: rgba(0, 221, 51, 0.2);
  color: #00dd33;
  border-color: rgba(0, 221, 51, 0.5);
}

.vote-no {
  background: rgba(255, 68, 68, 0.2);
  color: #ff4444;
  border-color: rgba(255, 68, 68, 0.5);
}

.vote-abstain {
  background: rgba(255, 200, 0, 0.2);
  color: #ffcc00;
  border-color: rgba(255, 200, 0, 0.5);
}

/* Job Title header with dropdown */
.job-title-header {
  position: relative;
  padding: 0 !important;
  cursor: pointer;
  overflow: hidden;
  max-height: 50px;
}

/* Hide the actual select element but keep it functional */
.job-header-select {
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

/* Show the pretty header text */
.job-title-text {
  display: block;
  color: #00dd33 !important;
  font-weight: 700 !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-shadow: 0 0 10px rgba(0, 221, 51, 0.5);
  font-family: 'Barlow Condensed' !important;
  font-size: 1.15em !important;
  padding: 15px !important;
  text-align: center !important;
  line-height: 20px;
}

.job-title-arrow {
  margin-left: 4px;
  font-size: 0.9em;
}

/* Perk header styling */
.perk-title-header {
  position: relative;
  padding: 0 !important;
  cursor: pointer;
  overflow: hidden;
  max-height: 50px;
}

/* Hide the actual perk select element but keep it functional */
.perk-header-select {
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

/* Show the pretty perk header text */
.perk-title-text {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #00dd33 !important;
  font-weight: 700 !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-shadow: 0 0 10px rgba(0, 221, 51, 0.5);
  font-family: 'Barlow Condensed' !important;
  font-size: 1.15em !important;
  padding: 15px !important;
  text-align: center !important;
  line-height: 20px;
  width: 100%;
}

.perk-title-arrow {
  margin-left: 4px;
  font-size: 0.9em;
}

/* Approval header styling */
.approval-title-header {
  position: relative;
  padding: 0 !important;
  cursor: pointer;
  overflow: hidden;
  max-height: 50px;
}

/* Hide the actual approval select element but keep it functional */
.approval-header-select {
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

/* Show the pretty approval header text */
.approval-title-text {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #00dd33 !important;
  font-weight: 700 !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-shadow: 0 0 10px rgba(0, 221, 51, 0.5);
  font-family: 'Barlow Condensed' !important;
  font-size: 1.15em !important;
  padding: 5px 10px !important;
  text-align: center !important;
  line-height: 20px;
  white-space: nowrap;
  width: 100%;
}

.approval-title-arrow {
  margin-left: 4px;
  font-size: 0.9em;
}

/* Vote header styling */
.vote-title-header {
  position: relative;
  padding: 0 !important;
  cursor: pointer;
  overflow: hidden;
  max-height: 50px;
}

/* Hide the actual vote select element but keep it functional */
.vote-header-select {
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

/* Show the pretty vote header text */
.vote-title-text {
  display: inline;
  color: #00dd33 !important;
  font-weight: 700 !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-shadow: 0 0 10px rgba(0, 221, 51, 0.5);
  font-family: 'Barlow Condensed' !important;
  font-size: 1.15em !important;
  padding: 5px 10px !important;
  text-align: center !important;
  line-height: 20px;
  white-space: nowrap;
}

.vote-title-arrow {
  margin-left: 4px;
  font-size: 0.9em;
}

/* Get Paid button styling */
.btn-get-paid {
  background: #0f1535 !important;
  border: 2px solid #ffcc00 !important;
  color: #ffcc00 !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
  padding: 8px 20px !important;
  box-shadow: 0 0 15px rgba(255, 204, 0, 0.4) !important;
  transition: all 0.2s ease !important;
  font-size: 0.9em !important;
  min-width: 150px;
}

.btn-get-paid:hover {
  border-color: #ffff00 !important;
  box-shadow: 0 0 20px rgba(255, 204, 0, 0.6) !important;
  text-shadow: 0 0 8px rgba(255, 204, 0, 0.4) !important;
  transform: translateY(-2px) !important;
}

.btn-get-paid:disabled {
  opacity: 0.6 !important;
  cursor: not-allowed !important;
}

/* Perk column styling */
.perk-column {
  padding: 0 !important;
  background: transparent !important;
  border: none !important;
  height: 60px !important;
  max-height: 60px !important;
  min-height: 60px !important;
  overflow: hidden !important;
  position: relative !important;
}

/* Perk icons inline with job titles */
.perk-icon {
  height: 40px;
  width: 40px;
  object-fit: contain;
  position: absolute !important;
  top: 50% !important;
  left: 50% !important;
  transform: translate(-50%, -50%) !important;
  margin: 0 !important;
}

@media (min-width: 1200px) {
  .perk-icon { height: 40px; }
}

/* optional: small spacing tweak */
.bleed-btn-minus { margin-right: 2px; }
.bleed-btn-plus  { margin-left: 2px; }

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
  background: #0f1535;
  border: 1px solid rgba(0, 221, 51, 0.2);
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

.bidding-tally {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tally-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #0f1535;
  border: 1px solid rgba(0, 221, 51, 0.1);
  border-radius: 4px;
  font-size: 0.9em;
  color: #00dd33;
}

.participant-name {
  font-weight: 500;
}

.tally-item .badge {
  font-size: 0.8em;
}

.bid-time-display {
  font-size: 2em;
  font-weight: bold;
  color: #00dd33;
  font-family: 'Barlow Condensed';
  text-shadow: 0 0 10px rgba(0, 221, 51, 0.5);
}

.bid-time-controls {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.time-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.time-label {
  font-weight: 600;
  font-size: 0.9em;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #00dd33;
}

.time-buttons {
  display: flex;
  align-items: center;
  gap: 12px;
}

.time-value {
  font-size: 1.5em;
  font-weight: bold;
  font-family: 'Barlow Condensed';
  min-width: 50px;
  text-align: center;
  color: #00dd33;
  text-shadow: 0 0 8px rgba(0, 221, 51, 0.3);
}

.time-buttons .btn {
  padding: 6px 12px;
  font-weight: bold;
}

/* Dictator Bidding Modal Styles */
.dictator-bid-container {
  padding: 10px 0;
}

.bid-display-section {
  background: #0a0e27;
  border: 2px solid rgba(0, 221, 51, 0.3);
  border-radius: 12px;
  padding: 30px 20px;
  text-align: center;
  color: #00dd33;
  box-shadow: 0 0 20px rgba(0, 221, 51, 0.2), inset 0 0 20px rgba(0, 221, 51, 0.05);
}

.bid-instruction {
  margin: 0;
  font-size: 1.1em;
  margin-bottom: 15px;
  font-weight: 500;
}

.bid-time-big {
  font-size: 4em;
  font-weight: bold;
  font-family: 'Barlow Condensed';
  letter-spacing: 8px;
  text-shadow: 0 0 20px rgba(0, 221, 51, 0.5), 0 0 40px rgba(0, 221, 51, 0.3);
  color: #00dd33;
}

.bid-buttons-section {
  background: #0f1535;
  border: 1px solid rgba(0, 221, 51, 0.2);
  border-radius: 12px;
  padding: 20px;
}

.bid-button-row {
  display: flex;
  gap: 12px;
  justify-content: space-between;
}

.bid-btn {
  flex: 1;
  padding: 12px 8px;
  font-weight: 600;
  border-width: 2px;
  transition: all 0.2s ease;
  background: #0f1535;
  border-color: #00dd33;
  color: #00dd33;
  box-shadow: 0 0 10px rgba(0, 221, 51, 0.2);
}

.bid-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 20px rgba(0, 221, 51, 0.4);
  text-shadow: 0 0 8px rgba(0, 221, 51, 0.6);
}

.bid-btn:active {
  transform: translateY(0);
}

.place-bid-btn {
  padding: 16px;
  font-size: 1.1em;
  letter-spacing: 1px;
  box-shadow: 0 0 15px rgba(0, 221, 51, 0.3);
  transition: all 0.3s ease;
  background: #0f1535;
  border: 2px solid #00dd33;
  color: #00dd33;
}

.place-bid-btn:hover {
  box-shadow: 0 0 30px rgba(0, 221, 51, 0.6);
  transform: translateY(-2px);
  text-shadow: 0 0 8px rgba(0, 221, 51, 0.6);
}

.bidding-status-section {
  background: #0f1535;
  border-radius: 12px;
  padding: 20px;
  border-left: 4px solid #00dd33;
}

.bidding-status-section h6 {
  color: #00dd33;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-size: 0.85em;
  text-shadow: 0 0 8px rgba(0, 221, 51, 0.3);
}

.admin-section {
  padding-top: 20px;
}

.admin-section .btn {
  padding: 14px;
  font-size: 1.05em;
  letter-spacing: 0.5px;
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
  transition: all 0.3s ease;
}

.admin-section .btn:hover {
  box-shadow: 0 6px 20px rgba(40, 167, 69, 0.5);
  transform: translateY(-2px);
}

/* Graph Filter Styles */
.graph-filters {
  background: white;
  border-radius: 10px;
  padding: 15px;
  border: 1px solid #e0e0e0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.graph-filters h6 {
  margin: 0 0 12px 0;
  color: #333;
  font-weight: 600;
  font-size: 0.95em;
}

.player-filter-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.player-filter-buttons .btn {
  padding: 6px 12px;
  font-size: 0.85em;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.player-filter-buttons .btn-primary {
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);
}

.player-filter-buttons .btn-outline-secondary {
  color: #666;
  border-color: #ccc;
}

.chart-controls-info {
  background: #f8f9fa;
  padding: 10px 12px;
  border-radius: 6px;
  border-left: 3px solid #667eea;
}
</style>
