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
};

export default new RoomListService();