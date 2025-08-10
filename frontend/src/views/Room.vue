<template>
  <div id="app">
    <b-container class="bv-example-row">
      <b-row class="itemRow">
        <b-col>
          <!-- Open modal via click (no nested <a>) -->
          <b-button class="butt" @click="openLeaveModal">Leave Room?</b-button>
        </b-col>
        <b-col>
          <div v-if="currentUserId == currentRoomId || currentUserId == 1">
            <b-button class="butt" @click="openRemoveModal">End Game?</b-button>
          </div>
        </b-col>
      </b-row>
      <b-row class="itemRow">
        <b-col>
          <h1>Clock</h1>
          <Click-To-Edit id="clock" v-bind:value="clock" action="updateClock"></Click-To-Edit>
        </b-col>
      </b-row>
      <b-row>
        <b-col></b-col>
        <b-col cols="14" class="itemRowButtonsClock">
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
        </b-col>
        <b-col></b-col>
      </b-row>
      <b-row class="itemRowPlayers">
        <b-col></b-col>
        <b-col cols="1.4">
          <table class="table table-sm table-bordered" style="width:100%">
            <thead>
              <tr>
                <th>Username</th>
                <th>Job Title</th>
                <th>Government Position</th>
                <th>Bleed</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in participants" :key="p.user_id">
                <td>{{ p.username || 'Unknown' }}</td>
                <td>{{ p.job_name || '-' }}</td>
                <td>{{ p.job_tier || '-' }}</td>
                <td>{{ p.bleed }}</td>
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
    </b-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { useSocket } from '@/composables/useSocket'
import ClickToEdit from '@/components/helpers/ClickToEdit.vue'
import RoomListService from '@/services/RoomListService'

const store = useStore()
const router = useRouter()
const { socket } = useSocket()

const clock = ref('')
const newComponent = ref(false)
const hover = ref(false)
const roomname = ref('test')
const participants = ref([])

// Modal refs and busy flags
const leaveRoomModal = ref(null)
const removeRoomModal = ref(null)
const isLeaving = ref(false)
const isRemoving = ref(false)

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
  const room = JSON.parse(data.data)
  participants.value = room.participants || []
})

onMounted(() => {
  window.addEventListener('beforeunload', leaveRoom)
  if (!store.state.auth.roomId) {
    router.push({ name: 'Rooms' })
    return
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', leaveRoom)
  socket.disconnect()
})

// Open modals
function openLeaveModal() {
  leaveRoomModal.value && leaveRoomModal.value.show()
}
function openRemoveModal() {
  removeRoomModal.value && removeRoomModal.value.show()
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
}

.itemRowPlayers {
  padding-left:40px;
}

.intselect {
  text-align: center;
}
ul {
  list-style-type: none;
  text-align: center;
}
</style>