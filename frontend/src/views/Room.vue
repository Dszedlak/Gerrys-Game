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
            <b-button class="market-btn" variant="primary" @click="sellTimeCounter">Sell a Time Counter (+2h)</b-button>
          </div>
        </b-col>
      </b-row>

      <!-- Centered dropdowns for Government and Job -->
      <b-row class="mt-3 mb-4">  <!-- add bottom margin under the dropdowns -->
        <b-col>
          <div class="center-row dropdowns">
            <!-- CHANGED: make this an inline-flex group like Job -->
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
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in participants" :key="p.user_id || p.userId || p.id">
                <td>
                  {{ p.username }}
                  <img
                    v-if="iconForParticipant(p)"
                    :src="iconForParticipant(p)"
                    class="gov-icon"
                    alt=""
                  />
                </td>
                <td>{{ p.job_name }}</td>
                <td>{{ p.bleed }}</td>
              </tr>
              <tr v-if="!participants.length">
                <td colspan="3" class="text-center">No participants yet</td>
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
    </b-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { useSocket } from '@/composables/useSocket'
import ClickToEdit from '@/components/helpers/ClickToEdit.vue'
import RoomListService from '@/services/RoomListService'
import WheelSpinner from '@/components/SpinWheel.vue'

const store = useStore()
const router = useRouter()
const { socket } = useSocket()

const clock = ref('')
const newComponent = ref(false)
const hover = ref(false)
const roomname = ref('test')
const participants = ref([])

// FIX: add missing refs
const roomGovernment = ref(null)
const selectedGovernmentId = ref(null)
const selectedJobId = ref(null)

// NEW: track room owner/creator
const roomOwnerId = ref(null)

// Defaults
const defaultGovernments = [
  { id: 1, name: 'Democracy' },
  { id: 2, name: 'Republic' },
  { id: 3, name: 'Dictatorship' },
  { id: 4, name: 'Communism' }
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
const isLeaving = ref(false)
const isRemoving = ref(false)

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
socket.on('updateClock', (data) => {
  clock.value = String(JSON.parse(data.data))
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
    bleed: p.bleed ?? 0
  })) : []
})

// Socket diagnostics: see what arrives
socket.onAny((event, ...args) => {
  if (event === 'updateCollectionData') {
    console.debug('[socket:onAny] updateCollectionData payload:', args[0])
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
    bleed: p.bleed ?? 0
  })) : []
  roomGovernment.value = room?.government || null

  // Sync dropdown to current government type if we have collections
  const syncId = findGovernmentIdByName(roomGovernment.value?.type)
  if (syncId !== undefined) selectedGovernmentId.value = syncId

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
  if (isRemoving.value) return
  const roomId = store.state.auth.roomId
  console.log('[RemoveRoom] OK clicked -> payload:', { roomId })
  isRemoving.value = true
  try {
    const resp = await RoomListService.removeRoom({ roomId })
    console.log('[RemoveRoom] Response:', resp?.status, resp?.data)
    store.commit('auth/leaveRoomId')
    removeRoomModal.value && removeRoomModal.value.hide()
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

// Market actions
function sellConsumable() {
  socket.emit('updateClock', JSON.stringify(30))
}
function sellTimeCounter() {
  socket.emit('updateClock', JSON.stringify(120))
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

  if (typeName === 'Democracy') {
    socket.emit('updateGovernment', JSON.stringify({ type: 'Democracy' }))
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
  // Backend handles target user; just send the delta
  try {
    socket.emit('updateBleed', JSON.stringify(Number(delta)))
  } catch (e) {
    console.error('[Bleed] emit failed', e)
  }
}
</script>

<style>
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
.job-controls {
  display: inline-flex;
  align-items: center;
  gap: 10px;          /* same spacing between label and select */
}

/* Space between the two groups */
.control-group { margin-right: 12px; }

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
  min-width: 110px;
  height: 38px;       /* align with select height */
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.bleed-header {
  text-align: center;
  vertical-align: middle;
}
.bleed-header-inner {
  display: inline-flex;          /* keeps width snug while centered in th */
  align-items: center;           /* vertical alignment */
  justify-content: center;       /* horizontal centering */
  gap: 8px;                      /* space around label */
}

.bleed-label {
  font-weight: 700;
  line-height: 28px;             /* match button height for perfect baseline */
}

.bleed-btn {
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

/* center the values in the Bleed column */
.table td:nth-child(3) { text-align: center; }

/* optional: small spacing tweak */
.bleed-btn-minus { margin-right: 2px; }
.bleed-btn-plus  { margin-left: 2px; }

.top-actions {
  display: flex;
  justify-content: center;
  align-items: center;
}

/* Space between the two buttons */
.top-actions-group { gap: 10px; } /* modern browsers */
.top-actions-group > .btn + .btn { margin-left: 10px; } /* fallback */
</style>