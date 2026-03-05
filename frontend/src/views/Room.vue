<template>
  <div id="app">
    <b-container class="bv-example-row">
      <!-- Header with action buttons -->
      <RoomHeader 
        :isAdmin="isAdmin"
        @leave-room="openLeaveModal"
        @open-admin-controls="openAdminControlsModal"
      />

      <!-- Clock display, collectables, and action buttons -->
      <RoomClock 
        :clock="clock"
        :maxCollectables="maxCollectables"
        :isLoadingPay="isPaying"
        :isLoadingJail="isPayingJail"
        @adjust-clock="uClock"
        @get-paid="getPaid"
        @get-out-of-jail="getOutOfJail"
      />

      <!-- Government Display -->
      <b-row class="room-government__row">
        <b-col>
          <div class="room-government__container">
            <div class="room-government__control-group">
              <span class="room-government__label">
                Government: {{ currentGovernmentName }}
              </span>
            </div>
          </div>
        </b-col>
      </b-row>

      <!-- Max Collectables Label -->
      <div class="room__max-collectables">
        Max collectables: {{ maxCollectables }}
      </div>

      <!-- Participants table -->
      <RoomParticipantsTable
        :activePlayers="activePlayers"
        :jobs="jobs"
        :selectedJobId="selectedJobId"
        :selectedPerk="selectedPerk"
        :selectedHeaderApproval="selectedHeaderApproval"
        :currentUserId="currentUserId"
        :governmentIcon="iconForParticipant"
        :perkIcon="perkIconForParticipant"
        @update:selectedJobId="(id) => selectedJobId = id"
        @update:selectedPerk="(perk) => selectedPerk = perk"
        @update:selectedHeaderApproval="(status) => selectedHeaderApproval = status"
        @header-approval-changed="onHeaderApprovalChange"
        @bleed-changed="changeBleed"
        @heat-changed="changeHeat"
        @clear-approval="clearApprovalStatus"
        @clear-vote="clearGovVote"
      />

      <!-- Dropped Players table -->
      <RoomDroppedPlayers
        :droppedPlayers="droppedPlayers"
        :governmentIcon="iconForParticipant"
        :perkIcon="perkIconForParticipant"
      />

      <!-- Leave Room modal -->
      <b-modal
        id="LeaveRoomModal"
        ref="leaveRoomModal"
        title="Leave Room:"
      >
        Are you sure you want to Leave room: {{ roomname }}
        <template #footer>
          <b-button size="sm" variant="secondary" :disabled="isLeaving" @click="leaveRoomModal?.hide()">
            No
          </b-button>
          <b-button size="sm" variant="danger" :disabled="isLeaving" @click="confirmLeave">
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
            <option value="reject">Reject</option>
          </select>
        </div>
      </b-modal>

      <!-- Government Vote Modal - Secret Voting until Admin Concludes -->
      <b-modal
        id="govVoteModal"
        ref="voteModal"
        title="🗳️ Vote in Progress"
        :hide-header-close="!isAdmin"
        no-close-on-backdrop
        no-close-on-esc
        size="lg"
        centered
      >
        <div class="vote-container">
          <!-- Question/Topic being voted on -->
          <div class="vote-question-box">
            <span class="vote-question-icon">📋</span>
            <p class="vote-question-text">{{ voteQuestion }}</p>
          </div>
          
          <!-- Vote Buttons - only show if user hasn't voted yet -->
          <div v-if="!currentUserVote" class="vote-section">
            <h5 class="vote-section-title">Cast Your Vote</h5>
            <div class="vote-buttons-row">
              <b-button
                size="lg"
                class="vote-button vote-yes"
                :style="{ backgroundColor: '#22c55e', borderColor: '#16a34a', color: '#ffffff' }"
                @click="submitVote('yes')"
              >
                <span class="vote-icon">✓</span>
                <strong style="color: #ffffff;">YES</strong>
              </b-button>
              <b-button
                size="lg"
                class="vote-button vote-abstain"
                :style="{ backgroundColor: '#f59e0b', borderColor: '#d97706', color: '#ffffff' }"
                @click="submitVote('abstain')"
              >
                <span class="vote-icon">−</span>
                <strong style="color: #ffffff;">ABSTAIN</strong>
              </b-button>
              <b-button
                size="lg"
                class="vote-button vote-no"
                :style="{ backgroundColor: '#ef4444', borderColor: '#dc2626', color: '#ffffff' }"
                @click="submitVote('no')"
              >
                <span class="vote-icon">✗</span>
                <strong style="color: #ffffff;">NO</strong>
              </b-button>
            </div>
          </div>
          
          <!-- Confirmation message after voting -->
          <div v-else class="vote-submitted-box">
            <span class="vote-submitted-icon">✅</span>
            <p class="vote-submitted-text">Your vote has been recorded.</p>
            <p class="vote-submitted-hint">Votes will be revealed when the admin concludes voting.</p>
          </div>
          
          <!-- Participant Voting Status -->
          <div class="vote-participants-section">
            <h5 class="vote-section-title">
              Voting Progress 
              <span class="vote-count-badge">
                {{ Object.values(voteTally).filter(v => v).length }} / {{ Object.keys(voteTally).length }}
              </span>
            </h5>
            <div class="vote-participants-grid">
              <div 
                v-for="participant in participants" 
                :key="participant.user_id"
                class="vote-participant-card"
                :class="{ 'has-voted': voteTally[participant.user_id] }"
              >
                <span class="participant-status-icon">
                  {{ voteTally[participant.user_id] ? '🗳️' : '⏳' }}
                </span>
                <span class="participant-name">{{ participant.username }}</span>
                <span class="participant-vote-status">
                  {{ voteTally[participant.user_id] ? 'Voted' : 'Waiting...' }}
                </span>
              </div>
            </div>
          </div>
          
          <!-- Admin Conclude Button -->
          <div v-if="isAdmin" class="vote-admin-section">
            <hr class="vote-divider" />
            <b-button 
              variant="primary" 
              size="lg"
              class="conclude-vote-btn"
              @click="concludeVote"
            >
              <span class="conclude-icon">🔓</span>
              Reveal Votes & Conclude
            </b-button>
            <p class="admin-hint">All votes will be revealed to everyone.</p>
          </div>
        </div>
        <template #footer></template>
      </b-modal>
      
      <!-- Vote Results Modal -->
      <b-modal
        id="voteResultsModal"
        ref="voteResultsModal"
        title="📊 Vote Results"
        size="lg"
        centered
        ok-only
        ok-title="Close"
      >
        <div v-if="resultsSummary" class="vote-results-container">
          <!-- Outcome Banner -->
          <div 
            class="vote-outcome-banner"
            :class="{
              'outcome-passed': resultsSummary.outcome === 'PASSED',
              'outcome-rejected': resultsSummary.outcome === 'REJECTED',
              'outcome-tie': resultsSummary.outcome === 'TIE'
            }"
          >
            <span class="outcome-icon">
              {{ resultsSummary.outcome === 'PASSED' ? '✅' : resultsSummary.outcome === 'REJECTED' ? '❌' : '⚖️' }}
            </span>
            <span class="outcome-text">{{ resultsSummary.outcome }}</span>
          </div>
          
          <!-- Vote Counts -->
          <div class="vote-counts-row">
            <div class="vote-count-box yes">
              <span class="count-number">{{ resultsSummary.yes }}</span>
              <span class="count-label">Yes</span>
            </div>
            <div class="vote-count-box abstain">
              <span class="count-number">{{ resultsSummary.abstain }}</span>
              <span class="count-label">Abstain</span>
            </div>
            <div class="vote-count-box no">
              <span class="count-number">{{ resultsSummary.no }}</span>
              <span class="count-label">No</span>
            </div>
          </div>
          
          <!-- Individual Votes -->
          <div class="individual-votes-section">
            <h5 class="votes-title">Individual Votes</h5>
            <div class="individual-votes-grid">
              <div 
                v-for="vote in resultsSummary.votes" 
                :key="vote.userId"
                class="individual-vote-card"
                :class="'vote-' + vote.vote"
              >
                <span class="voter-name">{{ vote.username }}</span>
                <span class="voter-choice">
                  {{ vote.vote === 'yes' ? '✓ YES' : vote.vote === 'no' ? '✗ NO' : '− ABSTAIN' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </b-modal>

      <!-- Dictator Bidding Modal -->
      <b-modal
        id="dictatorBiddingModal"
        ref="dictatorBiddingModal"
        title="Dictator Auction"
        hide-header-close
        no-close-on-backdrop
        no-close-on-esc
        size="md"
        centered
      >
        <div class="dictator-bid-container-compact">
          <!-- Top row: Your time + Bid amount side by side -->
          <div class="bid-top-row">
            <div class="your-time-compact">
              <span class="time-label">Your Time:</span>
              <span class="time-value">{{ clock }}</span>
            </div>
            <div class="bid-amount-compact">
              <span class="bid-label">Your Bid:</span>
              <span class="bid-value">{{ String(Math.floor(bidTimeMinutes / 60)).padStart(2, '0') }}:{{ String(bidTimeMinutes % 60).padStart(2, '0') }}</span>
            </div>
          </div>

          <!-- Time Control Buttons - Compact grid -->
          <div class="bid-buttons-compact">
            <b-button size="sm" variant="secondary" @click="bidTimeMinutes = Math.max(0, bidTimeMinutes - 60)">-1h</b-button>
            <b-button size="sm" variant="secondary" @click="bidTimeMinutes = Math.max(0, bidTimeMinutes - 30)">-30</b-button>
            <b-button size="sm" variant="secondary" @click="bidTimeMinutes = Math.max(0, bidTimeMinutes - 10)">-10</b-button>
            <b-button size="sm" variant="secondary" @click="bidTimeMinutes = bidTimeMinutes + 10">+10</b-button>
            <b-button size="sm" variant="secondary" @click="bidTimeMinutes = bidTimeMinutes + 30">+30</b-button>
            <b-button size="sm" variant="secondary" @click="bidTimeMinutes = bidTimeMinutes + 60">+1h</b-button>
          </div>

          <!-- Place Bid Button -->
          <b-button variant="warning" @click="placeDictatorBid" class="w-100 place-bid-btn-compact">
            <strong>PLACE BID</strong>
          </b-button>

          <!-- Bidding Status - Compact list -->
          <div class="bidding-status-compact">
            <div class="status-header">Bidding Status</div>
            <div class="bidding-list">
              <div 
                v-for="participant in participants" 
                :key="participant.user_id" 
                class="bid-participant"
              >
                <span class="p-name">{{ participant.username }}</span>
                <span v-if="!biddingActive && biddingTally[participant.user_id]" class="p-bid">
                  {{ String(Math.floor((dictator_bid_amounts[participant.user_id] || 0) / 60)).padStart(2, '0') }}:{{ String((dictator_bid_amounts[participant.user_id] || 0) % 60).padStart(2, '0') }}
                </span>
                <span v-if="biddingTally[participant.user_id]" class="p-status done">✓</span>
                <span v-else class="p-status waiting">⏳</span>
              </div>
            </div>
          </div>

          <!-- Admin Conclude Button -->
          <b-button v-if="isAdmin" variant="danger" @click="concludeDictatorBidding" class="w-100 conclude-btn-compact">
            <strong>Conclude Bidding</strong>
          </b-button>
        </div>
        <template #footer></template>
      </b-modal>

      <!-- Dictator Bidding Winner Modal -->
      <b-modal
        id="dictatorBiddingWinnerModal"
        ref="dictatorBiddingWinnerModal"
        title="Auction Results"
        centered
        size="md"
      >
        <div class="auction-results">
          <div class="winner-banner">
            <span class="crown">👑</span>
            <h3>{{ dictatorWinner }}</h3>
            <p>Crowned Dictator!</p>
          </div>
          
          <div class="leaderboard-section">
            <div class="leaderboard-header">Bid Leaderboard</div>
            <div class="leaderboard-list">
              <div 
                v-for="(entry, index) in biddingLeaderboard" 
                :key="entry.user_id" 
                class="leaderboard-row"
                :class="{ 'winner-row': entry.is_winner }"
              >
                <span class="rank">{{ index + 1 }}</span>
                <span class="lb-name">{{ entry.username }}</span>
                <span class="lb-bid">{{ String(Math.floor(entry.bid_amount / 60)).padStart(2, '0') }}:{{ String(entry.bid_amount % 60).padStart(2, '0') }}</span>
              </div>
            </div>
          </div>
          
          <div class="mt-3 d-flex justify-content-end">
            <b-button variant="primary" size="sm" @click="dictatorBiddingWinnerModal?.hide()">OK</b-button>
          </div>
        </div>
        <template #footer></template>
      </b-modal>

      <!-- End Game modal -->
      <b-modal
        id="removeRoomModal"
        ref="removeRoomModal"
        title="End Game:"
      >
        Are you sure you want to end the game: {{ roomname }}
        <template #footer>
          <b-button size="sm" variant="secondary" :disabled="isRemoving" @click="removeRoomModal?.hide()">
            No
          </b-button>
          <b-button size="sm" variant="danger" :disabled="isRemoving" @click="confirmRemove">
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
        
        <!-- Winner Selection Section -->
        <div class="winner-selection-section mt-4" v-if="isAdmin && !loadingHistory">
          <div class="winner-selection-card">
            <h5 class="winner-title">🏆 Select Game Winner</h5>
            <p class="winner-description">Choose a winner to award them a point on the leaderboard.</p>
            
            <div v-if="winnerSet" class="winner-confirmed">
              <span class="winner-badge">✓ Winner: {{ getParticipantName(selectedWinner) }}</span>
            </div>
            
            <div v-else class="winner-form">
              <select v-model="selectedWinner" class="winner-select">
                <option :value="null" disabled>-- Select Winner --</option>
                <option v-for="player in activePlayers" :key="player.user_id" :value="player.user_id">
                  {{ player.username }}
                </option>
              </select>
              <b-button 
                variant="success" 
                size="sm"
                :disabled="!selectedWinner || settingWinner"
                @click="confirmWinner"
                class="ms-2"
              >
                {{ settingWinner ? 'Saving...' : 'Confirm Winner' }}
              </b-button>
            </div>
          </div>
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

      <!-- Wheel Spinner Component -->
      <WheelSpinner ref="wheelSpinnerRef" :participants="participants" />

      <!-- Politburo Wheel Selection Modal -->
      <b-modal
        id="politburoWheelModal"
        ref="politburoWheelModal"
        title="Politburo Selection"
        size="lg"
        centered
      >
        <div class="politburo-selection-compact">
          <!-- Selected Members Banner -->
          <div class="selected-members-banner">
            <div class="members-header">
              <span class="members-icon">☭</span>
              <span class="members-title">Politburo Members</span>
              <span class="members-count">{{ politburoMembers.length }}/2</span>
            </div>
            <div class="members-slots">
              <div class="member-slot" :class="{ filled: politburoMembers.length >= 1 }">
                <span v-if="politburoMembers.length >= 1">{{ participantOptions.find(p => p.value === politburoMembers[0])?.text || '?' }}</span>
                <span v-else class="empty-slot">Empty</span>
              </div>
              <div class="member-slot" :class="{ filled: politburoMembers.length >= 2 }">
                <span v-if="politburoMembers.length >= 2">{{ participantOptions.find(p => p.value === politburoMembers[1])?.text || '?' }}</span>
                <span v-else class="empty-slot">Empty</span>
              </div>
            </div>
          </div>

          <!-- Wheel Container -->
          <div class="wheel-container-politburo">
            <WheelSpinner 
              ref="politburoWheelRef" 
              :participants="availablePolitburoCandidates" 
              :show-custom-actions="true" 
              :inline="true"
              :is-admin="isAdmin"
              :show-spin-button="politburoMembers.length < 2"
              @spin-request="handlePolitburoSpinRequest"
            >
              <template #winner-actions>
                <b-button 
                  variant="success" 
                  size="lg"
                  @click="addToPolitburo"
                  class="me-2 politburo-action-btn"
                >
                  ✓ Add to Politburo
                </b-button>
                <b-button 
                  variant="secondary" 
                  size="lg"
                  @click="spinAgain"
                  class="politburo-action-btn"
                >
                  ↻ Spin Again
                </b-button>
              </template>
            </WheelSpinner>
          </div>

          <!-- Admin Controls -->
          <div v-if="isAdmin" class="politburo-admin-controls">
            <div class="control-row-small">
              <b-button 
                variant="outline-warning" 
                size="sm"
                :disabled="politburoMembers.length === 0"
                @click="resetPolitburoSelection"
              >
                ↺ Reset Selection
              </b-button>
            </div>
            
            <!-- Balance Books Toggle -->
            <div class="balance-books-toggle">
              <label class="toggle-switch">
                <input type="checkbox" v-model="balanceBooksOnSave" />
                <span class="toggle-slider"></span>
              </label>
              <span class="toggle-label">Balance the books after selection</span>
            </div>
            
            <div class="final-actions">
              <b-button 
                variant="success" 
                size="lg"
                :disabled="politburoMembers.length !== 2 || isSubmittingGov"
                @click="savePolitburoSelection"
                class="complete-btn"
              >
                {{ isSubmittingGov ? 'Saving...' : '✓ Complete Selection' }}
              </b-button>
              <b-button 
                variant="secondary" 
                @click="cancelPolitburoSelection"
              >
                Cancel
              </b-button>
            </div>
          </div>

          <!-- Non-admin watching message -->
          <div v-else class="watching-message">
            <span class="watching-icon">👁</span>
            <span>Watching the Politburo selection...</span>
          </div>

          <div class="text-danger mt-2" v-if="govError">{{ govError }}</div>
        </div>
        <template #footer></template>
      </b-modal>

      <!-- Admin Controls Modal -->
      <AdminControlsModal
        ref="adminControlsModalRef"
        :socket="socket"
        :participants="participants"
        :displayGovernments="displayGovernments"
        :biddingTally="biddingTally"
        :biddingActive="biddingActive"
        :dictatorBiddingModal="dictatorBiddingModal"
        @spin-wheel="openWheelSpinner"
        @cast-vote="partakeGovVote"
        @end-game="openRemoveModal"
      />
    </b-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { useSocket } from '@/composables/useSocket'
import RoomListService from '@/services/RoomListService'
import WheelSpinner from '@/components/SpinWheel.vue'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js'

// Import extracted room components
import RoomHeader from '@/components/room/RoomHeader.vue'
import RoomClock from '@/components/room/RoomClock.vue'
import RoomParticipantsTable from '@/components/room/RoomParticipantsTable.vue'
import RoomDroppedPlayers from '@/components/room/RoomDroppedPlayers.vue'
import AdminControlsModal from '@/components/room/AdminControlsModal.vue'

// Import composables
import { useRoomState } from '@/composables/useRoomState'
import { useGovernment } from '@/composables/useGovernment'
import { useDictatorBidding } from '@/composables/useDictatorBidding'
import { usePolitburoWheel } from '@/composables/usePolitburoWheel'
import { useVoting } from '@/composables/useVoting'

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

const store = useStore()
const router = useRouter()
const { socket } = useSocket()

// Initialize composables
const roomState = useRoomState()
const government = useGovernment()
const dictatorBidding = useDictatorBidding()
const politburoWheel = usePolitburoWheel()
const voting = useVoting()

// Destructure room state refs and computed properties
const { roomname, roomOwnerId, clock, participants, roomGovernment, jobs, governments, displayGovernments, govLabel } = roomState

// Destructure government utility functions
const { getGovernmentIconForParticipant, getPerkIconForParticipant } = government

// Closures to match Room state injection into icon functions
const iconForParticipant = (p) => getGovernmentIconForParticipant(p, roomGovernment.value)
const perkIconForParticipant = (p) => getPerkIconForParticipant(p)

// Computed early to avoid circular dependencies
const currentUserId = computed(() => store.state.auth.userId)

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

const currentUserParticipant = computed(() => {
  return activePlayers.value.find(p => p.user_id === currentUserId.value)
})

const maxCollectables = computed(() => {
  const participant = currentUserParticipant.value
  if (!participant) return 5
  
  let max = 5
  // +1 if no bleed
  if (!participant.bleed || participant.bleed === 0) {
    max += 1
  }
  // +1 if senior perk
  if (participant.perk === 'Senior') {
    max += 1
  }
  
  return max
})

// FIX: add missing refs
const selectedJobId = ref(null)
const selectedPerk = ref(null)
const selectedHeaderApproval = ref(null)


// History graph modal
const historyGraphModal = ref(null)
const loadingHistory = ref(false)
const historyError = ref(null)
const chartData = ref(null)
const selectedPlayersForGraph = ref([])
const allGraphPlayers = ref([])
const selectedWinner = ref(null)
const winnerSet = ref(false)
const settingWinner = ref(false)
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

// State
const isPaying = ref(false)
const isPayingJail = ref(false)
const isSubmittingGov = ref(false)
const govError = ref('')

// Options for selects based on current participants
const participantOptions = computed(() =>
  (participants.value || []).map(p => ({
    value: p.user_id ?? p.userId ?? p.id,
    text: p.username || `User ${p.user_id || p.id}`
  }))
)

// ADD: modal refs and busy flags (fixes ReferenceError)
const leaveRoomModal = ref(null)
const removeRoomModal = ref(null)
const wheelSpinnerRef = ref(null)
const politburoWheelModal = ref(null)
const approvalStatusModal = ref(null)
const govVoteModal = ref(null)
const adminControlsModalRef = ref(null)
const isLeaving = ref(false)
const isRemoving = ref(false)
const showVoteColumn = ref(true)
const selectedApprovalOption = ref(null)
const selectedVoteOption = ref(null)

// Dictator bidding state (from composable)
const { 
  dictatorBiddingModal, 
  dictatorBiddingWinnerModal, 
  biddingActive, 
  biddingTally, 
  currentUserBid, 
  bidTimeMinutes, 
  dictatorWinner,
  initiateBidding,
  placeBid,
  concludeBidding,
  announceBiddingWinner,
  resetBidding
} = dictatorBidding
const concludeBiddingModal = ref(null)
const dictator_bid_amounts = ref({})
const biddingLeaderboard = ref([])

// Politburo wheel state (from composable)
const { 
  politburoMembers, 
  isSpinningPolitburo, 
  balanceBooksOnSave, 
  currentWheelWinner, 
  showWheelResult,
  isSelectionComplete,
  getAvailableCandidates,
  addMember,
  removeMember,
  validateSelection
} = politburoWheel

// Voting state (from composable)
const {
  votingActive,
  voteTally,
  currentUserVote,
  voteResults,
  votingConcluded,
  voteQuestion,
  voteModal,
  voteResultsModal,
  votedCount,
  totalParticipants: voteTotalParticipants,
  allVoted,
  resultsSummary,
  initiateVoting,
  castVote,
  updateTally,
  concludeVoting: concludeVotingLocal,
  resetVoting
} = voting

// Available candidates for politburo wheel (exclude already selected members)
const availablePolitburoCandidates = computed(() => {
  const candidates = getAvailableCandidates(participants.value)
  console.log('[availablePolitburoCandidates] Total participants:', participants.value.length, 'Selected members:', politburoMembers.value.length, 'Available candidates:', candidates.length, 'Participants:', participants.value)
  return candidates
})

// Build select options
const governmentOptions = computed(() => [
  { value: null, text: 'Select a government' },
  ...governments.value.map(g => ({ value: g.id, text: g.name }))
])
const jobOptions = computed(() => {
  // Sort jobs by faction: Finance first, then Illicit, then Public Service
  // Within each faction, sort alphabetically by name
  const factionOrder = { 'Finance': 1, 'Illicit': 2, 'Public Service': 3, 'Unemployed': 0 }
  
  const sortedJobs = [...jobs.value].sort((a, b) => {
    const orderA = factionOrder[a.type] ?? 99
    const orderB = factionOrder[b.type] ?? 99
    
    if (orderA !== orderB) return orderA - orderB
    return a.name.localeCompare(b.name)
  })
  
  return [
    { value: null, text: 'Select a job' },
    ...sortedJobs.map(j => ({
      value: j.id,
      text: j.tier ? `${j.name} (Tier ${j.tier})` : j.name
    }))
  ]
})

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
  participants.value = Array.isArray(room.participants) 
    ? room.participants.map(updatedP => {
        // Preserve existing participant data to avoid losing approval_status, gov_vote, etc
        const existingP = participants.value.find(p => p.user_id === updatedP.user_id)
        return {
          user_id: updatedP.user_id,
          username: updatedP.username ?? existingP?.username ?? 'Unknown',
          job_name: updatedP.job_name ?? existingP?.job_name ?? '-',
          job_tier: updatedP.job_tier ?? existingP?.job_tier ?? '-',
          clock: updatedP.clock ?? existingP?.clock ?? '00•00•00',
          bleed: updatedP.bleed ?? existingP?.bleed ?? 0,
          heat: updatedP.heat ?? existingP?.heat ?? 0,
          perk: updatedP.perk ?? existingP?.perk ?? null,
          approval_status: updatedP.approval_status ?? existingP?.approval_status ?? null,
          gov_vote: updatedP.gov_vote ?? existingP?.gov_vote ?? null,
          is_in_jail: updatedP.is_in_jail ?? existingP?.is_in_jail ?? false
        }
      })
    : []
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

  console.log('[room_state] Received room state:', room)

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
    perk: p.perk ?? null,
    approval_status: p.approval_status ?? null,
    gov_vote: p.gov_vote ?? null,
    is_in_jail: p.is_in_jail ?? false
  })) : []
  
  console.log('[room_state] Participants loaded:', participants.value.length, participants.value)
  
  // Debug: Check for dropped players
  const dropped = participants.value.filter(p => p.clock === '00•00•00')
  if (dropped.length > 0) {
    console.log('[room_state] Dropped players detected:', dropped.map(p => p.username))
  }
  
  roomGovernment.value = room?.government || null

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

// Secret voting socket listeners
socket.on('startVoting', (data) => {
  console.log('[startVoting] Voting session started', data)
  votingActive.value = true
  votingConcluded.value = false
  currentUserVote.value = null
  voteResults.value = null
  
  if (data?.question) {
    voteQuestion.value = data.question
  }
  
  // Initialize tally from server or locally
  if (data?.tally) {
    voteTally.value = data.tally
  } else {
    voteTally.value = {}
    participants.value.forEach(p => {
      voteTally.value[p.user_id] = false
    })
  }
  
  // Open voting modal for all players
  voteModal.value && voteModal.value.show()
})

socket.on('voteTallyUpdate', (data) => {
  console.log('[voteTallyUpdate] Tally updated', data)
  // Update tally (who has voted, not what)
  if (data?.tally) {
    voteTally.value = data.tally
  }
})

socket.on('votingConcluded', (data) => {
  console.log('[votingConcluded] Voting concluded', data)
  votingActive.value = false
  votingConcluded.value = true
  voteResults.value = data.results || {}
  
  // Close voting modal and show results
  voteModal.value && voteModal.value.hide()
  
  setTimeout(() => {
    voteResultsModal.value && voteResultsModal.value.show()
  }, 100)
})

socket.on('startDictatorBidding', (data) => {
  console.log('[startDictatorBidding] Bidding started', data)
  biddingActive.value = true
  
  // Check if this is a reconnect with existing tally data
  if (data?.reconnect && data?.tally) {
    biddingTally.value = data.tally
    dictator_bid_amounts.value = data.bid_amounts || {}
  } else {
    // Fresh bidding start
    biddingTally.value = {}
    dictator_bid_amounts.value = {}
    currentUserBid.value = null
    bidTimeMinutes.value = 0
    
    // Initialize tally with all participants
    participants.value.forEach(p => {
      biddingTally.value[p.user_id] = false
    })
  }
  
  // Open bidding modal for all players
  dictatorBiddingModal.value && dictatorBiddingModal.value.show()
})

socket.on('startPolitburoSpin', (data) => {
  console.log('[startPolitburoSpin] Received spin event with rotation:', data?.rotation)
  
  // Open the politburo modal for all players so they can see the spin
  politburoWheelModal.value && politburoWheelModal.value.show()
  
  // Apply the synchronized rotation to all players (including admin)
  if (politburoWheelRef.value && data?.rotation) {
    setTimeout(() => {
      politburoWheelRef.value.spinToRotation(data.rotation)
    }, 200)
    
    // Reset spinning state after animation completes
    setTimeout(() => {
      isSpinningPolitburo.value = false
    }, 5300)
  }
})

socket.on('politburoMembersUpdate', (data) => {
  console.log('[politburoMembersUpdate] Received members update:', data?.members)
  
  // Update local politburo members for all players
  if (data?.members !== undefined) {
    politburoMembers.value = data.members
    
    // Clear the winner on the wheel so everyone can see updated state
    if (politburoWheelRef.value?.clearWinner) {
      politburoWheelRef.value.clearWinner()
    }
  }
})

socket.on('closePolitburoModal', () => {
  console.log('[closePolitburoModal] Closing modal for all participants')
  politburoWheelModal.value && politburoWheelModal.value.hide()
  resetPolitburoSelection()
})

socket.on('biddingTallyUpdate', (data) => {
  console.log('[biddingTallyUpdate]', data)
  biddingTally.value = data.tally || {}
  dictator_bid_amounts.value = data.bid_amounts || {}
})

socket.on('dictatorWinner', (data) => {
  console.log('[dictatorWinner]', data)
  biddingActive.value = false
  dictatorWinner.value = data.winner_name
  biddingLeaderboard.value = data.leaderboard || []
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
function openAdminControlsModal() {
  adminControlsModalRef.value?.show()
}

function openWheelSpinner(options) {
  // If called for Communism, open the politburo wheel modal
  if (options?.forCommunism) {
    politburoWheelModal.value?.show()
  } else {
    wheelSpinnerRef.value?.open()
  }
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
  
  // Reset winner state
  selectedWinner.value = null
  winnerSet.value = false
  settingWinner.value = false
  
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
      
      // Generate color palette for 8 players - distinct, high-contrast colors
      const colors = [
        '#FF4136', // Red
        '#2ECC40', // Green
        '#0074D9', // Blue
        '#FF851B', // Orange
        '#B10DC9', // Purple
        '#FFDC00', // Yellow
        '#39CCCC', // Teal
        '#F012BE'  // Magenta
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
            y: s.clock_minutes
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
                const formatClock = (minutes) => {
                  const days = Math.floor(minutes / 1440)
                  const hours = Math.floor((minutes % 1440) / 60)
                  const mins = minutes % 60
                  return `${String(days).padStart(2, '0')}•${String(hours).padStart(2, '0')}•${String(mins).padStart(2, '0')}`
                }
                const formattedTime = formatClock(minutesValue)
                return `Time: ${formattedTime}`
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

// Winner selection
async function confirmWinner() {
  if (!selectedWinner.value || settingWinner.value) return
  
  const roomId = store.state.auth.roomId
  console.log('[SetWinner] Setting winner:', { roomId, winnerId: selectedWinner.value })
  
  settingWinner.value = true
  try {
    const resp = await RoomListService.setWinner({ 
      roomId, 
      winnerId: selectedWinner.value 
    })
    console.log('[SetWinner] Response:', resp?.data)
    winnerSet.value = true
  } catch (e) {
    console.error('[SetWinner] Failed:', e)
    alert(e.response?.data?.errors || 'Failed to set winner')
  } finally {
    settingWinner.value = false
  }
}

function getParticipantName(userId) {
  const player = activePlayers.value.find(p => p.user_id === userId)
  return player?.username || `User ${userId}`
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

function uClock(time) {
  socket.emit('updateClock', JSON.stringify(time))
}

// Admin check: ONLY the room creator can change gov (or leave superuser id 1 if you want)
const isAdmin = computed(() => {
  if (!roomOwnerId.value) return false
  return currentUserId.value === roomOwnerId.value
  // If you also want to allow global admin (id === 1), use:
  // return currentUserId.value === roomOwnerId.value || currentUserId.value === 1
})

const currentGovernmentName = computed(() => {
  return roomGovernment.value?.type || 'Unknown'
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
  console.log('[partakeGovVote] Admin starting new voting session')
  // Admin emits startVoting to initiate a secret voting session
  socket.emit('startVoting', JSON.stringify({ 
    question: 'Cast your vote on the current matter' 
  }))
}

function submitVote(choice) {
  console.log('[submitVote] Casting vote:', choice)
  currentUserVote.value = choice
  socket.emit('partakeGovVote', JSON.stringify({ choice: choice }))
}

function concludeVote() {
  console.log('[concludeVote] Admin concluding voting')
  socket.emit('concludeVoting')
}

function confirmGovVote() {
  // Legacy function - kept for compatibility but not used in new flow
  if (selectedVoteOption.value) {
    console.log('Casting vote:', selectedVoteOption.value)
    socket.emit('partakeGovVote', JSON.stringify({ choice: selectedVoteOption.value }))
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

// Pay jail fee handler -> emits "getOutOfJail"
function getOutOfJail() {
  if (isPayingJail.value) return
  isPayingJail.value = true
  try {
    console.log('[GetOutOfJail] emit getOutOfJail')
    socket.emit('getOutOfJail')
  } catch (e) {
    console.error('[GetOutOfJail] emit failed', e)
  } finally {
    setTimeout(() => { isPayingJail.value = false }, 600)
  }
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

// Politburo wheel functions
const politburoWheelRef = ref(null)

function handlePolitburoSpinRequest() {
  // Called when the spin button inside the wheel is clicked
  console.log('[handlePolitburoSpinRequest] Spin requested')
  
  if (politburoMembers.value.length >= 2 || isSpinningPolitburo.value) {
    console.log('[handlePolitburoSpinRequest] Blocking: already have 2 members or spinning in progress')
    return
  }
  
  if (!politburoWheelRef.value) {
    console.error('[Politburo] Wheel ref not available')
    return
  }
  
  // Generate spin data (rotation) on admin side
  const spinData = politburoWheelRef.value.generateSpinData()
  if (!spinData) {
    console.error('[Politburo] Could not generate spin data')
    return
  }
  
  isSpinningPolitburo.value = true
  
  // Broadcast to all players with the pre-determined rotation
  const roomId = store.state.auth.roomId
  socket.emit('startPolitburoSpin', JSON.stringify({ 
    room_id: roomId,
    rotation: spinData.rotation 
  }))
  
  // The socket listener will apply the rotation for everyone including admin
}

function spinForNextMember() {
  // Legacy function - now redirects to handlePolitburoSpinRequest
  handlePolitburoSpinRequest()
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
    
    // Broadcast the update to all room participants
    socket.emit('updatePolitburoMembers', JSON.stringify({ 
      members: politburoMembers.value 
    }))
  } else {
    console.log('[Politburo] Member already in list:', participant.username)
  }
  
  // Clear the winner state so wheel can be spun again
  if (politburoWheelRef.value?.clearWinner) {
    politburoWheelRef.value.clearWinner()
  }
}

function spinAgain() {
  // Clear winner and spin again
  if (politburoWheelRef.value?.clearWinner) {
    politburoWheelRef.value.clearWinner()
  }
  
  // Trigger another spin after brief delay
  setTimeout(() => {
    handlePolitburoSpinRequest()
  }, 100)
}

function resetPolitburoSelection() {
  politburoMembers.value = []
  balanceBooksOnSave.value = false
  govError.value = ''
  showWheelResult.value = false
  currentWheelWinner.value = null
  
  // Clear wheel winner state
  if (politburoWheelRef.value?.clearWinner) {
    politburoWheelRef.value.clearWinner()
  }
  
  // Broadcast reset to all players
  socket.emit('updatePolitburoMembers', JSON.stringify({ members: [] }))
}

function cancelPolitburoSelection() {
  resetPolitburoSelection()
  politburoWheelModal.value && politburoWheelModal.value.hide()
}

function savePolitburoSelection() {
  if (politburoMembers.value.length !== 2) {
    govError.value = 'Must select exactly 2 politburo members'
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
    
    // Broadcast to close modal for all participants
    socket.emit('closePolitburoModal')
    
    // If balance books is checked, wait for government update then balance
    if (balanceBooksOnSave.value) {
      // Wait longer to ensure government is saved first
      setTimeout(() => {
        console.log('[Politburo] Triggering balance books')
        socket.emit('balanceBooks')
      }, 1000)
    }
    
    // Modal closing and reset is handled by the closePolitburoModal socket event for everyone
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
  background: #0B0F19;
  padding: 0;
}

.bv-example-row {
  width: 100% !important;
  max-width: 100% !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
}

.dropped-table {
  opacity: 0.6;
}

.dropped-row {
  text-decoration: line-through;
  background-color: rgba(241, 245, 249, 0.05) !important;
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
  background: #1A1F2E !important;
  border: 2px solid #22D3EE !important;
  color: #F1F5F9 !important;
  font-weight: 700 !important;
  border-radius: 8px !important;
  transition: all 0.2s ease !important;
  font-size: 1.05em !important;
}

.addremovebuttonClock:hover {
  transform: translateY(-2px) !important;
  border-color: #EAB308 !important;
  color: #EAB308 !important;
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
  color: #F1F5F9;
  font-size: 2em;
  font-weight: 700;
  margin-bottom: 20px;;
  font-family: 'Barlow Condensed';
}

/* Clock styling with arm background effect */
.itemRow #clock {
  font-size: 4em;
  font-weight: bold;
  color: #00ff00;
  font-family: 'Barlow Condensed', monospace;
  background: radial-gradient(ellipse at center, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.9) 100%);
  border: 3px solid #000;
  border-radius: 15px;
  padding: 26px 44px;
  display: inline-block;
  letter-spacing: 8px;;
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

/* Table styling - core table rules only */

.table thead tr {
  height: 50px;
  background: #0B0F19 !important;
  overflow: hidden;
  max-height: 50px;
}

.table thead th {
  vertical-align: middle;
  height: 50px;
  border: 1px solid #22D3EE !important;
  color: #EAB308 !important;
  font-weight: 700 !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;;
  text-align: center !important;
  font-family: 'Barlow Condensed' !important;
  font-size: 1.15em !important;
  background: #1A1F2E !important;
  padding: 4px 13px !important;
  line-height: 20px;
  overflow: hidden;
  max-height: 50px;
}

.table tbody {
  background: #1A1F2E !important;
}

.table tbody td {
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

.table tbody tr {
  transition: background-color 0.2s ease;
  background: #1A1F2E !important;
  height: 60px !important;
  min-height: 60px !important;
  max-height: 60px !important;
  overflow: hidden !important;
}

.table tbody tr:hover {
  background-color: rgba(241, 245, 249, 0.1) !important;
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
  color: #F1F5F9;
  font-weight: 700;;
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

.job-controls { margin-right: 0px; }

.govt-label {
  color: #F1F5F9 !important;
  font-weight: 700 !important;;
  font-family: 'Barlow Condensed' !important;
  font-size: 1.9em !important;
  padding: 13px 18px !important;
  display: inline-block !important;
  letter-spacing: 1px !important;
  text-transform: uppercase;
}

.room__max-collectables {
  color: #F1F5F9 !important;
  font-weight: 600 !important;
  font-size: 1em !important;
  text-align: center !important;
  margin-top: 12px !important;
  margin-bottom: 24px !important;
  letter-spacing: 0.5px !important;
}

.govt-dropdown-wrapper {
  margin-left: 85px;
  display: inline-flex;
  align-items: center;
  gap: 0;
}

.govt-dropdown-wrapper label {
  color: #F1F5F9 !important;
  font-weight: 700 !important;
  font-size: 1.8em !important;
  margin: 0 !important;;
  font-family: 'Barlow Condensed' !important;
  letter-spacing: 1px !important;
  text-transform: uppercase;
}

.govt-dropdown-wrapper select {
  font-size: 1.5em !important;
  font-weight: 700 !important;
  padding: 0 !important;
  color: #F1F5F9 !important;
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
  color: #F1F5F9 !important;
  font-family: 'Barlow Condensed' !important;
  cursor: pointer !important;
  width: auto !important;
  height: auto !important;
  line-height: 1.2 !important;
  vertical-align: middle !important;;
  text-transform: uppercase !important;
}

.govt-select-box .govt-arrow {
  position: absolute;
  right: 90px;
  top: 11px;
  pointer-events: none;
  font-size: 1.1em;
  color: #F1F5F9 !important;
  margin: 0 !important;
  line-height: 1.2;
}

.govt-dropdown-wrapper select option {
  background-color: #001535 !important;
  color: #F1F5F9 !important;
  font-weight: 700 !important;
}

.perk-label {
  font-weight: 600;
  font-size: 14px;
  margin: 0;
  line-height: 38px;
  color: #F1F5F9;
}

.perk-btn {
  padding: 8px 12px;
  border: 2px solid rgba(241, 245, 249, 0.3);
  background: #1A1F2E;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: #F1F5F9;
  height: 38px;
  min-width: 38px;
}

.perk-btn:hover {
  border-color: #F1F5F9;
  background: rgba(241, 245, 249, 0.1);
  transform: translateY(-1px);;
}

.perk-btn.active {
  border-color: #F1F5F9;
  background: rgba(241, 245, 249, 0.2);
  color: #F1F5F9;
  font-weight: 600;;
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
  background: #1A1F2E !important;
  border: 2px solid #F1F5F9 !important;
  color: #F1F5F9 !important;
  font-weight: 600 !important;
  border-radius: 8px !important;;
  transition: all 0.2s ease !important;
  padding: 12px 20px !important;
}

.market-btn:hover {
  transform: translateY(-2px) !important;;;
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
  background: #1A1F2E !important;
  border: 2px solid #F1F5F9 !important;
  color: #F1F5F9 !important;
  font-weight: 600 !important;
  border-radius: 8px !important;;
  transition: all 0.3s ease !important;
  padding: 10px 16px !important;
  font-size: 0.95em !important;
}

.senate-btn:hover {
  transform: translateY(-2px) !important;;;
}

/* Special glow for the Show/Hide Senate Tabs button */
.senate-controls .senate-btn:nth-child(3) {
  animation: senateBtnGlow 2s ease-in-out infinite;
}

.senate-controls .senate-btn:nth-child(3):hover {
  animation: none;
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
  color: #EAB308 !important;     /* Match other header colors */
  text-transform: uppercase;
  letter-spacing: 0.5px;
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
  border-width: 2px;
  background: #1A1F2E !important;
  border-color: #22D3EE !important;
  color: #F1F5F9 !important;
  transition: all 0.2s ease;
}

.bleed-btn:hover,
.heat-btn:hover {
  border-color: #EAB308 !important;
  color: #EAB308 !important;
  transform: translateY(-1px);
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
  border: 1px solid rgba(241, 245, 249, 0.3);
  background: transparent;
}

.approval-empty,
.vote-empty {
  color: #666;
  background: rgba(241, 245, 249, 0.05);
  border-color: rgba(241, 245, 249, 0.2);
}

.approval-approve {
  background: rgba(241, 245, 249, 0.2);
  color: #F1F5F9;
  border-color: rgba(241, 245, 249, 0.5);
}

.approval-reject {
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
  background: rgba(241, 245, 249, 0.2);
  color: #F1F5F9;
  border-color: rgba(241, 245, 249, 0.5);
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
  color: #EAB308 !important;
  font-weight: 700 !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;;
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
  color: #EAB308 !important;
  font-weight: 700 !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;;
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
  color: #EAB308 !important;
  font-weight: 700 !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;;
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
  color: #EAB308 !important;
  font-weight: 700 !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;;
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
  background: #1A1F2E !important;
  border: 2px solid #EAB308 !important;
  color: #EAB308 !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
  padding: 8px 20px !important;
  transition: all 0.2s ease !important;
  font-size: 0.9em !important;
  min-width: 150px;
}

.btn-get-paid:hover {
  border-color: #F1F5F9 !important;
  color: #F1F5F9 !important;
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
  background: #1A1F2E;
  border: 1px solid rgba(241, 245, 249, 0.2);
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
  background: #1A1F2E;
  border: 1px solid rgba(241, 245, 249, 0.1);
  border-radius: 4px;
  font-size: 0.9em;
  color: #F1F5F9;
}

.tally-item.bid-tally-row {
  padding: 12px 16px;
  justify-content: space-between;
  align-items: center;
  border: 2px solid rgba(235, 163, 8, 0.5);
  background: rgba(235, 163, 8, 0.05);
}

.tally-item.bid-tally-row .participant-name {
  font-weight: 600;
  color: #F1F5F9;
  flex: 1;
  text-align: left;
}

.tally-item.bid-tally-row .bid-amount {
  font-size: 1.2em;
  font-weight: 700;
  color: #EAB308;
  min-width: 80px;
  text-align: center;
  margin-right: 15px;
  font-family: 'Courier New', monospace;
  letter-spacing: 2px;
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
  color: #F1F5F9;
  font-family: 'Barlow Condensed';;
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
  color: #F1F5F9;
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
  color: #F1F5F9;;
}

.time-buttons .btn {
  padding: 6px 12px;
  font-weight: bold;
}

/* Dictator Bidding Modal Styles */
.dictator-bid-container {
  padding: 10px 0;
}

.your-time-section {
  background: #0B0F19;
  border: 2px solid #22D3EE;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}

.your-time-label {
  margin: 0 0 10px 0;
  font-size: 1em;
  color: #F1F5F9;
  font-weight: 600;
}

.your-time-display {
  font-size: 2.5em;
  font-weight: bold;
  font-family: 'Barlow Condensed', monospace;
  letter-spacing: 4px;
  color: #22D3EE;
}

.bid-display-section {
  background: #1A1F2E;
  border: 2px solid rgba(241, 245, 249, 0.3);
  border-radius: 12px;
  padding: 30px 20px;
  text-align: center;
  color: #F1F5F9;
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
  letter-spacing: 8px;;
  color: #F1F5F9;
}

.bid-buttons-section {
  background: #1A1F2E;
  border: 1px solid rgba(241, 245, 249, 0.2);
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
  background: #1A1F2E;
  border-color: #F1F5F9;
  color: #F1F5F9;;
}

.bid-btn:hover {
  transform: translateY(-2px);;;
}

.bid-btn:active {
  transform: translateY(0);
}

.place-bid-btn {
  padding: 16px;
  font-size: 1.1em;
  letter-spacing: 1px;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #FF6B3D 0%, #FF8F3D 100%) !important;
  border: 3px solid #FFB81C !important;
  color: white !important;
  font-weight: 700;
  text-transform: uppercase;
  box-shadow: 0 4px 15px rgba(255, 107, 61, 0.4);
}

.place-bid-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(255, 107, 61, 0.6);
  border-color: white !important;
}

.bidding-status-section {
  background: #1A1F2E;
  border-radius: 12px;
  padding: 20px;
  border-left: 4px solid #F1F5F9;
}

.bidding-status-section h6 {
  color: #F1F5F9;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-size: 0.85em;;
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

/* Government Vote Modal Styles */
.vote-container {
  text-align: center;
  padding: 20px;
}

.vote-title {
  color: #EAB308;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 30px;
}

.vote-buttons-row {
  display: flex;
  gap: 15px;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 30px;
}

.vote-button {
  flex: 1;
  min-width: 120px;
  padding: 20px 15px;
  font-size: 1.1em;
  font-weight: 700;
  border: 3px solid;
  border-radius: 8px;
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.vote-yes {
  background: #22c55e !important;
  border-color: #16a34a !important;
  color: #ffffff !important;
}

.vote-yes:hover {
  background: #16a34a !important;
  transform: scale(1.05);
  box-shadow: 0 8px 20px rgba(34, 197, 94, 0.5);
}

.vote-yes.vote-selected {
  background: #15803d !important;
  color: white !important;
  box-shadow: 0 10px 30px rgba(34, 197, 94, 0.6);
}

.vote-no {
  background: #ef4444 !important;
  border-color: #dc2626 !important;
  color: #ffffff !important;
}

.vote-no:hover {
  background: #dc2626 !important;
  transform: scale(1.05);
  box-shadow: 0 8px 20px rgba(239, 68, 68, 0.5);
}

.vote-no.vote-selected {
  background: #b91c1c !important;
  color: white !important;
  box-shadow: 0 10px 30px rgba(239, 68, 68, 0.6);
}

.vote-abstain {
  background: #f59e0b !important;
  border-color: #d97706 !important;
  color: #ffffff !important;
}

.vote-abstain:hover {
  background: #d97706 !important;
  transform: scale(1.05);
  box-shadow: 0 8px 20px rgba(245, 158, 11, 0.5);
}

.vote-abstain.vote-selected {
  background: #b45309 !important;
  color: white !important;
  box-shadow: 0 10px 30px rgba(245, 158, 11, 0.6);
}

.vote-tally {
  border-top: 2px solid rgba(235, 163, 8, 0.3);
  padding-top: 20px;
}

.vote-tally-title {
  color: #EAB308;
  font-weight: 700;
  margin-bottom: 15px;
  text-transform: uppercase;
}

.tally-row {
  display: flex;
  gap: 15px;
  justify-content: center;
  flex-wrap: wrap;
}

.tally-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 15px 20px;
  border-radius: 8px;
  min-width: 80px;
  border: 2px solid;
}

.tally-item.yes {
  background: rgba(34, 211, 102, 0.1);
  border-color: #22d366;
}

.tally-item.no {
  background: rgba(255, 77, 77, 0.1);
  border-color: #ff4d4d;
}

.tally-item.abstain {
  background: rgba(255, 193, 7, 0.1);
  border-color: #ffc107;
}

.tally-item.pending {
  background: rgba(241, 245, 249, 0.1);
  border-color: #a0aec0;
}

.tally-count {
  font-size: 1.5em;
  font-weight: 700;
  color: #EAB308;
  display: block;
  margin-bottom: 5px;
}

.tally-label {
  font-size: 0.75em;
  text-transform: uppercase;
  color: #F1F5F9;
  font-weight: 600;
}

/* Secret Voting Modal Styles */
.vote-question-box {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border: 2px solid #3b82f6;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 25px;
  display: flex;
  align-items: center;
  gap: 15px;
}

.vote-question-icon {
  font-size: 2em;
}

.vote-question-text {
  color: #f1f5f9;
  font-size: 1.2em;
  font-weight: 500;
  margin: 0;
}

.vote-section {
  margin-bottom: 25px;
}

.vote-section-title {
  color: #EAB308;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.vote-count-badge {
  background: #3b82f6;
  color: white;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.8em;
  font-weight: 600;
}

.vote-icon {
  display: block;
  font-size: 1.5em;
  margin-bottom: 5px;
}

.vote-submitted-box {
  background: linear-gradient(135deg, #065f46 0%, #064e3b 100%);
  border: 2px solid #10b981;
  border-radius: 12px;
  padding: 30px;
  text-align: center;
  margin-bottom: 25px;
}

.vote-submitted-icon {
  font-size: 3em;
  display: block;
  margin-bottom: 15px;
}

.vote-submitted-text {
  color: #ecfdf5;
  font-size: 1.2em;
  font-weight: 600;
  margin-bottom: 5px;
}

.vote-submitted-hint {
  color: #a7f3d0;
  font-size: 0.9em;
  margin: 0;
}

.vote-participants-section {
  background: #0f172a;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}

.vote-participants-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.vote-participant-card {
  background: #1e293b;
  border: 2px solid #334155;
  border-radius: 8px;
  padding: 12px 15px;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.3s ease;
}

.vote-participant-card.has-voted {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

.participant-status-icon {
  font-size: 1.3em;
}

.participant-name {
  color: #f1f5f9;
  font-weight: 600;
  flex: 1;
}

.participant-vote-status {
  font-size: 0.85em;
  color: #94a3b8;
}

.vote-participant-card.has-voted .participant-vote-status {
  color: #10b981;
}

.vote-admin-section {
  text-align: center;
  padding-top: 20px;
}

.vote-divider {
  border-color: rgba(59, 130, 246, 0.3);
  margin-bottom: 20px;
}

.conclude-vote-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
  border: none !important;
  padding: 15px 40px !important;
  font-size: 1.1em !important;
  font-weight: 700 !important;
  border-radius: 10px !important;
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4) !important;
  transition: all 0.3s ease !important;
}

.conclude-vote-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 35px rgba(59, 130, 246, 0.5) !important;
}

.conclude-icon {
  margin-right: 10px;
}

.admin-hint {
  color: #94a3b8;
  font-size: 0.85em;
  margin-top: 10px;
}

/* Vote Results Modal Styles */
.vote-results-container {
  padding: 10px;
}

.vote-outcome-banner {
  padding: 25px;
  border-radius: 12px;
  text-align: center;
  margin-bottom: 25px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
}

.vote-outcome-banner.outcome-passed {
  background: linear-gradient(135deg, #065f46 0%, #064e3b 100%);
  border: 3px solid #10b981;
}

.vote-outcome-banner.outcome-rejected {
  background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%);
  border: 3px solid #ef4444;
}

.vote-outcome-banner.outcome-tie {
  background: linear-gradient(135deg, #78350f 0%, #92400e 100%);
  border: 3px solid #f59e0b;
}

.outcome-icon {
  font-size: 2.5em;
}

.outcome-text {
  font-size: 2em;
  font-weight: 800;
  color: white;
  text-transform: uppercase;
  letter-spacing: 3px;
}

.vote-counts-row {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-bottom: 30px;
}

.vote-count-box {
  flex: 1;
  max-width: 150px;
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  border: 3px solid;
}

.vote-count-box.yes {
  background: rgba(34, 197, 94, 0.2);
  border-color: #22c55e;
}

.vote-count-box.no {
  background: rgba(239, 68, 68, 0.2);
  border-color: #ef4444;
}

.vote-count-box.abstain {
  background: rgba(245, 158, 11, 0.2);
  border-color: #f59e0b;
}

.count-number {
  font-size: 2.5em;
  font-weight: 800;
  display: block;
}

.vote-count-box.yes .count-number {
  color: #22c55e;
}

.vote-count-box.no .count-number {
  color: #ef4444;
}

.vote-count-box.abstain .count-number {
  color: #f59e0b;
}

.count-label {
  font-size: 0.85em;
  text-transform: uppercase;
  font-weight: 600;
  color: #94a3b8;
}

.individual-votes-section {
  background: #0f172a;
  border-radius: 12px;
  padding: 20px;
}

.votes-title {
  color: #EAB308;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 15px;
}

.individual-votes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}

.individual-vote-card {
  padding: 12px 15px;
  border-radius: 8px;
  border: 2px solid;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.individual-vote-card.vote-yes {
  background: rgba(16, 185, 129, 0.15);
  border-color: #10b981;
}

.individual-vote-card.vote-no {
  background: rgba(239, 68, 68, 0.15);
  border-color: #ef4444;
}

.individual-vote-card.vote-abstain {
  background: rgba(245, 158, 11, 0.15);
  border-color: #f59e0b;
}

.voter-name {
  color: #f1f5f9;
  font-weight: 600;
}

.voter-choice {
  font-size: 0.85em;
  font-weight: 700;
}

.individual-vote-card.vote-yes .voter-choice {
  color: #10b981;
}

.individual-vote-card.vote-no .voter-choice {
  color: #ef4444;
}

.individual-vote-card.vote-abstain .voter-choice {
  color: #f59e0b;
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

/* Admin Controls Modal Styles */
.admin-controls-container {
  padding: 20px;
}

.admin-controls-group {
  background: #1A1F2E;
  border: 1px solid rgba(235, 163, 8, 0.3);
  border-radius: 12px;
  padding: 20px;
}

.admin-controls-group h5 {
  color: #EAB308;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-family: 'Barlow Condensed';
  font-size: 1.3em;
  margin-bottom: 15px;
}

.admin-controls-group .btn {
  font-weight: 700;
  border: 2px solid;
  border-radius: 8px;
  padding: 12px 20px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  transition: all 0.3s ease;
  font-size: 1.05em;
}

.admin-controls-group .btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
  border-width: 2px;
}

.admin-controls-group .btn-primary {
  background: #0D47A1 !important;
  border-color: #42A5F5 !important;
  color: #E3F2FD !important;
}

.admin-controls-group .btn-primary:hover {
  background: #1565C0 !important;
  border-color: #64B5F6 !important;
  color: #F5F5F5 !important;
}

.admin-controls-group .btn-info {
  background: #00838F !important;
  border-color: #4DB6AC !important;
  color: #E0F2F1 !important;
}

.admin-controls-group .btn-info:hover {
  background: #00A8B4 !important;
  border-color: #80CBC4 !important;
  color: #F5F5F5 !important;
}

.admin-controls-group .btn-success {
  background: #2E7D32 !important;
  border-color: #66BB6A !important;
  color: #E8F5E9 !important;
}

.admin-controls-group .btn-success:hover {
  background: #388E3C !important;
  border-color: #81C784 !important;
  color: #F5F5F5 !important;
}

.admin-controls-group .btn-danger {
  background: #C62828 !important;
  border-color: #EF5350 !important;
  color: #FFEBEE !important;
}

.admin-controls-group .btn-danger:hover {
  background: #D32F2F !important;
  border-color: #F44336 !important;
  color: #F5F5F5 !important;
}

.admin-controls-group .mb-4 {
  margin-bottom: 20px;
}

.admin-controls-group .mb-4:last-child {
  margin-bottom: 0;
}

.admin-controls-group .mb-2 {
  margin-bottom: 12px;
}

/* Government Display Styles */
.room-government__row {
  margin-top: 12px;
  margin-bottom: 12px;
}

.room-government__container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
}

.room-government__control-group {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.room-government__label {
  color: #F1F5F9 !important;
  font-weight: 700 !important;
  font-family: 'Barlow Condensed' !important;
  font-size: 1.9em !important;
  padding: 13px 18px !important;
  display: inline-block !important;
  letter-spacing: 1px !important;
  text-transform: uppercase;
}

.room-government__label strong {
  color: #60a5fa !important;
  margin-left: 8px;
}
</style>

<style>
/* Hide default modal footer for modals that don't need it */
#govVoteModal .modal-footer,
#dictatorBiddingModal .modal-footer,
#dictatorBiddingWinnerModal .modal-footer,
#politburoWheelModal .modal-footer {
  display: none !important;
}

/* Vote Modal Button Overrides - Force visible text on solid backgrounds */
#govVoteModal .vote-button.vote-yes,
#govVoteModal .vote-button.vote-yes.btn-success,
.vote-button.vote-yes {
  background-color: #22c55e !important;
  border-color: #16a34a !important;
  color: #ffffff !important;
}

#govVoteModal .vote-button.vote-yes:hover {
  background-color: #16a34a !important;
}

#govVoteModal .vote-button.vote-no,
#govVoteModal .vote-button.vote-no.btn-danger,
.vote-button.vote-no {
  background-color: #ef4444 !important;
  border-color: #dc2626 !important;
  color: #ffffff !important;
}

#govVoteModal .vote-button.vote-no:hover {
  background-color: #dc2626 !important;
}

#govVoteModal .vote-button.vote-abstain,
#govVoteModal .vote-button.vote-abstain.btn-warning,
.vote-button.vote-abstain {
  background-color: #f59e0b !important;
  border-color: #d97706 !important;
  color: #ffffff !important;
}

#govVoteModal .vote-button.vote-abstain:hover {
  background-color: #d97706 !important;
}

/* Ensure strong text inside buttons is also white */
#govVoteModal .vote-button strong,
.vote-button strong {
  color: #ffffff !important;
}

/* Ensure vote icon inside buttons is also white */
#govVoteModal .vote-button .vote-icon,
.vote-button .vote-icon {
  color: #ffffff !important;
}

/* Hide X close button on dictator bidding modal */
#dictatorBiddingModal .btn-close,
#dictatorBiddingModal .modal-header .close,
#dictatorBiddingModal .modal-header button[aria-label="Close"] {
  display: none !important;
}

/* Compact Dictator Bidding Modal Styles */
.dictator-bid-container-compact {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bid-top-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.your-time-compact,
.bid-amount-compact {
  flex: 1;
  background: #1e293b;
  border-radius: 8px;
  padding: 12px;
  text-align: center;
  border: 1px solid #475569;
}

.time-label,
.bid-label {
  display: block;
  font-size: 0.75rem;
  color: #94a3b8;
  text-transform: uppercase;
  margin-bottom: 4px;
}

.time-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #22d3ee;
  font-family: 'Barlow Condensed', sans-serif;
}

.bid-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #f97316;
  font-family: 'Barlow Condensed', sans-serif;
}

.bid-buttons-compact {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 6px;
}

.bid-buttons-compact .btn {
  padding: 8px 4px;
  font-size: 0.85rem;
  font-weight: 600;
}

.place-bid-btn-compact {
  padding: 10px;
  font-size: 1rem;
}

.bidding-status-compact {
  background: #334155;
  border-radius: 8px;
  padding: 10px;
}

.status-header {
  font-size: 0.75rem;
  color: #94a3b8;
  text-transform: uppercase;
  margin-bottom: 8px;
  font-weight: 600;
}

.bidding-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 150px;
  overflow-y: auto;
}

.bid-participant {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #1e293b;
  padding: 6px 10px;
  border-radius: 4px;
}

.p-name {
  flex: 1;
  color: #f1f5f9;
  font-size: 0.9rem;
}

.p-bid {
  color: #f97316;
  font-weight: 600;
  margin-right: 8px;
}

.p-status {
  font-size: 1rem;
}

.p-status.done {
  color: #22c55e;
}

.p-status.waiting {
  color: #eab308;
}

.conclude-btn-compact {
  margin-top: 4px;
  padding: 10px;
}

/* Auction Results Modal Styles */
.auction-results {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.winner-banner {
  text-align: center;
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  border: 2px solid #f97316;
  border-radius: 12px;
  padding: 16px;
}

.winner-banner .crown {
  font-size: 2rem;
  display: block;
  margin-bottom: 4px;
}

.winner-banner h3 {
  color: #f97316;
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
  font-family: 'Barlow Condensed', sans-serif;
}

.winner-banner p {
  color: #94a3b8;
  margin: 4px 0 0;
  font-size: 0.9rem;
}

.leaderboard-section {
  background: #334155;
  border-radius: 8px;
  padding: 12px;
}

.leaderboard-header {
  font-size: 0.75rem;
  color: #94a3b8;
  text-transform: uppercase;
  font-weight: 600;
  margin-bottom: 10px;
}

.leaderboard-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.leaderboard-row {
  display: flex;
  align-items: center;
  background: #1e293b;
  padding: 8px 12px;
  border-radius: 6px;
  transition: all 0.2s;
}

.leaderboard-row.winner-row {
  background: linear-gradient(90deg, #451a03 0%, #1e293b 100%);
  border: 1px solid #f97316;
}

.leaderboard-row .rank {
  width: 24px;
  height: 24px;
  background: #475569;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  color: #f1f5f9;
  margin-right: 10px;
}

.leaderboard-row.winner-row .rank {
  background: #f97316;
  color: #000;
}

.leaderboard-row .lb-name {
  flex: 1;
  color: #f1f5f9;
  font-size: 0.95rem;
}

.leaderboard-row.winner-row .lb-name {
  color: #f97316;
  font-weight: 600;
}

.leaderboard-row .lb-bid {
  color: #22d3ee;
  font-weight: 600;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1rem;
}

/* Politburo Selection Modal Styles */
.politburo-selection-compact {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.selected-members-banner {
  background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%);
  border-radius: 10px;
  padding: 12px;
  border: 2px solid #dc2626;
}

.members-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.members-icon {
  font-size: 1.3rem;
  color: #fbbf24;
}

.members-title {
  flex: 1;
  font-size: 1rem;
  font-weight: 600;
  color: #f1f5f9;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.members-count {
  background: #450a0a;
  padding: 3px 10px;
  border-radius: 20px;
  font-weight: 700;
  color: #fbbf24;
  font-size: 0.85rem;
}

.members-slots {
  display: flex;
  gap: 10px;
}

.member-slot {
  flex: 1;
  background: #450a0a;
  border: 2px dashed #dc2626;
  border-radius: 8px;
  padding: 8px 12px;
  text-align: center;
  font-weight: 600;
  color: #94a3b8;
  transition: all 0.3s;
}

.member-slot.filled {
  background: #16a34a;
  border: 2px solid #22c55e;
  color: #f1f5f9;
}

.member-slot .empty-slot {
  font-style: italic;
  color: #6b7280;
}

.wheel-container-politburo {
  background: #1e293b;
  border-radius: 10px;
  padding: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.politburo-admin-controls {
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: #334155;
  border-radius: 10px;
  padding: 12px;
}

.control-row {
  display: flex;
  gap: 10px;
}

.control-row-small {
  display: flex;
  justify-content: flex-end;
}

.control-row .spin-btn {
  flex: 1;
}

.balance-books-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #475569;
  transition: 0.3s;
  border-radius: 24px;
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

.toggle-switch input:checked + .toggle-slider {
  background-color: #22c55e;
}

.toggle-switch input:checked + .toggle-slider:before {
  transform: translateX(20px);
}

.toggle-label {
  color: #f1f5f9;
  font-size: 0.9rem;
}

.final-actions {
  display: flex;
  gap: 10px;
}

.final-actions .complete-btn {
  flex: 1;
  background-color: #22c55e !important;
  border-color: #22c55e !important;
  color: #ffffff !important;
}

.final-actions .complete-btn:disabled {
  background-color: #475569 !important;
  border-color: #475569 !important;
  color: #94a3b8 !important;
}

/* Politburo action buttons - Add to Politburo and Spin Again */
.politburo-action-btn {
  color: #ffffff !important;
  font-weight: 600 !important;
}

.politburo-action-btn.btn-success {
  background-color: #22c55e !important;
  border-color: #16a34a !important;
  color: #ffffff !important;
}

.politburo-action-btn.btn-success:hover {
  background-color: #16a34a !important;
  border-color: #15803d !important;
}

.politburo-action-btn.btn-secondary {
  background-color: #475569 !important;
  border-color: #64748b !important;
  color: #ffffff !important;
}

.politburo-action-btn.btn-secondary:hover {
  background-color: #64748b !important;
  border-color: #94a3b8 !important;
}

.watching-message {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: #334155;
  border-radius: 8px;
  color: #94a3b8;
  font-size: 0.95rem;
}

.watching-message .watching-icon {
  font-size: 1.2rem;
}

/* Winner Selection Styles */
.winner-selection-section {
  border-top: 1px solid #334155;
  padding-top: 20px;
}

.winner-selection-card {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border: 2px solid #eab308;
  border-radius: 12px;
  padding: 20px;
}

.winner-title {
  color: #eab308;
  font-weight: 700;
  font-size: 1.2rem;
  margin-bottom: 8px;
}

.winner-description {
  color: #94a3b8;
  font-size: 0.9rem;
  margin-bottom: 16px;
}

.winner-form {
  display: flex;
  align-items: center;
  gap: 12px;
}

.winner-select {
  flex: 1;
  padding: 10px 14px;
  background: #0f172a;
  border: 2px solid #334155;
  border-radius: 8px;
  color: #f1f5f9;
  font-size: 1rem;
  cursor: pointer;
  transition: border-color 0.2s;
}

.winner-select:hover,
.winner-select:focus {
  border-color: #eab308;
  outline: none;
}

.winner-select option {
  background: #1e293b;
  color: #f1f5f9;
}

.winner-confirmed {
  display: flex;
  align-items: center;
  justify-content: center;
}

.winner-badge {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  color: #ffffff;
  font-weight: 600;
  font-size: 1.1rem;
  padding: 12px 24px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
</style>














