from flask_restful import fields, reqparse

USER_FIELDS = {
	"id": fields.Integer,
	"username": fields.String,
}

LEADERBOARD_FIELDS = {
	"username": fields.String,
    "score": fields.Integer,
}

ROOMS_FIELDS = {
	"id": fields.Integer,
	"name": fields.String,
	"master": fields.Nested(USER_FIELDS),
	"createdAt": fields.DateTime,
	"modifiedAt": fields.DateTime,
	"governmentType": fields.String
}

JOIN_ROOM_FIELDS = {	
	"roomId": fields.Integer
}

LEAVE_ROOM_FIELDS = {
	"roomId": fields.Integer
}

ROOM_WAITING_FIELDS = {
	"user_id"
}

roomParser = reqparse.RequestParser()
roomParser.add_argument("name", type=str, required=True)
roomParser.add_argument("interest_rate", type=float, required=True)

joinRoomParser = reqparse.RequestParser()
joinRoomParser.add_argument("roomId", type=int, required=True)

leaveRoomParser = reqparse.RequestParser()
leaveRoomParser.add_argument("roomId", type=int, required=True)

removeRoomParser = reqparse.RequestParser()
removeRoomParser.add_argument("roomId", type=int, required=True)
