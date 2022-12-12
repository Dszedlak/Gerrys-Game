from sqlalchemy.orm import session
from . import db, jwt
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

rooms = db.Table("rooms", db.Column("roomId", db.Integer, db.ForeignKey("room.id"))),

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), index=True, unique=True)
    score = db.Column(db.Integer, default=0)
    passwordHash = db.Column(db.String(128))
    rooms = db.relationship("Room", secondary="room_participants", lazy="subquery", viewonly=True)

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

class Room(db.Model):
    __tablename__ = "room"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
    participants = db.relationship("RoomParticipants", lazy="subquery")
    startedAt = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    endedAt = db.Column(db.DateTime, default=datetime.datetime.utcnow)#TO-DO
    #government = db.relationship("Government", lazy="subquery")

class RoomParticipants(db.Model):
    __tablename__ = "room_participants"
    roomId = db.Column(db.Integer, db.ForeignKey("room.id"), primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    timeBank = db.Column(db.Integer, default=0)#Have add or remove button
    clock = db.Column(db.Integer, default=24)
    #job = db.relationship("Job", lazy="subquery")




class Job(db.Model):
    __tablename__ = "job"
    id = db.Column(db.Integer, primary_key=True)
    tier = db.Column(db.Integer)
    name = db.Column(db.String(60), nullable=False)
    description = db.Column(db.String(), nullable=False)    

class Government(db.Model):
    __tablename__ = "government"
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(60), default="Democracy")
    description = db.Column(db.String(), nullable=False)

class Laws(db.Model):
    __tablename__ = "laws"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
