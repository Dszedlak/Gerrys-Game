from flask_restful import fields, reqparse

USER_FIELDS = {
	"id": fields.Integer,
	"username": fields.String,
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

ROOM_WAITING_FIELDS = {
	"user_id"
}

roomParser = reqparse.RequestParser()
roomParser.add_argument("name", type=str, required=True)

joinRoomParser = reqparse.RequestParser()
joinRoomParser.add_argument("roomId", type=int, required=True)