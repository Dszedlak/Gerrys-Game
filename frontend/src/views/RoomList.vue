<template>
<div>
<div v-if="username != null">
<b-button v-b-modal.modal-prevent-closing>Create Room</b-button>
</div>
    <b-modal 
      id="modal-prevent-closing"
      ref="modal"
      title="Create Room"
      @show="resetModal"
      @hidden="resetModal"
      @ok="handleOk">
      <form ref="form" @submit.stop.prevent="handleSubmit">
        <b-form-group
          label="Room name"
          label-for="name-input"
          invalid-feedback="Room Name"
		  description="Enter a name for this room"
          :state="nameState">

		<b-form-input
		id="name-input"
		v-model="newRoom.name"
		:state="nameState"
		required
		></b-form-input>
		</b-form-group>

		<b-form-group
          label="Quiz"
          label-for="quiz-input"
          invalid-feedback="Quiz"
		  description="Select a quiz for this room"
          :state="nameState">

		<select v-model="newRoom.quizId" name="quiz" id="quiz" class="form-control" tabindex="12">
   			<option v-for="(quiz, index) in quizzes" :key="index" :value="quiz.id">{{ quiz.name }}</option>
		</select>

        </b-form-group>
			<b-form-group
			label="Create a new quiz?"
			label-for="quiz-input"
			invalid-feedback="Quiz"
			:state="nameState">

			<b-button size="sm" variant="outline-secondary">
				Create Quiz
			</b-button>
			</b-form-group>
	
	</form>
		<template #modal-footer="{ ok, cancel, hide }">
      <!-- Emulate built in modal footer ok and cancel button actions -->
	 
      <b-button size="sm" variant="success"@click="createRoom()">
        Create Room
      </b-button>
      <b-button size="sm" variant="danger" @click="cancel()">
        Cancel
      </b-button>
      <!-- Button with custom close trigger value -->      
    </template>
    </form>
    </b-modal>

		<b-table-simple hover small caption-top responive>
			<b-thead>
				<b-tr>
					<b-th>Name</b-th>
					<b-th>Quiz</b-th>
					<b-th>Room master</b-th>
          			<b-th>Room state</b-th>
				</b-tr>
			</b-thead>
			<b-tbody>
			<b-tr
			v-for="(room, index) in rooms"
			:key="index">
				<b-td><a v-b-modal.JoinRoomModal roomname="room" roomId="room" @click="sendInfo(room.name, room.id)">{{ room.name }}</a></b-td>
        		<b-td><a v-b-modal.JoinRoomModal roomname="room" roomId="room" @click="sendInfo(room.name, room.id)">{{ room.quiz }}</a></b-td>
				<b-td><a v-b-modal.JoinRoomModal roomname="room" roomId="room" @click="sendInfo(room.name, room.id)">{{ room.master.username }}</a></b-td>
        		<b-td><a v-b-modal.JoinRoomModal roomname="room" roomId="room" @click="sendInfo(room.name, room.id)">{{ room.state }}</a></b-td>
			</b-tr>
			</b-tbody>
		</b-table-simple>
			<b-modal id="JoinRoomModal" ref="modal" title="Join Room:">Are you sure you want to join room: {{roomname}}
			<template #modal-footer="{ ok, cancel, hide }">
      	<!-- Emulate built in modal footer ok and cancel button actions -->
	 
			<b-button size="sm" variant="success"@click="joinRoom()">
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
import QuizService from "@/services/QuizService";
export default {
	name: 'RoomList',
	data() {
		return {
			rooms: [],
        	quizzes: [],
			selected : null,
			newRoom: {
                name: "",
                quizId: "" 
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
		retrieveQuizzes() {
			QuizService.getQuizzes()
			.then(response => {
				this.quizzes = response.data;
			})
			.catch(e => {
				console.log(e);
			})
		},
		createRoom() {
            var data = {
                name: this.newRoom.name,
                quizId: this.newRoom.quizId,
            };
			
            RoomListService.createRoom(data)
            .then(response => {
                this.$router.push({ name: 'RoomList'})
            })
            .catch(e => {
                console.log(e);
            });
        },
		joinRoom() {
			var data = {
				roomId: this.roomId
			}
            RoomListService.joinRoom(data)
            .then(response => {
                this.$router.push({ name: 'Room'})
            })
            .catch(e => {
                console.log(e);
            });
        },
    },
		computed: {
			username () {
			return this.$store.state.auth.username
		},
	},
    mounted() {
        this.retrieveRooms();
		this.retrieveQuizzes();
    }
}
</script>