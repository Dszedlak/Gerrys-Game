<template>
  <div id="app">
    <BNavbar type="dark" variant="dark">
      <BNavbarBrand>
        <router-link to="/home" class="nav-link text-light">Gerrys Game</router-link>
      </BNavbarBrand>
      <BCollapse id="nav-collapse" is-nav>
        <BNavbarNav>
          <BNavItem>
            <router-link to="/rooms" class="nav-link text-light">Active games</router-link>
          </BNavItem>
        </BNavbarNav>
        <BNavbarNav class="ms-auto">
          <BNavItem v-if="!username">
            <router-link to="/login" class="nav-link text-light">Login</router-link>
          </BNavItem>
          <BNavItem v-else>
            <span class="nav-link text-light">Hello, {{ username }}</span>
          </BNavItem>
        </BNavbarNav>
      </BCollapse>
    </BNavbar>
    <router-view />
  </div>
</template>

<script>
export default {
  name: "App",
  mounted() {
    document.title = "Gerrys Game";
  },
  computed: {
    username() {
      return this.$store.state.auth.username;
    },
    roomId() {
      return this.$store.state.auth.roomId;
    },
  },
  methods: {
    async onLogout() {
      await this.$store.dispatch("logout").then(() => {
        this.$router.push("/login");
      });
    },
  },
};
</script>

<style>
.navbar {
  margin-bottom: 50px;
}
</style>