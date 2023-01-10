from flask import Blueprint
from flask_restful import Api

api = Blueprint("api", __name__)

from . import rooms
apiREST = Api(api)
apiREST.add_resource(rooms.RoomListResource, "/rooms")
apiREST.add_resource(rooms.JoinRoomResource, "/rooms/join")
apiREST.add_resource(rooms.LeaveRoomResource, "/rooms/leave")