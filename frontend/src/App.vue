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
  background: #0a0e27;
}

* {
  margin: 0;
  padding: 0;
}

#app {
  background: #0a0e27;
  min-height: 100vh;
  margin: 0;
  padding: 0;
}

.navbar {
  margin: 0 !important;
  padding: 0.5rem 0 !important;
  background: #0f1535 !important;
  box-shadow: 0 0 20px rgba(0, 255, 65, 0.3), inset 0 0 20px rgba(0, 255, 65, 0.05);
  border: 1px solid rgba(0, 255, 65, 0.2) !important;
  margin-bottom: 20px !important;
  width: 100%;
  position: relative;
  z-index: 100;
}

/* Make navbar brand text nice */
.navbar-brand {
  font-weight: 700;
  font-size: 1.4em;
  letter-spacing: 1px;
  color: #00ff41 !important;
}

.navbar-brand a {
  transition: all 0.3s ease;
  color: #00ff41 !important;
}

.navbar-brand a:hover {
  text-shadow: 0 0 8px rgba(0, 255, 65, 0.8), 0 0 16px rgba(0, 255, 65, 0.4);
}

/* Navigation link styling */
.nav-link {
  font-weight: 600;
  transition: all 0.3s ease !important;
  position: relative;
  color: #00ff41 !important;
}

.nav-link:hover {
  text-shadow: 0 0 8px rgba(0, 255, 65, 0.6);
  color: #00ff41 !important;
}

/* Dropdown styling */
.dropdown-menu {
  background-color: #0f1535 !important;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 255, 65, 0.2), inset 0 0 12px rgba(0, 255, 65, 0.05);
  border: 1px solid rgba(0, 255, 65, 0.2) !important;
}

/* Make dropdown menu text white */
.bg-dark .dropdown-item,
.bg-dark .dropdown-item:active,
.bg-dark .dropdown-item:focus,
.bg-dark .dropdown-item:hover {
  color: #00ff41 !important;
  background-color: #0f1535 !important;
  transition: all 0.2s ease;
}

.bg-dark .dropdown-item:hover {
  background-color: rgba(0, 255, 65, 0.1) !important;
  padding-left: 1.8rem;
  text-shadow: 0 0 8px rgba(0, 255, 65, 0.6);
}

.bg-dark .dropdown-menu {
  background-color: #0f1535 !important;
}

/* Form control styling */
.form-control,
.form-select,
select {
  background-color: #0a0e27 !important;
  border: 2px solid rgba(0, 255, 65, 0.3) !important;
  color: #00ff41 !important;
  transition: all 0.3s ease;
}

.form-control::placeholder {
  color: rgba(0, 255, 65, 0.5);
}

.form-control:focus,
.form-select:focus,
select:focus {
  background-color: #0a0e27 !important;
  border-color: #00ff41 !important;
  color: #00ff41 !important;
  box-shadow: 0 0 15px rgba(0, 255, 65, 0.3), inset 0 0 10px rgba(0, 255, 65, 0.05) !important;
}

/* Form labels */
.form-label,
label {
  color: #00ff41;
  font-weight: 500;
}

/* Option styling */
option {
  background-color: #0f1535;
  color: #00ff41;
}

option:checked {
  background: linear-gradient(#0a0e27, #0a0e27), linear-gradient(to right, transparent 10%, #00ff41 90%);
  color: #00ff41;
}
</style>