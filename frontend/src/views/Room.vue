<template>
  <div id="app">
		<h1>Quiz Room!</h1>
    <h2>Ready Users:</h2>
    <ul id="test">
      <li v-for="value in messages">
        {{ value }}
      </li>
    </ul>
  </div>
</template>
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
console.log(localStorage.getItem('token'))

Vue.use(VueSocketIOExt, socket, { store })
export default {
     sockets: {
    connect() {
      console.log(store.state.auth.token)
      console.log("socket connected");
      
    },
    UpdateUserStatus(data) {
      var users = JSON.parse(data.data)
      for(let i = 0; i < users.length; i++){
        this.messages.push(users[i]);
      }
    }
  },
  data() {
    return {
      messages: []
    };
  },
};
</script>