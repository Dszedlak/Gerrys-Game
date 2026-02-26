<template>
  <div id="app">
    <BContainer class="bv-example-row">
      <div v-if="username" class="create-room-btn-container">
        <BButton @click="showCreateRoomModal">+ Create Room</BButton>
      </div>
      
      <div v-if="!username" class="no-auth-message">
        <p>Please log in to see available rooms.</p>
      </div>
      
      <div v-else-if="rooms.length === 0" class="no-rooms-message">
        <p>No rooms available. Create one to get started!</p>
      </div>
      
      <div v-else class="rooms-list">
        <div v-for="(room, index) in rooms" :key="index" class="room-card">
          <div class="room-header">
            <h3 class="room-name">{{ room.name }}</h3>
          </div>
          <div class="room-actions">
            <BButton 
              variant="primary" 
              @click.prevent="showJoinRoomModal(room.name, room.id)"
              class="room-btn-preview"
            >
              View Details
            </BButton>
            <BButton 
              variant="success" 
              @click.prevent="quickJoin(room)"
              class="room-btn-join"
            >
              Join Game
            </BButton>
          </div>
        </div>
      </div>
    </BContainer>

    <!-- Create Room Modal -->
    <BModal
      id="modal-prevent-closing"
      ref="createRoomModal"
      title="Create Room"
      @ok="handleOkCreate"
      ok-title="Create Room"
      cancel-title="Cancel"
      :ok-disabled="creatingRoom"
    >
      <form
        id="create-room-form"
        ref="form"
        @submit.stop.prevent="createRoom"
      >
        <BFormGroup
          label="Room name"
          label-for="name-input"
          invalid-feedback="Room Name"
          description="Enter a name for this room"
        >
          <small v-if="localError" class="text-danger">{{ localError }}</small>
          <BFormInput
            id="name-input"
            v-model="newRoom.name"
            required
          ></BFormInput>
        </BFormGroup>
      </form>
    </BModal>

    <!-- Join Room Modal -->
    <BModal
      id="JoinRoomModal"
      ref="joinRoomModal"
      title="Join Room:"
      @ok="onConfirmJoin"
      ok-title="Yes"
      cancel-title="No"
      :ok-disabled="joiningRoom"
    >
      Are you sure you want to join room: {{ roomname }}
      <div class="mt-2">
        <small v-if="localError" class="text-danger">{{ localError }}</small>
      </div>
    </BModal>

    <!-- Leave Room Modal -->
    <BModal id="LeaveRoomModal" ref="leaveRoomModal" title="Leave Room:">
      Are you sure you want to Leave room: {{ roomname }}
      <template #modal-footer="{ cancel }">
        <BButton size="sm" variant="success" @click="leaveRoom">
          Yes
        </BButton>
        <BButton size="sm" variant="danger" @click="cancel()">
          No
        </BButton>
      </template>
    </BModal>
  </div>
</template>

<script>
import {
  BContainer, BRow, BCol, BButton, BModal, BFormGroup, BFormInput,
  BTableSimple, BThead, BTbody, BTr, BTh, BTd
} from 'bootstrap-vue-next'
import RoomListService from "@/services/RoomListService";

export default {
  name: 'RoomList',
  components: {
    BContainer, BRow, BCol, BButton, BModal, BFormGroup, BFormInput,
    BTableSimple, BThead, BTbody, BTr, BTh, BTd
  },
  data() {
    return {
      rooms: [],
      selected: null,
      newRoom: {
        name: "",
      },
      roomname: '',
      roomId: '',
      localError: '',
      creatingRoom: false
  , joiningRoom: false
    }
  },
  methods: {
    showCreateRoomModal() {
      this.localError = '';
      this.newRoom.name = '';
      this.$refs.createRoomModal.show();
    },
    async handleOkCreate(bvModalEvt) {
      // Prevent modal from closing automatically
      bvModalEvt.preventDefault()
      console.log('[CreateRoom] OK button clicked')
      await this.createRoom()
      // If successful (no error), the createRoom method will hide modal and navigate
      // If error, modal stays open to show error message
    },
    handleCreateRoom() {
      // Trigger form validation and submission
      console.log('[CreateRoom] Button clicked, calling createRoom()')
      this.createRoom()
    },
    async quickJoin(room) {
      try {
        this.roomname = room.name
        this.roomId = room.id
        console.log('[QuickJoin] Direct join for room:', room.name, 'id:', room.id)
        this.joiningRoom = true
        const payload = { roomId: Number(room.id) }
        this.$store.commit('auth/setRoomId', { id: payload.roomId })
        const resp = await RoomListService.joinRoom(payload)
        console.log('[QuickJoin] Response status:', resp?.status)
        if (resp && resp.status >= 200 && resp.status < 300) {
          this.$router.push({ name: 'Room' })
        } else {
          this.localError = 'Failed to join room. Please try again.'
        }
      } catch (e) {
        console.error('[QuickJoin] Error:', e)
        this.localError = e?.response?.data?.errors || e?.response?.data?.message || 'Failed to join room.'
      } finally {
        this.joiningRoom = false
      }
    },
    showJoinRoomModal(roomname, roomId) {
      this.roomname = roomname;
      this.roomId = roomId;
  this.localError = '';
  this.joiningRoom = false;
  console.log('[JoinRoom] Open modal for room:', roomname, 'id:', roomId)
      this.$refs.joinRoomModal.show();
    },
    async onConfirmJoin(bvModalEvt) {
      // Keep the modal open while processing
      bvModalEvt.preventDefault()
      await this.joinRoom()
      // If we reached here without error, hide the modal (route push already navigates)
      if (!this.localError) {
        this.$refs.joinRoomModal.hide()
      }
    },
    showLeaveRoomModal(roomname, roomId) {
      this.roomname = roomname;
      this.roomId = roomId;
      this.$refs.leaveRoomModal.show();
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
      console.log('[CreateRoom] Method called, room name:', this.newRoom.name)
      this.localError = '';
      if (!this.newRoom.name) {
        this.localError = "Room name is required.";
        console.log('[CreateRoom] Validation failed: no room name')
        return;
      }
      console.log('[CreateRoom] Validation passed, creating room...')
      this.creatingRoom = true;
      try {
        const response = await RoomListService.createRoom({ name: this.newRoom.name });
        console.log('[CreateRoom] Success:', response)
        this.$refs.createRoomModal.hide();
        this.$router.push({ name: 'Room' });
      } catch (e) {
        console.error('[CreateRoom] Error:', e)
        // Try to show backend error if available
        if (e.response && e.response.data && e.response.data.message) {
          this.localError = e.response.data.message;
        } else {
          this.localError = "Room already exists for this user. Please quit the previous room to create a new one.";
        }
        console.log(this.localError);
      } finally {
        this.creatingRoom = false;
      }
    },
    async joinRoom() {
      const data = { roomId: Number(this.roomId) }
      this.localError = ''
      this.joiningRoom = true
      const prevRoomId = this.$store.state.auth.roomId
      // Commit via mutation so reactivity is preserved
      try {
        console.log('[JoinRoom] Attempting join with payload:', data)
        this.$store.commit('auth/setRoomId', { id: data.roomId })
        const response = await RoomListService.joinRoom(data)
        console.log('[JoinRoom] Response status:', response?.status)
        // Optional: validate success shape if backend returns { success: true }
        if (response && response.status >= 200 && response.status < 300) {
          this.$refs.joinRoomModal.hide()
          this.$router.push({ name: 'Room' })
        } else {
          this.localError = 'Failed to join room. Please try again.'
        }
      } catch (e) {
        console.error('[JoinRoom] Join failed:', e)
        if (e.response && e.response.data) {
          this.localError = e.response.data.errors || e.response.data.message || 'Failed to join room. Please try again.'
        } else {
          this.localError = 'Network error while joining room.'
        }
        console.log(this.localError)
        // Revert optimistic update
        if (prevRoomId) {
          this.$store.commit('auth/setRoomId', { id: prevRoomId })
        } else {
          this.$store.commit('auth/leaveRoomId')
        }
      } finally {
        this.joiningRoom = false
      }
    },
    leaveRoom() {
      var data = {
        roomId: this.roomId
      }
      this.$store.commit('auth/leaveRoomId')
      RoomListService.leaveRoom(data)
        .then(response => {
          this.$refs.leaveRoomModal.hide();
          this.$router.push({ name: 'Rooms' })
        })
        .catch(e => {
          console.log(e);
        });
    }
  },
  computed: {
    username() {
      return this.$store.state.auth.username
    },
    currentRoomId() {
      return this.$store.state.auth.roomId
    },
    errors() {
      return this.$store.state.auth.errors
    }
  },
  mounted() {
    this.retrieveRooms();
  },
}
</script>

<style>
#app {
  background: #0a0e27;
  min-height: 100vh;
  padding: 5px 20px 30px 20px;
}

.bv-example-row {
  max-width: 1200px;
  margin: 0 auto;
}

.itemRow {
  height: auto;
  text-align: center;
  margin-bottom: 30px;
}

.leaveButtons {
  padding-top: 44px;
}

/* Create Room Button - Prominent Styling */
.create-room-btn-container {
  margin-bottom: 20px;
  display: flex;
  justify-content: center;
}

.create-room-btn-container button {
  background: #0f1535 !important;
  border: 2px solid #00dd33 !important;
  border-radius: 10px !important;
  padding: 14px 32px !important;
  font-weight: 700 !important;
  font-size: 1.1em !important;
  transition: all 0.3s ease !important;
  box-shadow: 0 0 20px rgba(0, 255, 65, 0.3) !important;
  color: #00dd33 !important;
  letter-spacing: 0.5px;
}

.create-room-btn-container button:hover {
  transform: translateY(-3px) !important;
  box-shadow: 0 0 40px rgba(0, 255, 65, 0.6) !important;
  text-shadow: 0 0 10px rgba(0, 255, 65, 0.6) !important;
}

.create-room-btn-container button:active {
  transform: translateY(-1px) !important;
}

/* Empty state messages */
.no-auth-message,
.no-rooms-message {
  background: #0f1535;
  border-radius: 12px;
  padding: 52px 35px;
  text-align: center;
  box-shadow: 0 0 20px rgba(0, 255, 65, 0.2), inset 0 0 15px rgba(0, 255, 65, 0.05);
  margin-top: 40px;
  border: 1px solid rgba(0, 255, 65, 0.2);
}

.no-auth-message p,
.no-rooms-message p {
  color: #00dd33;
  font-size: 1.1em;
  margin: 0;
}

/* Rooms List Layout - Full Width Rows */
.rooms-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 20px;
}

/* Room Card Styling - Full Width Row */
.room-card {
  background: #0f1535;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 0 15px rgba(0, 255, 65, 0.2), inset 0 0 15px rgba(0, 255, 65, 0.05);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: row;
  height: auto;
  border: 1px solid rgba(0, 255, 65, 0.3);
  align-items: center;
}

.room-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 0 25px rgba(0, 255, 65, 0.4), inset 0 0 15px rgba(0, 255, 65, 0.08);
  background: #0f1535;
}

.room-header {
  background: #0a0e27;
  color: #00dd33;
  padding: 12px 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 70px;
  min-width: 180px;
  flex-shrink: 0;
  border-right: 2px solid rgba(0, 255, 65, 0.2);
}

.room-name {
  margin: 0;
  font-size: 1.1em;
  font-weight: 700;
  text-align: center;
  word-break: break-word;
  color: #00dd33;
  text-shadow: 0 0 8px rgba(0, 255, 65, 0.3);
}

.room-actions {
  padding: 12px 20px;
  display: flex;
  gap: 10px;
  flex-direction: row;
  flex-grow: 1;
  justify-content: flex-end;
  align-items: center;
}

.room-btn-preview,
.room-btn-join {
  flex: 0 0 auto;
  font-weight: 600;
  border-radius: 8px;
  padding: 10px 20px !important;
  transition: all 0.2s ease;
  font-size: 0.95em;
}

.room-btn-preview {
  background: #0f1535 !important;
  border: 2px solid #00ccff !important;
  color: #00ccff !important;
  box-shadow: 0 0 10px rgba(0, 204, 255, 0.3) !important;
}

.room-btn-preview:hover {
  box-shadow: 0 0 20px rgba(0, 204, 255, 0.6) !important;
  transform: translateY(-2px);
  text-shadow: 0 0 8px rgba(0, 204, 255, 0.6) !important;
}

.room-btn-join {
  background: #0f1535 !important;
  border: 2px solid #00dd33 !important;
  color: #00dd33 !important;
  box-shadow: 0 0 10px rgba(0, 255, 65, 0.3) !important;
}

.room-btn-join:hover {
  box-shadow: 0 0 20px rgba(0, 255, 65, 0.6) !important;
  transform: translateY(-2px);
  text-shadow: 0 0 8px rgba(0, 255, 65, 0.6) !important;
}

/* Responsive Grid */
@media (max-width: 768px) {
  .rooms-grid {
    grid-template-columns: 1fr;
  }
}
</style>
