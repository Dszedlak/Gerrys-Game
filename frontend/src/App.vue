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
          <BNavItem v-if="roomId">
            <router-link to="/room" class="nav-link text-light">Room</router-link>
          </BNavItem>
        </BNavbarNav>
        <BNavbarNav class="ms-auto">
          <BNavItem v-if="!username">
            <router-link to="/login" class="nav-link text-light">Login</router-link>
          </BNavItem>
          <BNavItemDropdown
            v-else
            :text="username"
            right
            class="ml-2"
            menu-class="bg-dark"
            toggle-class="text-light"
          >
            <BDropdownItem @click="goToProfile">View Profile</BDropdownItem>
            <BDropdownItem @click="onLogout">Logout</BDropdownItem>
          </BNavItemDropdown>
        </BNavbarNav>
      </BCollapse>
    </BNavbar>
    <router-view />
  </div>
</template>

<script>
import { BNavItemDropdown, BDropdownItem } from 'bootstrap-vue-next'

export default {
  name: "App",
  components: {
    BNavItemDropdown,
    BDropdownItem
  },
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
    goToProfile() {
      this.$router.push({ name: 'Profile' }); // Change 'Profile' to your actual profile route name if needed
    },
    async onLogout() {
      await this.$store.dispatch("auth/logout");
      this.$router.push("/login");
    },
  },
};
</script>

<style>
.navbar {
  margin-bottom: 50px;
}

/* Make dropdown menu text white */
.bg-dark .dropdown-item,
.bg-dark .dropdown-item:active,
.bg-dark .dropdown-item:focus,
.bg-dark .dropdown-item:hover {
  color: #fff !important;
  background-color: #343a40 !important;
}
.bg-dark .dropdown-menu {
  background-color: #343a40 !important;
}
</style>