<template>
  <div id="app">
      <b-container class="bv-example-row">
        <b-row class="itemRow">
        <b-col>
          <b-button class="butt"><a v-b-modal.LeaveRoomModal>{{ "Leave Room?" }}</a></b-button>
        </b-col>  
        <b-col>
          <!-- Conditionally render the div and dropdown based on the user's ID -->
          <div>
            <div>Interest Rate:</div>
            <select class="intselect" @change="handleInterestRateChange">
              <option disabled value="">Change interest rate?</option>
              <option value=1.16667>10 mins per hour</option>
              <option value=1.33333>20 mins per hour</option>
              <option value=1.5>30 mins per hour</option>
            </select>
            <p @mouseover="handleHover(true)" @mouseleave="handleHover(false)">
              {{ message }}
            </p>
          </div>
        </b-col>
        <b-col>
          <div v-if="currentUserId == currentRoomId || currentUserId == 1"> 
          <b-button class="butt" ><a v-b-modal.removeRoomModal>{{ "End Game?" }}</a></b-button>
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
    <b-row class="itemRow">
      <b-col>
        <h1>Time Bank</h1>
        <Click-To-Edit id="" v-bind:value="timeBank" action="updateTimeBank"></Click-To-Edit>
      </b-col>
    </b-row>
    <b-row>
      <b-col></b-col>
      <b-col cols="14" class="itemRowButtons">
            <b-button-group class="mx-1">
              <b-button class="addremovebutton" @click="uTimeBank(-60)">-1h</b-button>
            </b-button-group>
            
            <b-button-group class="mx-1">
              <b-button class="addremovebutton" @click="uTimeBank(60)">+1h</b-button>
            </b-button-group>

            <b-button-group class="mx-1">
              <b-button class="emptyButton" @click="uTimeBank('clear')">Clear</b-button>
            </b-button-group>

            <b-button-group class="mx-1">
              <b-button class="cashoutButton" @click="uTimeBank('cashout')">Cashout</b-button>
            </b-button-group>

            <b-button-group class="mx-1">
              <b-button class="interestButton" @click="uTimeBank('addInterest')">+ Interest</b-button>
            </b-button-group>
      </b-col>
      <b-col></b-col>
    </b-row>
      <b-row class="itemRowPlayers">
        <b-col></b-col>
        <b-col cols="1.4">    
          <h1 class="players">Players</h1>
            <ul id="test">
              <li v-for="value in players" v-bind:key="value">
                <h5 class="list">{{ value }}</h5>
              </li>
            </ul>
        </b-col>
        <b-col></b-col>
        
      </b-row>
      <b-modal id="LeaveRoomModal" ref="modal" title="Leave Room:">Are you sure you want to Leave room: {{roomname}}
					<template #modal-footer="{ cancel }">
				<!-- Emulate built in modal footer ok and cancel button actions -->
			
					<b-button size="sm" variant="success" @click="leaveRoom()">
						Yes
					</b-button>
					<b-button size="sm" variant="danger" @click="cancel()">
						No
					</b-button>
					<!-- Button with custom close trigger value -->      
					</template>	
			</b-modal>
      <b-modal id="removeRoomModal" ref="modal" title="End Game:">Are you sure you want to end the game: {{roomname}}
					<template #modal-footer="{ cancel }">
				<!-- Emulate built in modal footer ok and cancel button actions -->
			
					<b-button size="sm" variant="success" @click="removeRoom()">
						Yes
					</b-button>
					<b-button size="sm" variant="danger" @click="cancel()">
						No
					</b-button>
					<!-- Button with custom close trigger value -->      
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
import JwtService from '@/services/JwtService'
import RoomListService from "@/services/RoomListService"

const store = useStore()
const router = useRouter()
const { socket, isConnected } = useSocket()

const players = ref([])
const clock = ref("")
const timeBank = ref("")
const interestRate = ref(0)
const roomId = ref(null)
const userId = ref("")
const newComponent = ref(false)
const hover = ref(false)
const roomname = ref("test")

// Socket event handlers
socket.on('UpdateUserStatus', (data) => {
  players.value = []
  const users = JSON.parse(data.data)
  for (let i = 0; i < users.length; i++) {
    players.value.push(users[i])
  }
})
socket.on('updateClock', (data) => {
  clock.value = String(JSON.parse(data.data))
})
socket.on('updateTimeBank', (data) => {
  timeBank.value = String(JSON.parse(data.data))
})
socket.on('updateInterestRate', (data) => {
  interestRate.value = String(JSON.parse(data.data))
})
socket.on('updateRoomId', (data) => {
  store.state.auth.roomId = data.data
})
socket.on('setUserId', (data) => {
  store.state.auth.userId = data.data
})

onMounted(() => {
  window.addEventListener("beforeunload", leaveRoom)
  if (localStorage.getItem('reloaded')) {
    localStorage.removeItem('reloaded')
  } else {
    localStorage.setItem('reloaded', '1')
    location.reload()
  }
})

onBeforeUnmount(() => {
  window.removeEventListener("beforeunload", leaveRoom)
  socket.disconnect()
})

// Methods
function changeComponent() {
  newComponent.value = !newComponent.value
}
function leaveRoom() {
  const data = { roomId: store.state.auth.roomId }
  socket.emit('leave')
  store.state.auth.roomId = null
  RoomListService.leaveRoom(data)
    .then(() => router.push({ name: 'RoomList' }))
    .catch(e => console.log(e))
}
function removeRoom() {
  const data = { roomId: store.state.auth.roomId }
  store.state.auth.roomId = null
  RoomListService.removeRoom(data)
    .then(() => router.push({ name: 'RoomList' }))
    .catch(e => console.log(e))
}
function uClock(time) {
  socket.emit('updateClock', JSON.stringify(time))
}
function uTimeBank(time) {
  socket.emit('updateTimeBank', JSON.stringify(time))
}
function handleInterestRateChange(event) {
  interestRate.value = event.target.value
  socket.emit('updateInterestRate', interestRate.value)
}
function handleHover(s) {
  hover.value = s
}

// Computed
const username = computed(() => store.state.auth.username)
const currentRoomId = computed(() => store.state.auth.roomId)
const currentUserId = computed(() => store.state.auth.userId)
const message = computed(() =>
  hover.value
    ? "1.2 = 20 mins per hour. 1.5 = 30 mins per hour. 2 = 1 hour per hour. "
    : "Help?"
)
</script>
<style>

.cashoutButton{
  width: 83px;
  height: 45px;
  text-align: left;
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

.interestButton{
  width: 95px;
  height: 45px;
  text-align: left;
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

.players {
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