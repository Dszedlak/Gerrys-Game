<template>
  <div id="app">
		<h1>Gerrys Game!</h1>
    <h2>Players:</h2>
    <ul id="test">
      <li v-for="value in players">
        {{ value }}
      </li>
    </ul>
    <div class="mt-2">Clock: {{ text }}</div>

    <b-form-input v-model="text" placeholder="Edit clock"></b-form-input>

  </div>
  
</template>
<input v-model="message" placeholder="edit me" />


<script src="https://cdn.jsdelivr.net/npm/vue/dist/vue.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/socket.io-client/dist/socket.io.slim.js"></script>
<script src="https://cdn.jsdelivr.net/npm/vue-socket.io-extended"></script>
<script>
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
    sockets: {
    connect() {
      console.log(`${JwtService.getToken()}`)
      console.log("socket connected");  
    },
    UpdateUserStatus(data) {
      var users = JSON.parse(data.data)
      for(let i = 0; i < users.length; i++){
        this.players.push(users[i]);
      }
    },
  },
  data() {
    return {
      players: []
    }    
  },

}
</script>