<template>
<div id="app">
	<b-container class="bv-example-row">
		<div v-if="username">
		<b-button v-b-modal.modal-prevent-closing>Create Room</b-button>
		</div>
		<b-row>
		<b-col>
				<b-table-simple hover small caption-top responive>
					<b-thead>
						<b-tr>
							<b-th>Name</b-th>
						</b-tr>
					</b-thead>
					<b-tbody>
					<b-tr
					v-for="(room, index) in rooms"
					:key="index">
						<b-td><a v-b-modal.JoinRoomModal roomname="room" roomId="room" @click="sendInfo(room.name, room.id)">{{ room.name }}</a></b-td>
					</b-tr>
					</b-tbody>
				</b-table-simple>
			</b-col>
		</b-row>
		</b-container>
			<b-modal 
			id="modal-prevent-closing"
			ref="modal"
			title="Create Room"
			@ok="handleOk">
			<form ref="form" @submit.stop.prevent="handleSubmit">
				<b-form-group
				label="Room name"
				label-for="name-input"
				invalid-feedback="Room Name"
				description="Enter a name for this room"
				>
				<small v-if="errors" class="text-danger">{{errors}}</small>
				<b-form-input
				id="name-input"
				v-model="newRoom.name"
				
				required
				></b-form-input>
				</b-form-group>
				
			</form>
				<template #modal-footer="{ cancel }">
			<!-- Emulate built in modal footer ok and cancel button actions -->
			
			<b-button size="sm" variant="success" @click="createRoom()">
				Create Room
			</b-button>
			<b-button size="sm" variant="danger" @click="cancel()">
				Cancel
			</b-button>
			<!-- Button with custom close trigger value -->      
			</template>
			</b-modal>
				
					<b-modal id="JoinRoomModal" ref="modal" title="Join Room:">Are you sure you want to join room: {{roomname}}
					<template #modal-footer="{ cancel }">
				<!-- Emulate built in modal footer ok and cancel button actions -->
			
					<b-button size="sm" variant="success" @click="joinRoom()">
						Yes
					</b-button>
					<b-button size="sm" variant="danger" @click="cancel()">
						No
					</b-button>
					<!-- Button with custom close trigger value -->      
					</template>	
					</b-modal>	
					<b-modal id="LeaveRoomModal" ref="modal" title="Leave Room:">Are you sure you want to Leave room: {{roomname}}
					<template #modal-footer="{ cancel }">
				<!-- Emulate built in modal footer ok and cancel button actions -->
			
					<b-button size="sm" variant="success" @click="leaveRoom()">
						Yes
					</b-button>
					<b-button size="sm" variant="danger" @click="cancel()">
						No
					</b-button>
					<!-- Button with custom close trigger value -->      
					</template>	
					</b-modal>
	</div>
	
</template>
<script>
import RoomListService from "@/services/RoomListService";
export default {
	name: 'RoomList',
	data() {
		return {
			rooms: [],
			selected : null,
			newRoom: {
                name: "",
            },
			roomname: '',
			roomId: ''
		}
	},
	methods: {
		sendInfo(roomname, roomId) {
        this.roomname = roomname;
		this.roomId = roomId;
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
		createRoom() {
            var data = {
                name: this.newRoom.name
            };
            RoomListService.createRoom(data)
            .then(response => {
                this.$router.push({ name: 'Room'})
            })
			.catch(e => {
                this.errors = "Room already exists for this user. Please quit the previous room to create a new one."
				console.log(this.errors)
            });
        },
		joinRoom() {
			var data = {
				roomId: this.roomId
			}
			this.$store.state.auth.roomId = data.data;
            RoomListService.joinRoom(data)
            .then(response => {
                this.$router.push({ name: 'Room'})
            })
            
        },
		leaveRoom() {
			var data = {
				roomId: this.roomId
			}
			this.$store.state.auth.roomId = 0;
            RoomListService.leaveRoom(data)
            .then(response => {
                this.$router.push({ name: 'RoomList'})
            })
            .catch(e => {
                console.log(e);
            });
        },
		handleOk() {
    	// Implement the handleOk method logic here
  		},
    },
		computed: {
			username () {
			return this.$store.state.auth.username
			},
			currentRoomId () {
			return this.$store.state.auth.roomId
			},
			errors () {
      		return this.$store.state.auth.errors
    }
		},
    mounted() {
        this.retrieveRooms();
	},  
}
</script>

<style>
.itemRow{
  height: 118px;
  text-align: center;
}

.leaveButtons {
	padding-top: 50px;
}

tr {
	font-size:25px;
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