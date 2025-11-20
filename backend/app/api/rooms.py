from flask_restful import Resource, marshal_with
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_socketio import join_room
from datetime import datetime, timedelta
from .. import db
from ..models import Room, RoomParticipants, Government, GovernmentMember, db
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
from sqlalchemy import and_

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
        args = roomParser.parse_args()
        name = args["name"]

        if Room.query.filter_by(id=user).first():
            return {"errors": "Room already exists for this user. Please quit a room before making a new one."}, 400

        room = Room(id=user, name=name)
        db.session.add(room)
        db.session.commit()

        # Create per-room Government without setting id
        gov = Government(type="Democracy", room_id=room.id)
        db.session.add(gov)
        db.session.commit()

        participant = RoomParticipants(roomId=room.id, userId=user, clock=(datetime.min + timedelta(days=1)))
        db.session.add(participant)
        db.session.commit()

        # If you manage a game object, guard None access
        game = gameThreads.get(room.id)  # or however you key it
        if game:
            try:
                game.closeRoom()
            except Exception as e:
                print(f"[createRoom] game.closeRoom error: {e}")
            del gameThreads[room.id]

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
    def post(self):
        user_id = get_jwt_identity()
        room = Room.query.filter_by(id=user_id).first()
        if not room:
            return {"errors": "Room not found"}, 404

        room_id = room.id
        print(f"[RemoveRoom] user={user_id} closing room {room_id}")

        game = gameThreads.pop(room_id, None)
        if game:
            try:
                game.closeRoom()
            except Exception as e:
                print(f"[RemoveRoom] game.closeRoom error: {e}")

        try:
            from app import socketio
            socketio.emit("roomClosed", {"roomId": room_id}, to=room_id)
        except Exception as e:
            print(f"[RemoveRoom] socket emit error: {e}")

        try:
            # Get government ids for this room (usually one)
            gov_ids = [gid for (gid,) in db.session.query(Government.id).filter_by(room_id=room_id).all()]
            if gov_ids:
                # Delete members by government_id (no join)
                GovernmentMember.query.filter(GovernmentMember.government_id.in_(gov_ids)).delete(synchronize_session=False)
                # Delete governments
                Government.query.filter(Government.id.in_(gov_ids)).delete(synchronize_session=False)

            # Delete participants
            RoomParticipants.query.filter_by(roomId=room_id).delete(synchronize_session=False)

            # Delete room
            Room.query.filter_by(id=room_id).delete(synchronize_session=False)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"[RemoveRoom][ERROR] {e}")
            return {"errors": "Internal Server Error"}, 500

        print(f"[RemoveRoom] room {room_id} removed")
        return {"success": True}, 200
