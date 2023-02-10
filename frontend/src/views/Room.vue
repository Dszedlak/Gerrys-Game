<template>
  <div id="app">
      <b-container class="bv-example-row">
        <b-row class="itemRow">
        <b-col>
          <b-button class="butt"><a v-b-modal.LeaveRoomModal>{{ "Leave Room?" }}</a></b-button>
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
<script src="https://cdn.jsdelivr.net/npm/vue/dist/vue.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/socket.io-client/dist/socket.io.slim.js"></script>
<script src="https://cdn.jsdelivr.net/npm/vue-socket.io-extended"></script>
<script>
import ClickToEdit from '@/components/helpers/ClickToEdit.vue'
import VueSocketIOExt from 'vue-socket.io-extended';
import io from 'socket.io-client';
import Vue from 'vue';
import store from '../store/index';
import JwtService from '@/services/JwtService'
import RoomListService from "@/services/RoomListService";

var socket = io("ws://127.0.0.1:5000/",  {
      transportOptions: {
        polling: {
            extraHeaders: {
                Authorization: `Bearer ${JwtService.getToken()}`
            }
        }
    }
});

Vue.use(VueSocketIOExt, socket, { store })
export default {
    components: {
      ClickToEdit,
    },
    sockets: {
    connect() {
      console.log(`${JwtService.getToken()}`)
      console.log("socket connected");  
      this.$socket.client.emit('join');
    },
    UpdateUserStatus(data) {
      this.players = [];
      var users = JSON.parse(data.data)
      for(let i = 0; i < users.length; i++){
        this.players.push(users[i]);
      }
    },
    updateClock(data)
    {
      this.clock = String(JSON.parse(data.data))
    },
    updateTimeBank(data)
    {
      this.timeBank= String(JSON.parse(data.data))
    },
    updateRoomId(data)
    {
      this.$store.state.auth.roomId = data.data;
      console.log("roomId: " + this.$store.state.auth.roomId)
    },
    setUserId(data)
    {
      this.$store.state.auth.userId = data.data;
      console.log("userId: " + this.$store.state.auth.userId)

    }
  },
  created() {
    window.addEventListener("beforeunload", this.leaveRoom);
  }, 
  mounted() {
    if (localStorage.getItem('reloaded')) {
        localStorage.removeItem('reloaded');
    } else {
        localStorage.setItem('reloaded', '1');
        location.reload();
    }
  },  
  data() {
    return {
      players: [],
      clock: "",
      timeBank: "",
      roomId: null,
      userId: "",
      newComponent: false, 
    }    
  },
  methods: {
    changeComponent: function () {
      this.newComponent = !this.newComponent
    },
    leaveRoom()
    {
			var data = {
				roomId: this.$store.state.auth.roomId
			}
      this.$socket.client.emit('leave')
			this.$store.state.auth.roomId = 0;
            RoomListService.leaveRoom(data)
            .then(response => {
                this.$router.push({ name: 'RoomList'})
            })
            .catch(e => {
                console.log(e);
            });
    },
    removeRoom()
    {
      var data = {
				roomId: this.$store.state.auth.roomId
			}
      //this.$socket.client.emit('closeRoom')
      this.$store.state.auth.roomId = 0
      RoomListService.removeRoom(data)
            .then(response => {
                this.$router.push({ name: 'RoomList'})
            })
            .catch(e => {
                console.log(e);
            });
    },
    uClock(time)
    {
      this.$socket.client.emit('updateClock', JSON.stringify(time))
    },
    uTimeBank(time)
    {
      this.$socket.client.emit('updateTimeBank', JSON.stringify(time))
    },
  },
  computed: {
			username () {
			return this.$store.state.auth.username
			},
			currentRoomId () {
			return this.$store.state.auth.roomId
			},
      currentUserId () {
			return this.$store.state.auth.roomId
			},
		},
  } 

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

ul {
  list-style-type: none;
  text-align: center;
}
</style>