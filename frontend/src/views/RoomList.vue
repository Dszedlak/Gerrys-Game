<template>
  <div id="app">
    <BContainer class="bv-example-row">
      <div v-if="username">
        <BButton @click="showCreateRoomModal">Create Room</BButton>
      </div>
      <BRow>
        <BCol>
          <BTableSimple hover small caption-top responsive>
            <BThead>
              <BTr>
                <BTh>Name</BTh>
              </BTr>
            </BThead>
            <BTbody>
              <BTr v-for="(room, index) in rooms" :key="index">
                <BTd>
                  <a href="#" @click.prevent="showJoinRoomModal(room.name, room.id)">{{ room.name }}</a>
                  <BButton size="sm" class="ms-2" variant="primary" @click.prevent="quickJoin(room)">Join</BButton>
                </BTd>
              </BTr>
            </BTbody>
          </BTableSimple>
        </BCol>
      </BRow>
    </BContainer>

    <!-- Create Room Modal -->
    <BModal
      id="modal-prevent-closing"
      ref="createRoomModal"
      title="Create Room"
      hide-footer
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
      <template #modal-footer="{ cancel }">
        <BButton
          size="sm"
          variant="success"
          @click="createRoom"
          :disabled="creatingRoom"
        >
          Create Room
        </BButton>
        <BButton size="sm" variant="danger" @click="cancel()">
          Cancel
        </BButton>
      </template>
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
      this.localError = '';
      if (!this.newRoom.name) {
        this.localError = "Room name is required.";
        return;
      }
      this.creatingRoom = true;
      try {
        await RoomListService.createRoom({ name: this.newRoom.name });
        this.$refs.createRoomModal.hide();
        this.$router.push({ name: 'Room' });
      } catch (e) {
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
.itemRow {
  height: 118px;
  text-align: center;
}

.leaveButtons {
  padding-top: 50px;
}

tr {
  font-size: 25px;
  text-align: center;
  vertical-align: middle;
}

.butt {
  height: 45px;
}
.bv-example-row {
  padding-left: 120px;
}
</style>