from flask_restful import fields, reqparse

USER_FIELDS = {
	"id": fields.Integer,
	"username": fields.String,
}

ANSWER_FIELDS = {
	"type": fields.String(attribute="type.name"),
	"data": fields.String,
	"createdAt": fields.DateTime,
	"modifiedAt": fields.DateTime
}

QUESTION_FIELDS = {
	"type": fields.String(attribute="type.name"),
	"data": fields.String,
	"createdAt": fields.DateTime,
	"modifiedAt": fields.DateTime,
	"questions": fields.Nested(ANSWER_FIELDS)
}

QUIZZES_FIELDS = {
	"id": fields.Integer,
	"name": fields.String,
	"description": fields.String,
	"createdAt": fields.DateTime,
	"modifiedAt": fields.DateTime
}

QUIZ_FIELDS = {
	"id": fields.Integer,
	"name": fields.String,
	"description": fields.String,
	"createdAt": fields.DateTime,
	"modifiedAt": fields.DateTime,
	"questions": fields.Nested(QUESTION_FIELDS)
}

ROOMS_FIELDS = {
	"id": fields.Integer,
	"name": fields.String,
	"quiz": fields.String(attribute="quiz.name"),
	"state": fields.String(attribute="state.name"),
	"master": fields.Nested(USER_FIELDS),
	"createdAt": fields.DateTime,
	"modifiedAt": fields.DateTime
}

JOIN_ROOM_FIELDS = {	
	"roomId": fields.Integer
}

ROOM_WAITING_FIELDS = {
	"user_id"
}
quizParser = reqparse.RequestParser()
quizParser.add_argument("name", type=str, required=True)
quizParser.add_argument("description", type=str, required=True)
quizParser.add_argument("questions", type=list, required=True)

questionParser = reqparse.RequestParser()
questionParser.add_argument("data", type=dict, required=True)
questionParser.add_argument("type", type=int, required=True)
questionParser.add_argument("answer", type=dict, required=True)

answerParser = reqparse.RequestParser()
answerParser.add_argument("data", type=dict, required=True, location=('answer',))
answerParser.add_argument("type", type=int, required=True, location=('answer',))

roomParser = reqparse.RequestParser()
roomParser.add_argument("name", type=str, required=True)
roomParser.add_argument("quizId", type=int, required=True)

joinRoomParser = reqparse.RequestParser()
joinRoomParser.add_argument("roomId", type=int, required=True)