<template>
  <div class="room-list-page">
    <div class="room-list-container">
      <!-- Header -->
      <header class="rl-head">
        <div>
          <div class="rl-eyebrow">Gerry's Game</div>
          <h1 class="rl-title">
            Active games
            <span v-if="username && rooms.length" class="rl-count">{{ rooms.length }} open</span>
          </h1>
          <p class="rl-sub">Join a room with your friends, or start your own.</p>
        </div>
        <button v-if="username" type="button" class="rl-create" @click="showCreateRoomModal">
          <span class="rl-create__plus" aria-hidden="true">+</span>
          Create room
        </button>
      </header>

      <div v-if="!username" class="rl-empty">
        <div class="rl-empty__art" aria-hidden="true">🔒</div>
        <h2 class="rl-empty__title">Sign in to play</h2>
        <p class="rl-empty__text">Log in to see the games that are running and join one.</p>
        <router-link to="/login" class="rl-create rl-create--link">Sign in</router-link>
      </div>

      <div v-else-if="rooms.length === 0" class="rl-empty">
        <div class="rl-empty__art" aria-hidden="true">🎲</div>
        <h2 class="rl-empty__title">No games running yet</h2>
        <p class="rl-empty__text">Create a room, share its name with your friends, and start once everyone's in the lobby.</p>
        <button type="button" class="rl-create" @click="showCreateRoomModal">
          <span class="rl-create__plus" aria-hidden="true">+</span>
          Create the first room
        </button>
      </div>

      <!-- Room Cards Grid -->
      <div v-else class="rl-grid">
        <article v-for="(room, index) in rooms" :key="index" class="rl-card">
          <div class="rl-card__top">
            <h3 class="rl-card__name" :title="room.name">{{ room.name }}</h3>
            <span v-if="room.game_version" class="rl-card__version">v{{ room.game_version }}</span>
          </div>
          <div class="rl-card__host">
            <span class="rl-card__avatar">{{ (room.owner_name || '?').charAt(0).toUpperCase() }}</span>
            <span>Hosted by <strong>{{ room.owner_name || 'Unknown' }}</strong></span>
          </div>
          <div class="rl-card__stats">
            <span class="rl-chip">👥 {{ room.participant_count || 0 }} {{ (room.participant_count || 0) === 1 ? 'player' : 'players' }}</span>
            <span class="rl-chip">⏱️ Open {{ formatDuration(room.startedAt) }}</span>
            <span v-if="room.governmentType" class="rl-chip">🏛️ {{ room.governmentType }}</span>
          </div>
          <div class="rl-card__actions">
            <button type="button" class="rl-btn rl-btn--ghost" @click.prevent="showDetailsModal(room)">Details</button>
            <button type="button" class="rl-btn rl-btn--join" @click.prevent="quickJoin(room)">Join game →</button>
          </div>
        </article>
      </div>
    </div>

    <!-- Create Room Modal -->
    <BModal
      ref="createRoomModal"
      :hide-header="true"
      :hide-footer="true"
      :hide-header-close="true"
      centered
      content-class="custom-modal-content"
      body-class="custom-modal-body"
    >
      <div class="modal-custom-content">
        <div class="modal-custom-header">
          <h2>Create New Room</h2>
          <button class="modal-close-btn" @click="$refs.createRoomModal.hide()">×</button>
        </div>
        <form @submit.stop.prevent="createRoom" class="modal-form">
          <div class="form-group">
            <label for="room-name-input">Room Name</label>
            <input
              id="room-name-input"
              v-model="newRoom.name"
              type="text"
              placeholder="Enter room name..."
              class="form-input"
              required
            />
            <small v-if="localError" class="form-error">{{ localError }}</small>
          </div>
          <div v-if="gameVersions.length" class="form-group">
            <label for="game-version-select">Game version</label>
            <select id="game-version-select" v-model="newRoom.gameVersion" class="form-input">
              <option v-for="v in gameVersions" :key="v.key" :value="v.key">
                {{ v.name }}{{ v.is_default ? ' (latest)' : '' }}
              </option>
            </select>
            <small v-if="selectedVersion" class="form-hint">
              {{ selectedVersion.counts.scenario }} scenario cards ·
              {{ selectedVersion.counts.assignment }} assignment slips ·
              {{ selectedVersion.counts.collectable }} collectables
              <template v-if="selectedVersion.examples"> · contains example cards</template>
            </small>
            <small v-if="selectedVersion?.notes" class="form-hint form-hint--notes">{{ selectedVersion.notes }}</small>
          </div>
        </form>
        <div class="modal-actions">
          <button type="button" class="btn-cancel" @click="$refs.createRoomModal.hide()">Cancel</button>
          <button type="button" class="btn-create" :disabled="creatingRoom" @click="createRoom">
            {{ creatingRoom ? 'Creating...' : 'Create Room' }}
          </button>
        </div>
      </div>
    </BModal>

    <!-- Room Details Modal -->
    <BModal
      ref="detailsModal"
      :hide-header="true"
      :hide-footer="true"
      :hide-header-close="true"
      centered
      size="lg"
      content-class="custom-modal-content"
      body-class="custom-modal-body"
    >
      <div class="modal-custom-content" v-if="selectedRoom">
        <div class="modal-custom-header">
          <h2>{{ selectedRoom.name }}</h2>
          <button class="modal-close-btn" @click="$refs.detailsModal.hide()">×</button>
        </div>
        <div class="details-content">
          <div class="details-info">
            <div class="info-row">
              <span class="info-label">Created by:</span>
              <span class="info-value">{{ selectedRoom.owner_name || 'Unknown' }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Open for:</span>
              <span class="info-value">{{ formatDuration(selectedRoom.startedAt) }}</span>
            </div>
            <div v-if="selectedRoom.game_version" class="info-row">
              <span class="info-label">Game version:</span>
              <span class="info-value">{{ versionName(selectedRoom.game_version) }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Government:</span>
              <span class="info-value">{{ selectedRoom.governmentType || 'Democracy' }}</span>
            </div>
          </div>
          <div class="details-members">
            <h4>Players ({{ selectedRoom.participants?.length || 0 }})</h4>
            <div class="members-list">
              <div 
                v-for="participant in selectedRoom.participants" 
                :key="participant.user_id" 
                class="member-item"
              >
                <span class="member-icon">🎮</span>
                <span class="member-name">{{ participant.username }}</span>
                <span v-if="participant.user_id === selectedRoom.owner_id" class="member-badge">Host</span>
              </div>
              <div v-if="!selectedRoom.participants?.length" class="no-members">
                No players yet
              </div>
            </div>
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn-cancel" @click="$refs.detailsModal.hide()">Close</button>
          <button type="button" class="btn-join-large" @click="joinSelectedRoom" :disabled="joiningRoom">
            {{ joiningRoom ? 'Joining...' : 'Join Game' }}
          </button>
        </div>
      </div>
    </BModal>
  </div>
</template>

<script>
import { BButton, BModal } from 'bootstrap-vue-next'
import RoomListService from "@/services/RoomListService";

export default {
  name: 'RoomList',
  components: {
    BButton, BModal
  },
  data() {
    return {
      rooms: [],
      selectedRoom: null,
      newRoom: {
        name: "",
        gameVersion: null,
      },
      gameVersions: [],
      localError: '',
      creatingRoom: false,
      joiningRoom: false
    }
  },
  computed: {
    selectedVersion() {
      return this.gameVersions.find(v => v.key === this.newRoom.gameVersion) || null
    }
  },
  methods: {
    showCreateRoomModal() {
      this.localError = '';
      this.newRoom.name = '';
      this.loadGameVersions();
      this.$refs.createRoomModal.show();
    },
    async loadGameVersions() {
      try {
        const { data } = await RoomListService.getGameVersions()
        this.gameVersions = data?.versions || []
        if (!this.gameVersions.some(v => v.key === this.newRoom.gameVersion)) {
          this.newRoom.gameVersion = data?.default || this.gameVersions[0]?.key || null
        }
      } catch (e) {
        // Older server without versions: create the room without one
        this.gameVersions = []
      }
    },
    versionName(key) {
      return this.gameVersions.find(v => v.key === key)?.name || key
    },
    showDetailsModal(room) {
      this.selectedRoom = room;
      this.localError = '';
      this.$refs.detailsModal.show();
    },
    async quickJoin(room) {
      try {
        this.joiningRoom = true
        const payload = { roomId: Number(room.id) }
        this.$store.commit('auth/setRoomId', { id: payload.roomId })
        const resp = await RoomListService.joinRoom(payload)
        if (resp && resp.status >= 200 && resp.status < 300) {
          this.$router.push({ name: 'Room' })
        } else {
          this.localError = 'Failed to join room.'
        }
      } catch (e) {
        this.localError = e?.response?.data?.errors || e?.response?.data?.message || 'Failed to join room.'
      } finally {
        this.joiningRoom = false
      }
    },
    async joinSelectedRoom() {
      if (!this.selectedRoom) return
      try {
        this.joiningRoom = true
        const payload = { roomId: Number(this.selectedRoom.id) }
        this.$store.commit('auth/setRoomId', { id: payload.roomId })
        const resp = await RoomListService.joinRoom(payload)
        if (resp && resp.status >= 200 && resp.status < 300) {
          this.$refs.detailsModal.hide()
          this.$router.push({ name: 'Room' })
        } else {
          this.localError = 'Failed to join room.'
        }
      } catch (e) {
        this.localError = e?.response?.data?.errors || e?.response?.data?.message || 'Failed to join room.'
      } finally {
        this.joiningRoom = false
      }
    },
    retrieveRooms() {
      RoomListService.getRooms()
        .then(response => {
          this.rooms = response.data;
        })
        .catch(e => {
          console.log(e);
        })
    },
    async createRoom() {
      this.localError = '';
      if (!this.newRoom.name) {
        this.localError = "Room name is required.";
        return;
      }
      this.creatingRoom = true;
      try {
        const payload = { name: this.newRoom.name }
        if (this.newRoom.gameVersion) payload.game_version = this.newRoom.gameVersion
        await RoomListService.createRoom(payload);
        this.$refs.createRoomModal.hide();
        this.$router.push({ name: 'Room' });
      } catch (e) {
        if (e.response && e.response.data && e.response.data.message) {
          this.localError = e.response.data.message;
        } else {
          this.localError = "Room already exists. Please quit the previous room first.";
        }
      } finally {
        this.creatingRoom = false;
      }
    },
    formatDuration(startedAt) {
      if (!startedAt) return '—'
      const start = new Date(startedAt)
      const now = new Date()
      const diffMs = now - start
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMins / 60)
      const diffDays = Math.floor(diffHours / 24)
      
      if (diffDays > 0) return `${diffDays}d`
      if (diffHours > 0) return `${diffHours}h`
      if (diffMins > 0) return `${diffMins}m`
      return 'Just now'
    }
  },
  computed: {
    username() {
      return this.$store.state.auth.username
    }
  },
  mounted() {
    this.retrieveRooms();
    this.loadGameVersions();
  },
}
</script>

<style scoped>
.form-hint {
  display: block;
  margin-top: 6px;
  color: #94A3B8;
  font-size: 0.8rem;
}

.form-hint--notes {
  max-height: 90px;
  overflow-y: auto;
  white-space: pre-line;
  color: #CBD5E1;
}

.room-list-page {
  min-height: calc(100vh - 65px);
  padding: 40px 24px 60px;
  background:
    radial-gradient(900px 420px at 50% -10%, rgba(234, 179, 8, 0.08), transparent 70%),
    radial-gradient(700px 400px at 90% 20%, rgba(34, 211, 238, 0.05), transparent 70%),
    #0B0F19;
}

.room-list-container {
  max-width: 1040px;
  margin: 0 auto;
}

/* Header */
.rl-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
  margin-bottom: 28px;
}

.rl-eyebrow {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 0.9rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #22D3EE;
}

.rl-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 2px 0 6px;
  font-size: 2.3rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #F8FAFC;
}

.rl-count {
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(34, 197, 94, 0.14);
  border: 1px solid rgba(34, 197, 94, 0.4);
  color: #86EFAC;
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0;
}

.rl-sub {
  margin: 0;
  font-size: 1rem;
  color: #94A3B8;
}

/* The main button */
.rl-create {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 12px 22px 12px 14px;
  border: 0;
  border-radius: 12px;
  background: linear-gradient(180deg, #FACC15, #EAB308 55%, #CA8A04);
  color: #1c1917 !important;
  font-size: 1rem;
  font-weight: 800;
  text-decoration: none !important;
  box-shadow: 0 10px 24px rgba(234, 179, 8, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.4);
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.rl-create:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 30px rgba(234, 179, 8, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.rl-create__plus {
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.85);
  color: #A16207;
  font-size: 1.25rem;
  font-weight: 900;
  line-height: 1;
}

.rl-create--link { padding: 12px 26px; }

/* Nothing to show */
.rl-empty {
  display: grid;
  justify-items: center;
  gap: 10px;
  padding: 56px 24px 52px;
  border-radius: 20px;
  border: 1px dashed rgba(148, 163, 184, 0.3);
  background: linear-gradient(180deg, rgba(26, 31, 46, 0.75), rgba(18, 23, 38, 0.75));
  text-align: center;
}

.rl-empty__art {
  display: grid;
  place-items: center;
  width: 84px;
  height: 84px;
  margin-bottom: 6px;
  border-radius: 24px;
  background: radial-gradient(circle at 35% 30%, rgba(234, 179, 8, 0.25), rgba(234, 179, 8, 0.05));
  border: 1px solid rgba(234, 179, 8, 0.35);
  font-size: 2.6rem;
}

.rl-empty__title {
  margin: 0;
  font-size: 1.45rem;
  font-weight: 800;
  color: #F1F5F9;
}

.rl-empty__text {
  max-width: 420px;
  margin: 0 0 10px;
  color: #94A3B8;
  line-height: 1.5;
}

/* Room cards */
.rl-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 18px;
}

.rl-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px 20px 18px;
  border-radius: 16px;
  background: linear-gradient(180deg, #1A1F2E, #141927);
  border: 1px solid rgba(148, 163, 184, 0.14);
  overflow: hidden;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.rl-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 3px;
  background: linear-gradient(90deg, #EAB308, #22D3EE);
}

.rl-card:hover {
  transform: translateY(-3px);
  border-color: rgba(234, 179, 8, 0.45);
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.35);
}

.rl-card__top { display: flex; align-items: center; gap: 10px; }

.rl-card__name {
  flex: 1;
  min-width: 0;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 1.3rem;
  font-weight: 800;
  color: #F8FAFC;
}

.rl-card__version {
  padding: 2px 8px;
  border-radius: 6px;
  background: rgba(34, 211, 238, 0.12);
  border: 1px solid rgba(34, 211, 238, 0.35);
  color: #67E8F9;
  font-size: 0.75rem;
  font-weight: 700;
}

.rl-card__host { display: flex; align-items: center; gap: 8px; color: #94A3B8; font-size: 0.9rem; }
.rl-card__host strong { color: #E2E8F0; }

.rl-card__avatar {
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  border-radius: 8px;
  background: linear-gradient(135deg, #22D3EE, #0891B2);
  color: #0B0F19;
  font-size: 0.8rem;
  font-weight: 800;
}

.rl-card__stats { display: flex; flex-wrap: wrap; gap: 6px; }

.rl-chip {
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.1);
  border: 1px solid rgba(148, 163, 184, 0.18);
  color: #CBD5E1;
  font-size: 0.8rem;
  font-weight: 600;
}

.rl-card__actions { display: flex; gap: 8px; margin-top: auto; padding-top: 4px; }

.rl-btn {
  padding: 9px 14px;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease, transform 0.15s ease;
}

.rl-btn--ghost {
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: transparent;
  color: #CBD5E1;
}

.rl-btn--ghost:hover { border-color: #94A3B8; background: rgba(148, 163, 184, 0.1); }

.rl-btn--join {
  flex: 1;
  border: 1px solid #EAB308;
  background: linear-gradient(180deg, #EAB308, #CA8A04);
  color: #1c1917;
}

.rl-btn--join:hover { transform: translateY(-1px); background: linear-gradient(180deg, #FACC15, #EAB308); }

@media (max-width: 600px) {
  .room-list-page { padding: 24px 16px 40px; }
  .rl-title { font-size: 1.8rem; }
  .rl-create { width: 100%; justify-content: center; }
}

.modal-custom-content {
  background: #1A1F2E;
  border-radius: 16px;
  border: 1px solid #22D3EE44;
  overflow: hidden;
}

.modal-custom-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: #0B0F19;
  border-bottom: 1px solid #22D3EE33;
}

.modal-custom-header h2 {
  font-size: 1.4em;
  font-weight: 700;
  color: #EAB308;
  margin: 0;
}

.modal-close-btn {
  background: none;
  border: none;
  color: #64748B;
  font-size: 1.8em;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  transition: color 0.2s;
}

.modal-close-btn:hover {
  color: #F1F5F9;
}

/* Form Styling */
.modal-form {
  padding: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 0.9em;
  font-weight: 600;
  color: #94A3B8;
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 14px 16px;
  background: #0B0F19;
  border: 1px solid #22D3EE44;
  border-radius: 10px;
  color: #F1F5F9;
  font-size: 1em;
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #EAB308;
}

.form-input::placeholder {
  color: #475569;
}

.form-error {
  display: block;
  margin-top: 8px;
  color: #EF4444;
  font-size: 0.85em;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 20px 24px;
}

.btn-cancel {
  background: transparent;
  border: 1px solid #64748B;
  color: #94A3B8;
  padding: 12px 24px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  border-color: #F1F5F9;
  color: #F1F5F9;
}

.btn-create,
.btn-join-large {
  background: linear-gradient(135deg, #EAB308 0%, #CA8A04 100%);
  border: none;
  color: #0B0F19;
  padding: 12px 28px;
  border-radius: 10px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-create:hover,
.btn-join-large:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(234, 179, 8, 0.4);
}

.btn-create:disabled,
.btn-join-large:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* Details Modal Content */
.details-content {
  padding: 24px;
}

.details-info {
  margin-bottom: 24px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #22D3EE11;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  color: #64748B;
  font-size: 0.9em;
}

.info-value {
  color: #F1F5F9;
  font-weight: 600;
}

.details-members h4 {
  font-size: 1em;
  font-weight: 700;
  color: #22D3EE;
  margin: 0 0 12px 0;
}

.members-list {
  background: #0B0F19;
  border-radius: 10px;
  padding: 4px;
  max-height: 200px;
  overflow-y: auto;
}

.member-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  transition: background 0.2s;
}

.member-item:hover {
  background: #1A1F2E;
}

.member-icon {
  font-size: 1.1em;
}

.member-name {
  flex-grow: 1;
  color: #F1F5F9;
}

.member-badge {
  background: #EAB308;
  color: #0B0F19;
  font-size: 0.7em;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  text-transform: uppercase;
}

.no-members {
  text-align: center;
  color: #64748B;
  padding: 20px;
  font-style: italic;
}

/* Responsive */
@media (max-width: 600px) {
  .room-list-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .rooms-grid {
    grid-template-columns: 1fr;
  }
  
  .modal-actions {
    flex-direction: column;
  }
  
  .btn-cancel,
  .btn-create,
  .btn-join-large {
    width: 100%;
  }
}
</style>

<!-- Global modal styles (unscoped because modals are teleported to body) -->
<style>
.custom-modal-content {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

.custom-modal-content .modal-header,
.custom-modal-content .modal-footer {
  display: none !important;
}

.custom-modal-body {
  padding: 0 !important;
  background: transparent !important;
}
</style>







