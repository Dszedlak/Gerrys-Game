import ApiService from "./ApiService"

class RoomListService {
 
  getRooms() {
    return ApiService.get("rooms");
  }

  createRoom(data) {
		return ApiService.post("rooms", data);
	}

  joinRoom(data) {
		return ApiService.post("rooms/join", data);
	}

  leaveRoom(data) {
		return ApiService.post("rooms/leave", data);
	}

  removeRoom(data) {
    return ApiService.post("rooms/remove", data);
  }
};

export default new RoomListService();