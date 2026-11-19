<template>
  <div>
    <!-- Main Admin Controls Modal -->
    <b-modal
      ref="modal"
      id="adminControlsModal"
      title="Admin Controls"
      size="md"
      centered
      no-footer
    >
      <section class="admin-section">
        <h6 class="admin-section__label">Game</h6>
        <div class="admin-list">
          <button
            v-for="action in actions"
            :key="action.title"
            type="button"
            class="admin-action"
            @click="action.run"
          >
            <span class="admin-action__icon" aria-hidden="true">{{ action.icon }}</span>
            <span class="admin-action__text">
              <span class="admin-action__title">{{ action.title }}</span>
              <span class="admin-action__desc">{{ action.desc }}</span>
            </span>
            <span class="admin-action__chevron" aria-hidden="true">›</span>
          </button>
        </div>
      </section>

      <section class="admin-section admin-section--danger">
        <h6 class="admin-section__label">Danger zone</h6>
        <button type="button" class="admin-action admin-action--danger" @click="handleEndGame">
          <span class="admin-action__icon" aria-hidden="true">🏁</span>
          <span class="admin-action__text">
            <span class="admin-action__title">End game</span>
            <span class="admin-action__desc">Show the clock history, then close the room for everyone</span>
          </span>
          <span class="admin-action__chevron" aria-hidden="true">›</span>
        </button>
      </section>
    </b-modal>

    <!-- Government Selection Modal -->
    <b-modal
      ref="govSelectModal"
      id="govSelectModal"
      title="🏛️ Select Government Type"
      centered
    >
      <div class="gov-selection">
        <p class="gov-selection-description">Choose a government system to apply to the room:</p>
        
        <div class="gov-dropdown-wrapper">
          <select v-model="selectedGovType" id="govTypeSelect" class="gov-select">
            <option :value="null" disabled>-- Select Government --</option>
            <option v-for="gov in displayGovernments" :key="gov.id" :value="gov.name">
              {{ gov.name }}
            </option>
          </select>
          <span class="gov-dropdown-arrow">▼</span>
        </div>
        
        <div class="gov-selection-actions">
          <b-button 
            variant="secondary" 
            @click="hideGovernmentSelection"
            class="gov-btn"
          >
            Cancel
          </b-button>
          <b-button 
            variant="primary"
            :disabled="!selectedGovType || isProcessingGov"
            @click="processGovernmentChange"
            class="gov-btn gov-btn-primary"
          >
            {{ isProcessingGov ? 'Processing…' : 'Continue →' }}
          </b-button>
        </div>
      </div>
      <template #footer></template>
    </b-modal>

    <!-- RoomGovernmentModal (for role assignment) -->
    <RoomGovernmentModal
      ref="roomGovModal"
      :participants="participants"
      @submit="submitGovernment"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import RoomGovernmentModal from './RoomGovernmentModal.vue'

const modal = ref(null)
const govSelectModal = ref(null)
const roomGovModal = ref(null)
const selectedGovType = ref(null)
const isProcessingGov = ref(false)

const props = defineProps({
  socket: {
    type: Object,
    required: true
  },
  participants: {
    type: Array,
    required: true
  },
  displayGovernments: {
    type: Array,
    required: true
  },
  biddingTally: {
    type: Object,
    default: () => ({})
  },
  biddingActive: {
    type: Boolean,
    default: false
  },
  dictatorBiddingModal: {
    type: Object,
    default: null
  }
})

const emit = defineEmits([
  'spin-wheel',
  'cast-vote',
  'end-game',
  'update-government'
])

// Public methods
const show = () => modal.value?.show()
const hide = () => {
  modal.value?.hide()
  selectedGovType.value = null
}

const openGovernmentSelection = () => {
  selectedGovType.value = null
  govSelectModal.value?.show()
}

const hideGovernmentSelection = () => {
  govSelectModal.value?.hide()
  selectedGovType.value = null
}

const processGovernmentChange = async () => {
  if (!selectedGovType.value) return
  
  isProcessingGov.value = true
  const govType = selectedGovType.value

  try {
    // Handle simple governments immediately
    if (govType === 'Democracy' || govType === 'Anarchy') {
      props.socket.emit('updateGovernment', JSON.stringify({ type: govType }))
      hideGovernmentSelection()
      hide()
      return
    }

    // Handle Dictatorship - start bidding
    if (govType === 'Dictatorship') {
      const biddingTally = {}
      props.participants.forEach(p => {
        biddingTally[p.user_id] = false
      })
      
      props.socket.emit('startDictatorBidding', JSON.stringify({ 
        initiatedBy: props.socket.id 
      }))
      
      hideGovernmentSelection()
      hide()
      
      // Open bidding modal
      setTimeout(() => {
        props.dictatorBiddingModal?.show?.()
      }, 100)
      return
    }

    // Handle Communism - open politburo wheel
    if (govType === 'Communism') {
      hideGovernmentSelection()
      hide()
      emit('spin-wheel', { forCommunism: true })
      return
    }

    // Handle Republic - start popular vote for head of state
    if (govType === 'Republic') {
      props.socket.emit('startRepublicVoting')
      hideGovernmentSelection()
      hide()
      return
    }
  } finally {
    isProcessingGov.value = false
  }
}

const submitGovernment = (payload) => {
  props.socket.emit('updateGovernment', JSON.stringify(payload))
  roomGovModal.value?.hide()
  hide()
}

const handleSpinWheel = () => {
  hide()
  emit('spin-wheel')
}

const handleCastVote = () => {
  hide()
  emit('cast-vote')
}

const handleEndGame = () => {
  hide()
  emit('end-game')
}

const actions = [
  { icon: '🏛️', title: 'Change government', desc: 'Switch the room to a new government system', run: openGovernmentSelection },
  { icon: '🎡', title: 'Spin wheel', desc: 'Spin the wheel for the whole room', run: handleSpinWheel },
  { icon: '🗳️', title: 'Cast vote', desc: 'Start a secret vote for all players', run: handleCastVote }
]

defineExpose({
  show,
  hide
})
</script>

<style scoped>
/* ---------- Admin panel: a calm, settings-style list ---------- */
.admin-section + .admin-section {
  margin-top: 20px;
}

.admin-section__label {
  margin: 0 0 8px 2px;
  color: #64748b;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

/* Rows share borders, so the group reads as one list */
.admin-list {
  display: flex;
  flex-direction: column;
  border: 1px solid #1f2937;
  border-radius: 10px;
  overflow: hidden;
}

.admin-action {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  padding: 14px 16px;
  background: #111827;
  border: none;
  color: #e5e7eb;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.admin-list .admin-action + .admin-action {
  border-top: 1px solid #1f2937;
}

.admin-action:hover {
  background: #1a2332;
}

.admin-action:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: -2px;
}

.admin-action__icon {
  flex: 0 0 auto;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1f2937;
  border-radius: 8px;
  font-size: 1.05rem;
  line-height: 1;
}

.admin-action__text {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.admin-action__title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #f1f5f9;
}

.admin-action__desc {
  font-size: 0.82rem;
  color: #94a3b8;
}

.admin-action__chevron {
  flex: 0 0 auto;
  color: #475569;
  font-size: 1.4rem;
  line-height: 1;
  transition: transform 0.15s ease, color 0.15s ease;
}

.admin-action:hover .admin-action__chevron {
  color: #94a3b8;
  transform: translateX(2px);
}

/* Danger zone: same shape, quietly red rather than shouting */
.admin-section--danger .admin-section__label {
  color: #f87171;
}

.admin-action--danger {
  border: 1px solid rgba(248, 113, 113, 0.35);
  border-radius: 10px;
}

.admin-action--danger .admin-action__icon {
  background: rgba(248, 113, 113, 0.12);
}

.admin-action--danger .admin-action__title {
  color: #fca5a5;
}

.admin-action--danger:hover {
  background: rgba(248, 113, 113, 0.08);
}

.gov-selection {
  padding: 0.5rem 0;
}

.gov-selection-description {
  color: #94a3b8;
  font-size: 0.95rem;
  margin-bottom: 1.25rem;
}

.gov-dropdown-wrapper {
  position: relative;
  margin-bottom: 1.5rem;
}

.gov-select {
  width: 100%;
  color: #f1f5f9;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border: 2px solid #475569;
  border-radius: 10px;
  padding: 14px 45px 14px 16px;
  font-size: 1.05rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
}

.gov-select:focus {
  border-color: #3b82f6;
  outline: none;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25);
}

.gov-select:hover {
  border-color: #60a5fa;
}

.gov-select option {
  color: #f1f5f9;
  background-color: #1e293b;
  padding: 12px;
}

.gov-dropdown-arrow {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: #60a5fa;
  font-size: 0.85rem;
  pointer-events: none;
}

.gov-selection-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.gov-btn {
  padding: 12px 24px;
  font-weight: 600;
  border-radius: 8px;
  font-size: 0.95rem;
  transition: all 0.2s ease;
}

.gov-btn:hover {
  transform: translateY(-1px);
}

.gov-btn-primary {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
  border-color: #60a5fa !important;
}

.gov-btn-primary:hover {
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%) !important;
}

.gov-btn-primary:disabled {
  background: #475569 !important;
  border-color: #64748b !important;
  opacity: 0.6;
}
</style>

<style>
/* Hide default modal footer for AdminControlsModal modals */
#adminControlsModal .modal-footer,
#govSelectModal .modal-footer {
  display: none !important;
}

/* Style modal headers */
#adminControlsModal .modal-header,
#govSelectModal .modal-header {
  background: #0f172a;
  border-bottom: 1px solid #1f2937;
  padding: 16px 20px;
}

#adminControlsModal .modal-title,
#govSelectModal .modal-title {
  color: #f1f5f9;
  font-weight: 600;
  font-size: 1.1rem;
}

/* The default close icon is dark; invert it for the dark header */
#adminControlsModal .btn-close,
#govSelectModal .btn-close {
  filter: invert(1) grayscale(1) brightness(1.6);
}

#adminControlsModal .modal-content,
#govSelectModal .modal-content {
  background: #0f172a;
  border: 1px solid #1f2937;
  border-radius: 12px;
  overflow: hidden;
}

#adminControlsModal .modal-body,
#govSelectModal .modal-body {
  background: #0f172a;
  padding: 20px;
}
</style>
