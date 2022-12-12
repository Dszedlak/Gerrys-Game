from flask_restful import Resource, marshal_with
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import db
from ..models import Room, RoomParticipants, Government, Job
from .util import ROOMS_FIELDS,JOIN_ROOM_FIELDS, roomParser,joinRoomParser


#Have a log for the game that logs peoples actions to show whether people are cheating

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
		room = Room(name=name, id=user)
		#room = Room(name=name, id=user, state=RoomState.query.filter_by(name="Waiting").first(), government=Government.query.filter_by(name="Democracy").first())
		db.session.add(room)
		db.session.commit()
		return room

class JoinRoomResource(Resource):
	@jwt_required()
	@marshal_with(JOIN_ROOM_FIELDS)
	def post(self):
		user = get_jwt_identity()
		parsedArgs = joinRoomParser.parse_args()
		roomId = parsedArgs['roomId']
		participant = RoomParticipants(roomId=roomId, userId=user, timeBank=0, clock=24)
		#participant = RoomParticipants(roomId=roomId, userId=user, timeBank=0, clock=24, job=Job.query.filter_by(name="None").first(), isReady=False)
		db.session.add(participant)
		db.session.commit()
