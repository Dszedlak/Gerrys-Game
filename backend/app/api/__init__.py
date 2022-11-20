from flask import Blueprint
from flask_restful import Api

api = Blueprint("api", __name__)

from . import quizzes, rooms
apiREST = Api(api)
apiREST.add_resource(quizzes.QuizListResource, "/quizzes")
apiREST.add_resource(quizzes.QuizResource, "/quiz/<quizId>")
apiREST.add_resource(rooms.RoomListResource, "/rooms")
apiREST.add_resource(rooms.JoinRoomResource, "/rooms/join")