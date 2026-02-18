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
html, body {
  margin: 0 !important;
  padding: 0 !important;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

* {
  margin: 0;
  padding: 0;
}

#app {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
  margin: 0;
  padding: 0;
}

.navbar {
  margin: 0 !important;
  padding: 0.5rem 0 !important;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  border: none !important;
  margin-bottom: 50px !important;
  width: 100%;
  position: relative;
  z-index: 100;
}

/* Make navbar brand text nice */
.navbar-brand {
  font-weight: 700;
  font-size: 1.4em;
  letter-spacing: 1px;
}

.navbar-brand a {
  transition: all 0.3s ease;
}

.navbar-brand a:hover {
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.5);
}

/* Navigation link styling */
.nav-link {
  font-weight: 600;
  transition: all 0.3s ease !important;
  position: relative;
}

.nav-link:hover {
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.3);
}

/* Dropdown styling */
.dropdown-menu {
  background-color: #343a40 !important;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  border: none;
}

/* Make dropdown menu text white */
.bg-dark .dropdown-item,
.bg-dark .dropdown-item:active,
.bg-dark .dropdown-item:focus,
.bg-dark .dropdown-item:hover {
  color: #fff !important;
  background-color: #343a40 !important;
  transition: all 0.2s ease;
}

.bg-dark .dropdown-item:hover {
  background-color: #495057 !important;
  padding-left: 1.8rem;
}

.bg-dark .dropdown-menu {
  background-color: #343a40 !important;
}
</style>