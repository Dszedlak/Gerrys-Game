<template>
  <div id="app">
    <head>
      <title>Gerrys Game</title>
    </head>
    <b-navbar type="dark" variant="dark">
      <b-navbar-brand to="/home" href="#">Gerrys Game</b-navbar-brand>
        <b-collapse id="nav-collapse" is-nav>
        <b-navbar-nav>
          <b-nav-item to="/rooms">Active games</b-nav-item>
          <template v-if="username != null && roomId != null"> 
            <b-nav-item to="/room">Current Game</b-nav-item>
          </template>
        
          <!--<b-nav-item to="/me/quizzes">My quizzes</b-nav-item> -->
        </b-navbar-nav>
        <b-navbar-nav class="ml-auto">
          <template v-if="username != null">
            <b-nav-item-dropdown right>
              <template v-slot:button-content>
                <em>{{ username }}</em>
              </template>
              <b-dropdown-item to="/me">Profile</b-dropdown-item>
              <b-dropdown-item v-on:click="onLogout()">Sign Out</b-dropdown-item>
            </b-nav-item-dropdown>
          </template>
          <template v-else>
            <b-nav-item to="/login">Login/Register</b-nav-item>
          </template>
        </b-navbar-nav>
      </b-collapse>
    </b-navbar>
    <b-container fluid>
      <router-view/>
    </b-container>
  </div>
</template>
<script>

export default {
  name: "App",
  mounted() {
     document.title = "Gerrys Game";
  },
  data() {
		return {
			name: 'RoomList',
		}
	},
    methods: {
      async onLogout () {
        await this.$store.dispatch('logout').then(() => {
          this.$router.push('/login')
      })
    }  
    },
    computed: {
      username () {
        return this.$store.state.auth.username
      },
      roomId () {
        return this.$store.state.auth.roomId
      },
  }
}
</script>
<style>
  .navbar {
    margin-bottom: 50px;
  }
</style>