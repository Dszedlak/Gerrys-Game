from flask import Blueprint
from flask_restful import Api

api = Blueprint("api", __name__)

from . import rooms, leaderboard, game_versions_api

apiREST = Api(api)
apiREST.add_resource(leaderboard.LeaderBoardResource, "/leaderboard")
apiREST.add_resource(leaderboard.FriendsLeaderBoardResource, "/leaderboard/friends")
apiREST.add_resource(rooms.RoomListResource, "/rooms")
apiREST.add_resource(rooms.JoinRoomResource, "/rooms/join")
apiREST.add_resource(rooms.LeaveRoomResource, "/rooms/leave")
apiREST.add_resource(rooms.RemoveRoomResource, "/rooms/remove")
apiREST.add_resource(rooms.RoomHistoryResource, "/rooms/history")
apiREST.add_resource(rooms.SetWinnerResource, "/rooms/winner")
apiREST.add_resource(game_versions_api.GameVersionListResource, "/game-versions")
apiREST.add_resource(game_versions_api.GameVersionExportResource, "/game-versions/<string:key>/export")
