from flask_restful import Resource, marshal_with
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_socketio import join_room
from datetime import datetime, timedelta
from .. import db
from ..models import Room, RoomParticipants
from .util import (
    ROOMS_FIELDS,
    JOIN_ROOM_FIELDS,
    LEAVE_ROOM_FIELDS,
    roomParser,
    joinRoomParser,
    leaveRoomParser,
)
from ..websocket.game_session import GameSession
from flask.json import jsonify
import traceback

# Have a log for the game that logs peoples actions to show whether people are cheating

gameThreads = {}


class RoomListResource(Resource):
    @jwt_required()
    @marshal_with(ROOMS_FIELDS)
    def get(self):
        rooms = Room.query.all()
        return rooms

    # Create room
    @jwt_required()
    @marshal_with(ROOMS_FIELDS)
    def post(self):
        user = get_jwt_identity()
        parsedArgs = roomParser.parse_args()
        name = parsedArgs["name"]
        if Room.query.filter_by(id=user).first():
            return {"errors": "Room already exists for this user. Please quit a room before making a new one."}, 400  # changed

        room = Room(name=name, id=user)
        db.session.add(room)
        db.session.commit()
        game = GameSession(name)
        game.run()

        roomId = user
        participant = RoomParticipants(
            roomId=roomId, userId=user, clock=(datetime.min + timedelta(days=1))
        )
        db.session.add(participant)
        db.session.commit()

        gameThreads[user] = game
        return room


class JoinRoomResource(Resource):
    @jwt_required()
    def post(self):
        try:
            user_id = get_jwt_identity()
            args = joinRoomParser.parse_args()
            room_id = args.get("roomId")

            print(f"[JoinRoom] user_id={user_id}, room_id={room_id}")

            if room_id is None:
                print("[JoinRoom] Missing roomId in request")
                return {"errors": "roomId is required"}, 400  # changed

            room = Room.query.get(room_id)
            if not room:
                print(f"[JoinRoom] Room not found: {room_id}")
                return {"errors": "Room does not exist"}, 404  # changed

            existing = RoomParticipants.query.filter_by(roomId=room_id, userId=user_id).first()
            if existing:
                print(f"[JoinRoom] User {user_id} already in room {room_id}")
                return {"roomId": room_id}, 200  # changed

            participant = RoomParticipants(
                roomId=room_id,
                userId=user_id,
                clock=(datetime.min + timedelta(days=1)),
            )
            db.session.add(participant)
            db.session.commit()
            print(f"[JoinRoom] User {user_id} joined room {room_id}")

            return {"roomId": room_id}, 200  # changed
        except Exception as e:
            db.session.rollback()
            print(f"[JoinRoom][ERROR] {e}")
            traceback.print_exc()
            return {"errors": "Internal Server Error"}, 500  # changed


class LeaveRoomResource(Resource):
    @jwt_required()
    @marshal_with(LEAVE_ROOM_FIELDS)
    def post(self):
        print("user attempting to leave room")
        user = get_jwt_identity()
        parsedArgs = leaveRoomParser.parse_args()
        roomId = parsedArgs["roomId"]
        RoomParticipants.query.filter_by(userId=user, roomId=roomId).delete()
        db.session.commit()


class RemoveRoomResource(Resource):
    @jwt_required()
    @marshal_with(LEAVE_ROOM_FIELDS)
    def post(self):
        user = get_jwt_identity()
        parsedArgs = leaveRoomParser.parse_args()
        roomId = parsedArgs["roomId"]
        Room.query.filter_by(id=roomId).delete()
        RoomParticipants.query.filter_by(roomId=roomId).delete()
        db.session.commit()
        game: GameSession = gameThreads.get(user)
        game.closeRoom()
        del game
