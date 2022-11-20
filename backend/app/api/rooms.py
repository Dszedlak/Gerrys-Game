from flask_restful import Resource, marshal_with
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import db
from ..models import Room, Quiz, RoomParticipants, RoomState
from .util import ROOMS_FIELDS,JOIN_ROOM_FIELDS, roomParser,joinRoomParser

class RoomListResource(Resource):
	@marshal_with(ROOMS_FIELDS)
	def get(self):
		rooms = Room.query.all()
		return rooms

	@jwt_required()
	@marshal_with(ROOMS_FIELDS)
	def post(self):
		user = get_jwt_identity()
		parsedArgs = roomParser.parse_args()
		name = parsedArgs["name"]
		quizId = parsedArgs["quizId"]
		if Quiz.query.filter_by(id=quizId).first() == None:
			#fail
			pass
		room = Room(name=name, masterId=user, quizId=quizId, state=RoomState.query.filter_by(name="Waiting").first())
		db.session.add(room)
		db.session.commit()
		return room

class JoinRoomResource(Resource):
	@jwt_required()
	@marshal_with(JOIN_ROOM_FIELDS)
	def post(self):
		user = get_jwt_identity()
		parsedArgs = joinRoomParser.parse_args()
		print(parsedArgs)
		print(user)
		roomId = parsedArgs['roomId']
		participant = RoomParticipants(roomId=roomId, userId=user, score=0, isReady=False)
		db.session.add(participant)
		db.session.commit()
