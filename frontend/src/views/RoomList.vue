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
    <BModal id="JoinRoomModal" ref="joinRoomModal" title="Join Room:">
      Are you sure you want to join room: {{ roomname }}
      <template #modal-footer="{ cancel }">
        <BButton size="sm" variant="success" @click="joinRoom">
          Yes
        </BButton>
        <BButton size="sm" variant="danger" @click="cancel()">
          No
        </BButton>
      </template>
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
    }
  },
  methods: {
    showCreateRoomModal() {
      this.localError = '';
      this.newRoom.name = '';
      this.$refs.createRoomModal.show();
    },
    showJoinRoomModal(roomname, roomId) {
      this.roomname = roomname;
      this.roomId = roomId;
      this.$refs.joinRoomModal.show();
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
    joinRoom() {
      var data = {
        roomId: this.roomId
      }
      this.$store.state.auth.roomId = data.roomId;
      RoomListService.joinRoom(data)
        .then(response => {
          this.$refs.joinRoomModal.hide();
          this.$router.push({ name: 'Room' })
        })
    },
    leaveRoom() {
      var data = {
        roomId: this.roomId
      }
      this.$store.state.auth.roomId = 0;
      RoomListService.leaveRoom(data)
        .then(response => {
          this.$refs.leaveRoomModal.hide();
          this.$router.push({ name: 'RoomList' })
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