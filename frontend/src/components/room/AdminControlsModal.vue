<template>
  <div>
    <!-- Main Admin Controls Modal -->
    <b-modal
      ref="modal"
      id="adminControlsModal"
      title="⚙️ Admin Controls"
      size="lg"
      centered
    >
      <div class="admin-controls-container">
        <div class="admin-controls-group mb-4">
          <h5 class="mb-3">Game Management</h5>
          <b-button 
            variant="primary" 
            @click="openGovernmentSelection"
            class="w-100 mb-2"
          >
            🏛️ Change Government
          </b-button>
          <b-button 
            variant="info" 
            @click="handleSpinWheel"
            class="w-100 mb-2"
          >
            🎡 Spin Wheel
          </b-button>
          <b-button 
            variant="success" 
            @click="handleCastVote"
            class="w-100 mb-2"
          >
            🗳️ Cast Vote
          </b-button>
        </div>
        
        <div class="admin-controls-group">
          <h5 class="mb-3">End Game</h5>
          <b-button 
            variant="danger" 
            @click="handleEndGame"
            class="w-100"
          >
            🏁 End Game & View History
          </b-button>
        </div>
      </div>
      <template #footer></template>
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

    // Handle Republic - open role assignment modal
    roomGovModal.value?.show('Republic')
    hideGovernmentSelection()
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

defineExpose({
  show,
  hide
})
</script>

<style scoped>
.admin-controls-container {
  padding: 0;
}

.admin-controls-group {
  margin-bottom: 1.5rem;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 20px;
}

.admin-controls-group:last-child {
  margin-bottom: 0;
}

.admin-controls-group h5 {
  color: #f1f5f9;
  font-weight: 700;
  font-size: 1.1rem;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #3b82f6;
  text-transform: uppercase;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.admin-controls-group h5::before {
  content: "⚙";
  font-size: 1rem;
}

.admin-controls-group:last-child h5::before {
  content: "⛔";
}

.admin-controls-group .btn {
  padding: 14px 20px;
  font-weight: 600;
  font-size: 1rem;
  border-radius: 8px;
  transition: all 0.2s ease;
  border-width: 2px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.admin-controls-group .btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.admin-controls-group .btn-primary {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
  border-color: #60a5fa !important;
}

.admin-controls-group .btn-primary:hover {
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%) !important;
}

.admin-controls-group .btn-info {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%) !important;
  border-color: #22d3ee !important;
  color: #ffffff !important;
}

.admin-controls-group .btn-info:hover {
  background: linear-gradient(135deg, #22d3ee 0%, #06b6d4 100%) !important;
}

.admin-controls-group .btn-success {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important;
  border-color: #4ade80 !important;
}

.admin-controls-group .btn-success:hover {
  background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%) !important;
}

.admin-controls-group .btn-danger {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
  border-color: #f87171 !important;
}

.admin-controls-group .btn-danger:hover {
  background: linear-gradient(135deg, #f87171 0%, #ef4444 100%) !important;
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
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border-bottom: 2px solid #3b82f6;
  padding: 16px 20px;
}

#adminControlsModal .modal-title,
#govSelectModal .modal-title {
  color: #f1f5f9;
  font-weight: 700;
  font-size: 1.25rem;
  letter-spacing: 0.5px;
}

#adminControlsModal .modal-body,
#govSelectModal .modal-body {
  background: #0f172a;
  padding: 20px;
}
</style>
