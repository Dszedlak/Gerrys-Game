from sqlalchemy.orm import session
from . import db, jwt
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

quizRooms = db.Table("quiz_rooms",
    db.Column("roomId", db.Integer, db.ForeignKey("room.id")),
    db.Column("quizId", db.Integer, db.ForeignKey("quiz.id")))

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), index=True, unique=True)
    passwordHash = db.Column(db.String(128))
    rooms = db.relationship("Room", secondary="room_participants", lazy="subquery", viewonly=True)
    quizzes = db.relationship("Quiz", viewonly=True)

    @property
    def password(self):
        raise AttributeError("You stupid fucking idiot")

    @password.setter
    def password(self, newPassword):
        self.passwordHash = generate_password_hash(newPassword)

    def verifyPassword(self, testPassword):
        return check_password_hash(self.passwordHash, testPassword)

@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id

@jwt.user_lookup_loader
def user_lookup_callback(jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.filter_by(id=identity).one_or_none()

class Quiz(db.Model):
    __tablename__ = "quiz"
    id = db.Column(db.Integer, primary_key=True)
    creatorId = db.Column(db.Integer, db.ForeignKey("user.id"))
    creator = db.relationship("User", lazy=True)
    name = db.Column(db.String(60), nullable=False)
    description = db.Column(db.Text())
    questions = db.relationship("Question", lazy=True)
    rooms = db.relationship("Room", secondary=quizRooms, lazy="subquery")
    createdAt = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    modifiedAt = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Question(db.Model):
    __tablename__ = "question"
    id = db.Column(db.Integer, primary_key=True)
    quizId = db.Column(db.Integer, db.ForeignKey("quiz.id"))
    typeId = db.Column(db.Integer, db.ForeignKey("question_type.id"), nullable=False)
    type = db.relationship("QuestionType", lazy=True)
    data = db.Column(db.JSON())
    answer = db.relationship("Answer", lazy=True)
    createdAt = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    modifiedAt = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Answer(db.Model):
    __tablename__ = "answer"
    id = db.Column(db.Integer, primary_key=True)
    questionId = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=False)
    typeId = db.Column(db.Integer, db.ForeignKey("answer_type.id"), nullable=False)
    type = db.relationship("AnswerType", lazy=True)
    data = db.Column(db.JSON())
    createdAt = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    modifiedAt = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Room(db.Model):
    __tablename__ = "room"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
    quizId = db.Column(db.Integer, db.ForeignKey("quiz.id"))
    quiz=db.relationship("Quiz", lazy="subquery")
    participants = db.relationship("RoomParticipants", lazy="subquery")
    masterId = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    master = db.relationship("User", lazy=True)
    stateId = db.Column(db.Integer, db.ForeignKey("room_state.id"), nullable=False)
    state = db.relationship("RoomState", lazy=True)
    startedAt = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    endedAt = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class RoomParticipants(db.Model):
    __tablename__ = "room_participants"
    roomId = db.Column(db.Integer, db.ForeignKey("room.id"), primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    score = db.Column(db.Integer)
    isReady = db.Column(db.Boolean)

class QuestionType(db.Model):
    __tablename__ = "question_type"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)

class AnswerType(db.Model):
    __tablename__ = "answer_type"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)

class RoomState(db.Model):
    __tablename__ = "room_state"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
