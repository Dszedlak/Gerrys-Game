import ApiService from "./ApiService"

class LeaderboardService {
  getLeaderboard() {
    return ApiService.get("leaderboard");
  }

  getFriendsLeaderboard() {
    return ApiService.get("leaderboard/friends");
  }
};

export default new LeaderboardService();