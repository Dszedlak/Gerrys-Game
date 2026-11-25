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

  getRoomHistory(roomId) {
    return ApiService.get(`rooms/history?roomId=${roomId}`);
  }

  // Card sets ("game versions") a new room can be played with
  getGameVersions() {
    return ApiService.get("game-versions");
  }

  setWinner(data) {
    return ApiService.post("rooms/winner", data);
  }
};

export default new RoomListService();