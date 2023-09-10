from flask_restful import Resource, marshal_with
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_socketio import join_room
from datetime import datetime, timedelta
from .. import db
from ..models import Room, RoomParticipants
from .util import ROOMS_FIELDS,JOIN_ROOM_FIELDS,LEAVE_ROOM_FIELDS,roomParser,joinRoomParser, leaveRoomParser
from ..websocket.game_session import GameSession
from flask.json import jsonify

#Have a log for the game that logs peoples actions to show whether people are cheating

gameThreads = {}

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
		print(parsedArgs["interest_rate"])
		interest_rate = float(parsedArgs["interest_rate"])

		if Room.query.filter_by(id=user).first():
			return jsonify({'errors': 'Room already exists for this user. Please quit a room before making a new one.'}), 400
		
		room = Room(name=name, id=user, interest_rate=interest_rate)
		db.session.add(room)
		db.session.commit()
		game = GameSession(name)
		game.run()

		roomId = user
		participant = RoomParticipants(roomId=roomId, userId=user, timeBank=datetime.min, clock=(datetime.min + timedelta(days=1)))
		db.session.add(participant)
		db.session.commit()

		gameThreads[user] = game
		return room

class JoinRoomResource(Resource):
	@jwt_required()
	@marshal_with(JOIN_ROOM_FIELDS)
	def post(self):
		user = get_jwt_identity()
		parsedArgs = joinRoomParser.parse_args()
		roomId = parsedArgs['roomId']
		participant = RoomParticipants(roomId=roomId, userId=user, timeBank=datetime.min, clock=(datetime.min + timedelta(days=1)))
		db.session.add(participant)
		db.session.commit()

class LeaveRoomResource(Resource):
	@jwt_required()
	@marshal_with(LEAVE_ROOM_FIELDS)
	def post(self):
		user = get_jwt_identity()
		parsedArgs = leaveRoomParser.parse_args()
		roomId = parsedArgs['roomId']
		RoomParticipants.query.filter_by(userId=user, roomId=roomId).delete()
		db.session.commit()

class RemoveRoomResource(Resource):
	@jwt_required()
	@marshal_with(LEAVE_ROOM_FIELDS)
	def post(self):
		user = get_jwt_identity()
		parsedArgs = leaveRoomParser.parse_args()
		roomId = parsedArgs['roomId']
		Room.query.filter_by(id=roomId).delete()
		RoomParticipants.query.filter_by(roomId=roomId).delete()
		db.session.commit()
		game : GameSession = gameThreads.get(user)
		game.closeRoom()
		del game