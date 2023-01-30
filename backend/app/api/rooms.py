from flask_restful import Resource, marshal_with
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_socketio import join_room
from datetime import datetime, timedelta
from .. import db
from ..models import Room, RoomParticipants, Government, Job
from .util import ROOMS_FIELDS,JOIN_ROOM_FIELDS,LEAVE_ROOM_FIELDS,roomParser,joinRoomParser
from ..websocket.game_session import GameSession
from app import socketio
#Have a log for the game that logs peoples actions to show whether people are cheating

class RoomListResource(Resource):
	@jwt_required()
	@marshal_with(ROOMS_FIELDS)
	def get(self):
		rooms = Room.query.all()
		return rooms

#Create room
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
		game = GameSession(name)
		game.run()
		return room

class JoinRoomResource(Resource):
	@jwt_required()
	@marshal_with(JOIN_ROOM_FIELDS)
	def post(self):
		user = get_jwt_identity()
		parsedArgs = joinRoomParser.parse_args()
		roomId = parsedArgs['roomId']
		participant = RoomParticipants(roomId=roomId, userId=user, timeBank=datetime.min, clock=(datetime.min + timedelta(days=1)))
		#participant = RoomParticipants(roomId=roomId, userId=user, timeBank=0, clock=24, job=Job.query.filter_by(name="None").first(), isReady=False)
		db.session.add(participant)
		db.session.commit()

class LeaveRoomResource(Resource):
	@jwt_required()
	@marshal_with(LEAVE_ROOM_FIELDS)
	def post(self):
		user = get_jwt_identity()
		parsedArgs = joinRoomParser.parse_args()
		roomId = parsedArgs['roomId']
		RoomParticipants.query.filter_by(userId=user, roomId=roomId).delete()
		db.session.commit()