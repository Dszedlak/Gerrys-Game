<template>
  <div id="app">
    <nav class="main-navbar">
      <div class="navbar-container">
        <!-- Left: the brand, then the main links as tabs -->
        <div class="navbar-left">
          <router-link to="/home" class="navbar-brand" title="Gerry's Game">
            <span class="brand-icon">🎲</span>
            <span class="brand-text">Gerry's Game</span>
          </router-link>

          <div class="nav-tabs-main" role="navigation" aria-label="Main">
            <router-link to="/rooms" class="nav-tab" title="Active games">
              <span class="nav-tab__icon">🎮</span><span class="nav-tab__text">Games</span>
            </router-link>
            <router-link v-if="roomId" to="/room" class="nav-tab nav-tab--room" title="Current room">
              <span class="nav-tab__live" aria-hidden="true" /><span class="nav-tab__text">Current room</span>
            </router-link>
            <router-link to="/home" class="nav-tab" title="Leaderboard">
              <span class="nav-tab__icon">🏆</span><span class="nav-tab__text">Leaderboard</span>
            </router-link>
            <router-link to="/help" class="nav-tab" title="Help">
              <span class="nav-tab__icon">❓</span><span class="nav-tab__text">Help</span>
            </router-link>
          </div>
        </div>

        <!-- Right: the room's controls in one toolbar, then your account -->
        <div class="navbar-user">
          <div v-if="inRoom" class="room-toolbar" role="toolbar" aria-label="Room">
            <div class="room-toolbar__switch" role="group" aria-label="Room view">
              <button
                type="button"
                :class="{ 'is-active': roomView === 'board' }"
                :aria-pressed="roomView === 'board'"
                @click="setView('board')"
              >🎲<span class="navbar-label"> Board</span></button>
              <button
                type="button"
                :class="{ 'is-active': roomView === 'table' }"
                :aria-pressed="roomView === 'table'"
                @click="setView('table')"
              >📋<span class="navbar-label"> Table</span></button>
            </div>
            <span class="room-toolbar__sep" aria-hidden="true" />
            <button
              v-if="fullscreenSupported"
              type="button"
              class="room-toolbar__btn"
              :title="isFullscreen ? 'Leave full screen (Esc)' : 'Full screen: hide the browser tabs, bookmarks and address bar'"
              @click="toggleFullscreen"
            >
              <span class="room-toolbar__icon">{{ isFullscreen ? '🗗' : '⛶' }}</span><span class="navbar-label">{{ isFullscreen ? 'Exit full screen' : 'Full screen' }}</span>
            </button>
            <button
              v-if="isRoomAdmin"
              type="button"
              class="room-toolbar__btn"
              title="Admin controls"
              @click="openAdminControls"
            >
              <span class="room-toolbar__icon">⚙</span><span class="navbar-label">Admin</span>
            </button>
            <button
              type="button"
              class="room-toolbar__btn room-toolbar__btn--leave"
              title="Leave this room"
              @click="leaveRoom"
            >
              <span class="room-toolbar__icon">⎋</span><span class="navbar-label">Leave</span>
            </button>
          </div>

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
    <!-- A newer version went live while this tab was open -->
    <UpdateBanner />
    <!-- In-game confirmation dialogs -->
    <ConfirmHost />
  </div>
</template>

<script>
import { useRoomChrome } from '@/composables/useRoomChrome'
import { useFullscreen } from '@/composables/useFullscreen'
import UpdateBanner from '@/components/UpdateBanner.vue'
import ConfirmHost from '@/components/ConfirmHost.vue'

export default {
  name: "App",
  components: { UpdateBanner, ConfirmHost },
  setup() {
    // Room.vue registers its handlers here while it is mounted, so the
    // navbar can carry the room's own controls.
    const { inRoom, isRoomAdmin, roomView, setView, leaveRoom, openAdminControls } = useRoomChrome()
    const { isFullscreen, supported: fullscreenSupported, toggleFullscreen } = useFullscreen()
    return {
      inRoom, isRoomAdmin, roomView, setView, leaveRoom, openAdminControls,
      isFullscreen, fullscreenSupported, toggleFullscreen
    }
  },
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
  background: rgba(11, 15, 25, 0.96);
  border-bottom: 1px solid rgba(148, 163, 184, 0.14);
  padding: 0;
  position: sticky;
  top: 0;
  z-index: 1000;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(6px);
}

.navbar-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  height: 64px;
  max-width: 1880px;
  margin: 0 auto;
  padding: 0 20px;
}

/* Brand */
.navbar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-right: 18px;
  border-right: 1px solid rgba(148, 163, 184, 0.16);
  text-decoration: none !important;
}

.brand-icon {
  font-size: 1.6rem;
  filter: drop-shadow(0 0 8px rgba(234, 179, 8, 0.35));
}

.brand-text {
  font-size: 1.3rem;
  font-weight: 800;
  background: linear-gradient(135deg, #EAB308 0%, #FCD34D 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.3px;
  white-space: nowrap;
}

.navbar-left {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

/* Main links: plain tabs, a gold underline on the page you're on */
.nav-tabs-main {
  display: flex;
  align-items: stretch;
  gap: 2px;
  height: 64px;
}

.nav-tab {
  position: relative;
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 0 12px;
  color: #94A3B8 !important;
  font-weight: 600;
  font-size: 0.92rem;
  white-space: nowrap;
  text-decoration: none !important;
  transition: color 0.15s ease;
}

.nav-tab::after {
  content: '';
  position: absolute;
  left: 12px;
  right: 12px;
  bottom: 0;
  height: 2px;
  border-radius: 2px 2px 0 0;
  background: transparent;
  transition: background 0.15s ease;
}

.nav-tab:hover { color: #F1F5F9 !important; }
.nav-tab.router-link-exact-active { color: #FDE68A !important; }
.nav-tab.router-link-exact-active::after { background: #EAB308; }

.nav-tab__icon { font-size: 1rem; opacity: 0.85; }

/* "Current room": a live dot instead of an icon */
.nav-tab__live {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22C55E;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.2);
}

/* Right */
.navbar-user {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 0 0 auto;
}

/* The room's controls: one toolbar, buttons all the same height */
.room-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px;
  border-radius: 12px;
  background: #121726;
  border: 1px solid rgba(148, 163, 184, 0.16);
}

.room-toolbar__switch {
  display: flex;
  gap: 2px;
  padding: 2px;
  border-radius: 9px;
  background: #0B0F19;
}

.room-toolbar__switch button,
.room-toolbar__btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 12px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: #CBD5E1;
  font-weight: 600;
  font-size: 0.85rem;
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.room-toolbar__switch button { height: 28px; }
.room-toolbar__switch button:hover { color: #F1F5F9; }
.room-toolbar__switch button.is-active { background: #EAB308; color: #1c1917; font-weight: 700; }

.room-toolbar__btn:hover { background: rgba(148, 163, 184, 0.12); color: #F8FAFC; }
.room-toolbar__btn--leave:hover { background: rgba(239, 68, 68, 0.16); color: #FCA5A5; }

.room-toolbar__icon { font-size: 1rem; line-height: 1; }

.room-toolbar__sep {
  width: 1px;
  height: 22px;
  margin: 0 4px;
  background: rgba(148, 163, 184, 0.2);
}

/* Narrower screens: icons stand in for the labels */
@media (max-width: 1500px) {
  .room-toolbar__btn .navbar-label { display: none; }
  .room-toolbar__btn { padding: 0 9px; }
}

@media (max-width: 1300px) {
  .brand-text { display: none; }
  .nav-tab__text { display: none; }
  .nav-tab--room .nav-tab__text { display: inline; }
}

@media (max-width: 1000px) {
  .room-toolbar__switch .navbar-label { display: none; }
  .user-name { display: none; }
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

/* Beats the global a:visited/a:hover/a:focus yellow in overrides.css,
   which would otherwise put yellow text on this yellow button */
a.login-btn,
a.login-btn:hover,
a.login-btn:focus,
a.login-btn:visited {
  color: #000 !important;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(234, 179, 8, 0.3);
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 10px 4px 4px;
  background: #121726;
  border: 1px solid rgba(148, 163, 184, 0.16);
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
  width: 32px;
  height: 32px;
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













