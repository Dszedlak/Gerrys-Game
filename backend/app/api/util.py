from flask_restful import fields, reqparse

LEADERBOARD_FIELDS = {
    "username": fields.String,
    "score": fields.Integer,
    "profilePic": fields.String,
}

PARTICIPANT_FIELDS = {
    "user_id": fields.Integer(attribute="userId"),
    "username": fields.String(attribute=lambda x: x.user.username if x.user else None),
}

ROOMS_FIELDS = {
    "id": fields.Integer,
    "name": fields.String,
    "startedAt": fields.DateTime(attribute="startedAt"),
    "endedAt": fields.DateTime(attribute="endedAt"),
    "governmentType": fields.String(
        attribute=lambda x: x.government.type if hasattr(x, 'government') and x.government else None
    ),
    "owner_id": fields.Integer(attribute="id"),
    "owner_name": fields.String(
        attribute=lambda x: next((p.user.username for p in x.participants if p.userId == x.id and p.user), None)
    ),
    "participant_count": fields.Integer(
        attribute=lambda x: len(x.participants) if x.participants else 0
    ),
    "participants": fields.List(fields.Nested(PARTICIPANT_FIELDS)),
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
