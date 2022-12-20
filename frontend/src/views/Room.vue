<template>
  <div id="app">
      <b-container class="bv-example-row">
      <b-row class="itemRow">
        <b-col>
          <h1>Clock</h1>
          <Click-To-Edit id="clock" value="0•00•00•00"></Click-To-Edit>
        </b-col>  
    </b-row>
    <b-row>
      <b-col></b-col>
      <b-col cols="14" class="itemRowButtonsClock">
            <b-button-group class="mx-1">
              <b-button class="addremovebuttonClock">-1h</b-button>
              <b-button class="addremovebuttonClock">-30</b-button>
              <b-button class="addremovebuttonClock">-20</b-button>
              <b-button class="addremovebuttonClock">-10</b-button>
            </b-button-group>
            
            <b-button-group class="mx-1">
              <b-button class="addremovebuttonClock">+10</b-button>
              <b-button class="addremovebuttonClock">+20</b-button>
              <b-button class="addremovebuttonClock">+30</b-button>
              <b-button class="addremovebuttonClock">+1h</b-button>
            </b-button-group>
      </b-col>
      <b-col></b-col>
    </b-row>
    <b-row class="itemRow">
      <b-col>
        <h1>Time Bank</h1>
        <Click-To-Edit value="0•00•00•00"></Click-To-Edit>
      </b-col>
    </b-row>
    <b-row>
      <b-col></b-col>
      <b-col cols="14" class="itemRowButtons">
            <b-button-group class="mx-1">
              <b-button class="addremovebutton">-1h</b-button>
            </b-button-group>
            
            <b-button-group class="mx-1">
              <b-button class="addremovebutton">+1h</b-button>
            </b-button-group>

            <b-button-group class="mx-1">
              <b-button class="emptyButton">Clear</b-button>
            </b-button-group>

            <b-button-group class="mx-1">
              <b-button class="cashoutButton">Cashout</b-button>
            </b-button-group>

            <b-button-group class="mx-1">
              <b-button class="interestButton">+ Interest</b-button>
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
    updateUserInfo() 
    {
      var args = arguments;
      var playerData = [];

      for (var a in args)
      {
        playerData.push(a);
      }
      
      const player = JSON.stringify(Object.assign({}, playerData))
      this.$socket.client.emit('updatePlayerData', player)
    },
    updateRoomId(data)
    {
      this.$store.state.auth.roomId = data.data;
      console.log("roomId: " + this.$store.state.auth.roomId)

    }
  },
  created() {
    window.addEventListener("beforeunload", this.leaveRoom);
  }, 
  mounted() {
    if (localStorage.getItem('reloaded')) {
        // The page was just reloaded. Clear the value from local storage
        // so that it will reload the next time this page is visited.
        localStorage.removeItem('reloaded');
    } else {
        // Set a flag so that we know not to reload the page twice.
        localStorage.setItem('reloaded', '1');
        location.reload();
    }
  },  
  methods:{
    leaveRoom()
    {
      this.$socket.client.emit('leave')
      this.$router.push("/rooms")
    }
  },
  data() {
    return {
      players: [],
      roomId: null,
      newComponent: false
    }    
  },
 
  methods: {
    changeComponent: function () {
      this.newComponent = !this.newComponent
    }
  }

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