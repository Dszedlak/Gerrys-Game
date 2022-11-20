from flask_restful import Resource, marshal_with, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import db
from ..models import Quiz, Question, Answer, QuestionType, AnswerType
from .util import QUIZ_FIELDS, QUIZZES_FIELDS, quizParser, questionParser, answerParser

class QuizListResource(Resource):
	@jwt_required()
	@marshal_with(QUIZZES_FIELDS)
	def get(self):
		user = get_jwt_identity()
		quizzes = Quiz.query.filter_by(creatorId=user).all()
		return quizzes

	@jwt_required()
	@marshal_with(QUIZ_FIELDS)
	def post(self):
		user = get_jwt_identity()
		parsedQuizArgs = quizParser.parse_args()
		quiz = Quiz(creatorId=user, name=parsedQuizArgs["name"], description=parsedQuizArgs["description"])
		for questionReqData in parsedQuizArgs["questions"]:
			parsedQuestionArgs = questionParser.parse_args(req=questionReqData)
			parsedAnswerArgs = answerParser.parse_args(req=parsedQuestionArgs["answer"])
			question = Question(quizId=quiz.id, type=QuestionType.query.filter_by(id=parsedQuestionArgs["type"]).first())
			question.data = parsedQuestionArgs["data"]
			answer = Answer(questionId=question.id, type=AnswerType.query.filter_by(id=parsedAnswerArgs["type"]).first())
			answer.data = parsedAnswerArgs["data"]
			question.answer = answer
			db.session.add(question)
			db.session.add(answer)
		db.session.add(quiz)
		db.session.commit()
		return quiz

class QuizResource(Resource):
	@jwt_required()
	@marshal_with(QUIZ_FIELDS)
	def get(self, quizId):
		user = get_jwt_identity()
		quiz = Quiz.query.filter_by(id=quizId, creatorId=user).first()
		return quiz

	#I am almost positive this will lead to fuckery later.
	#What if someone deletes a quiz that has been played already?
	#What will the scoreboard say?
	@jwt_required()
	@marshal_with(QUIZZES_FIELDS)
	def delete(self, quizId):
		user = get_jwt_identity()
		quiz = Quiz.query.filter_by(id=quizId, creatorId=user).first()
		if not quiz:
			abort(404, message="Quiz {} does not exist".format(quizId))
		for question in quiz.questions:
			db.session.delete(question.answer)
		quiz.questions.clear()
		db.session.delete(quiz)
		db.session.commit()
		quizzes = Quiz.query.filter_by(creatorId=user).all()
		return quizzes

	@jwt_required()
	@marshal_with(QUIZ_FIELDS)
	def put(self, quizId):
		user = get_jwt_identity()
		quiz = Quiz.query.filter_by(id=quizId, creatorId=user).first()
		if quiz == None:
			#fail
			return ""
		parsedQuizArgs = quizParser.parse_args()
		quiz.name = parsedQuizArgs["name"]
		quiz.description = parsedQuizArgs["description"]
		quiz.questions.clear()
		for questionReqData in parsedQuizArgs["questions"]:
			parsedQuestionArgs = questionParser.parse_args(req=questionReqData)
			parsedAnswerArgs = answerParser.parse_args(req=parsedQuestionArgs["answer"])
			question = Question(quizId=quiz.id, type=QuestionType.query.filter_by(id=parsedQuestionArgs["type"]).first())
			question.data = parsedQuestionArgs["data"]
			answer = Answer(questionId=question.id, type=AnswerType.query.filter_by(id=parsedAnswerArgs["type"]).first())
			answer.data = parsedAnswerArgs["data"]
			question.answer = answer
			db.session.add(question)
			db.session.add(answer)
		db.session.commit()
		return quiz