<template>
  <div id="app">
    <nav class="main-navbar">
      <div class="navbar-container">
        <!-- Left Section: Brand + Info Links -->
        <div class="navbar-left">
          <router-link to="/home" class="navbar-brand">
            <span class="brand-icon">🎲</span>
            <span class="brand-text">Gerry's Game</span>
          </router-link>
          
          <div class="nav-group nav-group-info">
            <router-link to="/home" class="nav-link-item">
              <span class="nav-icon">🏆</span>
              <span class="nav-text">Leaderboard</span>
            </router-link>
            <router-link to="/help" class="nav-link-item">
              <span class="nav-icon">❓</span>
              <span class="nav-text">Help</span>
            </router-link>
          </div>
        </div>
        
        <!-- Center Section: Games -->
        <div class="navbar-center">
          <div class="nav-group nav-group-games">
            <router-link to="/rooms" class="nav-link-item">
              <span class="nav-icon">🎮</span>
              <span class="nav-text">Active Games</span>
            </router-link>
            <router-link v-if="roomId" to="/room" class="nav-link-item nav-link-active-room">
              <span class="nav-icon">🚪</span>
              <span class="nav-text">Current Room</span>
            </router-link>
          </div>
        </div>
        
        <!-- User Section -->
        <div class="navbar-user">
          <router-link v-if="!username" to="/login" class="login-btn">
            Sign In
          </router-link>
          <div v-else class="user-dropdown" @click="toggleDropdown" ref="dropdownRef">
            <div class="user-avatar">
              {{ username.charAt(0).toUpperCase() }}
            </div>
            <span class="user-name">{{ username }}</span>
            <span class="dropdown-arrow">▾</span>
            
            <!-- Dropdown Menu -->
            <div v-if="dropdownOpen" class="dropdown-menu-custom">
              <div class="dropdown-item-custom" @click="goToProfile">
                <span class="dropdown-icon">👤</span>
                View Profile
              </div>
              <div class="dropdown-divider"></div>
              <div class="dropdown-item-custom dropdown-logout" @click="onLogout">
                <span class="dropdown-icon">🚪</span>
                Logout
              </div>
            </div>
          </div>
        </div>
      </div>
    </nav>
    <router-view />
  </div>
</template>

<script>
export default {
  name: "App",
  data() {
    return {
      dropdownOpen: false
    }
  },
  mounted() {
    document.title = "Gerrys Game";
    document.addEventListener('click', this.closeDropdownOnClickOutside);
  },
  beforeUnmount() {
    document.removeEventListener('click', this.closeDropdownOnClickOutside);
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
    toggleDropdown(e) {
      e.stopPropagation();
      this.dropdownOpen = !this.dropdownOpen;
    },
    closeDropdownOnClickOutside(e) {
      if (this.$refs.dropdownRef && !this.$refs.dropdownRef.contains(e.target)) {
        this.dropdownOpen = false;
      }
    },
    goToProfile() {
      this.dropdownOpen = false;
      this.$router.push({ name: 'Profile' });
    },
    async onLogout() {
      this.dropdownOpen = false;
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
  background: #0B0F19;
}

* {
  margin: 0;
  padding: 0;
}

#app {
  background: #0B0F19;
  min-height: 100vh;
  margin: 0;
  padding: 0;
}

/* ===== NAVBAR STYLES ===== */
.main-navbar {
  background: linear-gradient(135deg, #1A1F2E 0%, #0B0F19 100%);
  border-bottom: 1px solid #22D3EE33;
  padding: 0;
  position: sticky;
  top: 0;
  z-index: 1000;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.navbar-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  position: relative;
}

/* Brand */
.navbar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none !important;
  transition: transform 0.2s ease;
}

.navbar-brand:hover {
  transform: scale(1.02);
}

.brand-icon {
  font-size: 1.8rem;
  filter: drop-shadow(0 0 8px rgba(234, 179, 8, 0.4));
}

.brand-text {
  font-size: 1.4rem;
  font-weight: 800;
  background: linear-gradient(135deg, #EAB308 0%, #FCD34D 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.5px;
}

/* Navbar Layout */
.navbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.navbar-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.nav-group {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 12px;
}

.nav-group-games {
  background: linear-gradient(135deg, #EAB30815 0%, #CA8A0415 100%);
  border: 1px solid #EAB30833;
}

.nav-group-info {
  background: transparent;
  border: none;
}

.nav-link-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 8px;
  text-decoration: none !important;
  color: #94A3B8 !important;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  background: transparent;
}

.nav-link-item:hover {
  background: #22D3EE15;
  color: #F1F5F9 !important;
}

.nav-link-item.router-link-active,
.nav-link-item.router-link-exact-active {
  background: #22D3EE22;
  color: #22D3EE !important;
}

.nav-link-active-room {
  color: #EAB308 !important;
  background: #EAB30818 !important;
}

.nav-link-active-room:hover {
  background: #EAB30828 !important;
  color: #FCD34D !important;
}

.nav-icon {
  font-size: 1.1rem;
}

.nav-text {
  white-space: nowrap;
}

/* User Section */
.navbar-user {
  display: flex;
  align-items: center;
}

.login-btn {
  padding: 10px 24px;
  background: linear-gradient(135deg, #EAB308 0%, #CA8A04 100%);
  border: none;
  border-radius: 10px;
  color: #0B0F19 !important;
  font-weight: 700;
  font-size: 0.95rem;
  text-decoration: none !important;
  transition: all 0.2s ease;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(234, 179, 8, 0.3);
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px 6px 6px;
  background: #0B0F19;
  border: 1px solid #334155;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.user-dropdown:hover {
  border-color: #22D3EE55;
  background: #1A1F2E;
}

.user-avatar {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #22D3EE 0%, #0891B2 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #0B0F19;
  font-weight: 800;
  font-size: 1rem;
}

.user-name {
  color: #F1F5F9;
  font-weight: 600;
  font-size: 0.95rem;
}

.dropdown-arrow {
  color: #64748B;
  font-size: 0.8rem;
  transition: transform 0.2s ease;
}

.user-dropdown:hover .dropdown-arrow {
  color: #94A3B8;
}

/* Dropdown Menu */
.dropdown-menu-custom {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  background: #1A1F2E;
  border: 1px solid #22D3EE44;
  border-radius: 12px;
  min-width: 180px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
  overflow: hidden;
  z-index: 1001;
  animation: dropdownSlide 0.15s ease;
}

@keyframes dropdownSlide {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dropdown-item-custom {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  color: #F1F5F9;
  font-weight: 500;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.dropdown-item-custom:hover {
  background: #22D3EE15;
  padding-left: 20px;
}

.dropdown-icon {
  font-size: 1rem;
}

.dropdown-divider {
  height: 1px;
  background: #334155;
  margin: 4px 0;
}

.dropdown-logout:hover {
  background: #EF444422;
  color: #EF4444;
}

/* Hide old navbar styles */
.navbar {
  display: none !important;
}

/* Form control styling */
.form-control,
.form-select,
select {
  background-color: #1A1F2E !important;
  border: 2px solid #334155 !important;
  color: #F1F5F9 !important;
  transition: all 0.3s ease;
}

.form-control::placeholder {
  color: rgba(241, 245, 249, 0.5);
}

.form-control:focus,
.form-select:focus,
select:focus {
  background-color: #1A1F2E !important;
  border-color: #22D3EE !important;
  color: #F1F5F9 !important;
  box-shadow: 0 0 8px rgba(34, 211, 238, 0.4);
}

/* Form labels */
.form-label,
label {
  color: #F1F5F9;
  font-weight: 500;
}

/* Option styling */
option {
  background-color: #1A1F2E;
  color: #F1F5F9;
}

option:checked {
  background: linear-gradient(#0B0F19, #0B0F19), linear-gradient(to right, transparent 10%, #F1F5F9 90%);
  color: #F1F5F9;
}

/* Global overrides for Bootstrap success/warning colors */
.btn-success, .btn-success:hover, .btn-success:focus, .btn-success:active,
.badge-success,
.alert-success,
.text-success,
.bg-success {
  background-color: #1A1F2E !important;
  border-color: #F1F5F9 !important;
  color: #ffffff !important;
}

/* Override Bootstrap Vue colors */
.table-success,
.table-success > td,
.table-success > th {
  background-color: rgba(241, 245, 249, 0.1) !important;
}

/* Force all success-themed elements to purple */
:root {
  --bs-success: #F1F5F9 !important;
  --bs-success-rgb: 145, 70, 255 !important;
  --bs-primary: #F1F5F9 !important;
  --bs-primary-rgb: 145, 70, 255 !important;
}

/* Target text colors that might be green */
.text-muted {
  color: #888888 !important;
}

/* Fix table header colors */
.table thead th,
.table thead td {
  color: #F1F5F9 !important;
  background-color: #1A1F2E !important;
}

/* Responsive */
@media (max-width: 768px) {
  .navbar-container {
    padding: 0 16px;
  }
  
  .nav-text {
    display: none;
  }
  
  .nav-link-item {
    padding: 10px 12px;
  }
  
  .brand-text {
    font-size: 1.2rem;
  }
  
  .user-name {
    display: none;
  }
  
  .user-dropdown {
    padding: 6px;
    border-radius: 10px;
  }
}
</style>













