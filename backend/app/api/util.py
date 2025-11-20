from flask_restful import fields, reqparse

LEADERBOARD_FIELDS = {
    "username": fields.String,
    "score": fields.Integer,
}

ROOMS_FIELDS = {
    "id": fields.Integer,
    "name": fields.String,
    "startedAt": fields.DateTime(attribute="startedAt"),
    "endedAt": fields.DateTime(attribute="endedAt"),
    "governmentType": fields.String(
        attribute=lambda x: x.government.type if x.government else None
    ),
    # Optionally, add a nested government field for members, etc.
}

JOIN_ROOM_FIELDS = {"roomId": fields.Integer}

LEAVE_ROOM_FIELDS = {"roomId": fields.Integer}

ROOM_WAITING_FIELDS = {"user_id"}

roomParser = reqparse.RequestParser()
roomParser.add_argument("name", type=str, required=True)

joinRoomParser = reqparse.RequestParser()
joinRoomParser.add_argument("roomId", type=int, required=True)

leaveRoomParser = reqparse.RequestParser()
leaveRoomParser.add_argument("roomId", type=int, required=True)

removeRoomParser = reqparse.RequestParser()
removeRoomParser.add_argument("roomId", type=int, required=True)
