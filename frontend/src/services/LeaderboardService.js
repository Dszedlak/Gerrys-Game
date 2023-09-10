import ApiService from "./ApiService"

class LeaderboardService {
  getLeaderboard() {
    return ApiService.get("leaderboard");
  }
};

export default new LeaderboardService();