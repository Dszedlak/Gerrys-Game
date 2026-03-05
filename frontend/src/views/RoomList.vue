<template>
  <div class="room-list-page">
    <div class="room-list-container">
      <!-- Header -->
      <div class="room-list-header">
        <h1 class="room-list-title">Active Games</h1>
        <BButton v-if="username" class="create-room-btn" @click="showCreateRoomModal">
          <span class="btn-icon">+</span> Create Room
        </BButton>
      </div>
      
      <div v-if="!username" class="empty-state">
        <div class="empty-state-icon">🔒</div>
        <p>Please log in to see available rooms.</p>
      </div>
      
      <div v-else-if="rooms.length === 0" class="empty-state">
        <div class="empty-state-icon">🎮</div>
        <p>No rooms available. Create one to get started!</p>
      </div>
      
      <!-- Room Cards Grid -->
      <div v-else class="rooms-grid">
        <div v-for="(room, index) in rooms" :key="index" class="room-card">
          <div class="room-card-header">
            <h3 class="room-card-title">{{ room.name }}</h3>
            <span class="room-card-owner">by {{ room.owner_name || 'Unknown' }}</span>
          </div>
          <div class="room-card-body">
            <div class="room-card-stats">
              <div class="stat">
                <span class="stat-icon">👥</span>
                <span class="stat-value">{{ room.participant_count || 0 }}</span>
                <span class="stat-label">Players</span>
              </div>
              <div class="stat">
                <span class="stat-icon">⏱️</span>
                <span class="stat-value">{{ formatDuration(room.startedAt) }}</span>
                <span class="stat-label">Open</span>
              </div>
            </div>
          </div>
          <div class="room-card-actions">
            <BButton class="btn-details" @click.prevent="showDetailsModal(room)">
              Details
            </BButton>
            <BButton class="btn-join" @click.prevent="quickJoin(room)">
              Join
            </BButton>
          </div>
        </div>
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
      },
      localError: '',
      creatingRoom: false,
      joiningRoom: false
    }
  },
  methods: {
    showCreateRoomModal() {
      this.localError = '';
      this.newRoom.name = '';
      this.$refs.createRoomModal.show();
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
        const response = await RoomListService.createRoom({ name: this.newRoom.name });
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
  },
}
</script>

<style scoped>
.room-list-page {
  background: #0B0F19;
  min-height: 100vh;
  padding: 30px 20px;
  color: #F1F5F9;
}

.room-list-container {
  max-width: 900px;
  margin: 0 auto;
}

/* Header */
.room-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #22D3EE33;
}

.room-list-title {
  font-size: 2em;
  font-weight: 700;
  color: #EAB308;
  margin: 0;
}

.create-room-btn {
  background: linear-gradient(135deg, #1A1F2E 0%, #0B0F19 100%) !important;
  border: 2px solid #EAB308 !important;
  border-radius: 12px !important;
  padding: 12px 24px !important;
  font-weight: 700 !important;
  font-size: 1em !important;
  color: #EAB308 !important;
  transition: all 0.3s ease !important;
  display: flex;
  align-items: center;
  gap: 8px;
}

.create-room-btn:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 4px 20px rgba(234, 179, 8, 0.3) !important;
}

.btn-icon {
  font-size: 1.3em;
  font-weight: 300;
}

/* Empty State */
.empty-state {
  background: #1A1F2E;
  border-radius: 16px;
  padding: 60px 40px;
  text-align: center;
  border: 1px solid #22D3EE44;
}

.empty-state-icon {
  font-size: 3em;
  margin-bottom: 16px;
}

.empty-state p {
  color: #94A3B8;
  font-size: 1.1em;
  margin: 0;
}

/* Room Cards Grid */
.rooms-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.room-card {
  background: #1A1F2E;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #22D3EE44;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

.room-card:hover {
  transform: translateY(-4px);
  border-color: #EAB308;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
}

.room-card-header {
  background: linear-gradient(135deg, #0B0F19 0%, #1A1F2E 100%);
  padding: 20px;
  border-bottom: 1px solid #22D3EE33;
}

.room-card-title {
  font-size: 1.2em;
  font-weight: 700;
  color: #EAB308;
  margin: 0 0 4px 0;
}

.room-card-owner {
  font-size: 0.85em;
  color: #64748B;
}

.room-card-body {
  padding: 16px 20px;
  flex-grow: 1;
}

.room-card-stats {
  display: flex;
  gap: 24px;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.stat-icon {
  font-size: 1.2em;
}

.stat-value {
  font-size: 1.1em;
  font-weight: 700;
  color: #22D3EE;
}

.stat-label {
  font-size: 0.75em;
  color: #64748B;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.room-card-actions {
  display: flex;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid #22D3EE22;
}

.btn-details,
.btn-join {
  flex: 1;
  padding: 10px 16px !important;
  font-weight: 600 !important;
  font-size: 0.9em !important;
  border-radius: 8px !important;
  transition: all 0.2s ease !important;
}

.btn-details {
  background: transparent !important;
  border: 1px solid #64748B !important;
  color: #94A3B8 !important;
}

.btn-details:hover {
  border-color: #22D3EE !important;
  color: #22D3EE !important;
}

.btn-join {
  background: linear-gradient(135deg, #EAB308 0%, #CA8A04 100%) !important;
  border: none !important;
  color: #0B0F19 !important;
}

.btn-join:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 4px 15px rgba(234, 179, 8, 0.4) !important;
}

/* Modal inner content styling */

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







