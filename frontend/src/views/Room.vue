<template>
  <div id="app">
      <b-container class="bv-example-row">
      <b-row class="itemRow">
        <b-col>
          <h1>Clock</h1>
          <Click-To-Edit id="clock" v-bind:value="clock" @change="uClock(clock)"></Click-To-Edit>
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
        <Click-To-Edit id="" v-bind:value="timeBank" @change="uTimeBank(timeBank)"></Click-To-Edit>
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
      newComponent: false
    }    
  },
  methods: {
    changeComponent: function () {
      this.newComponent = !this.newComponent
    },
    leaveRoom()
    {
      this.$socket.client.emit('leave')
      this.$router.push("/rooms")
    }, 
    uClock(time)
    {
      this.$socket.client.emit('updateClock', JSON.stringify(time))
    },
    uTimeBank(time)
    {
      this.$socket.client.emit('updateTimeBank', JSON.stringify(time))
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