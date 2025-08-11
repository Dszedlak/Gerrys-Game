from sqlalchemy.orm import session
from . import db, jwt
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

rooms = (db.Table("rooms", db.Column("roomId", db.Integer, db.ForeignKey("room.id"))),)


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), index=True, unique=True)
    score = db.Column(db.Integer, default=0)
    passwordHash = db.Column(db.String(128))
    rooms = db.relationship(
        "Room", secondary="room_participants", lazy="subquery", viewonly=True
    )

    @property
    def password(self):
        raise AttributeError("You stupid idiot")

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
    startedAt = db.Column(db.DateTime, default=datetime.utcnow)
    endedAt = db.Column(db.DateTime, default=datetime.utcnow)
    government = db.relationship(
        "Government", backref="room", uselist=False, lazy="subquery"
    )


class RoomParticipants(db.Model):
    __tablename__ = "room_participants"
    roomId = db.Column(db.Integer, db.ForeignKey("room.id"), primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    clock = db.Column(db.DateTime, default=datetime.min + timedelta(days=1))
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"))
    job = db.relationship("Job")
    bleed = db.Column(db.Integer, default=0)
    user = db.relationship("User")

class Job(db.Model):
    __tablename__ = "job"
    id = db.Column(db.Integer, primary_key=True)
    tier = db.Column(db.Integer)
    name = db.Column(db.String(60), nullable=False)
    type = db.Column(db.String(), nullable=False)


class Government(db.Model):
    __tablename__ = "government"
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(60), default="Democracy")
    room_id = db.Column(db.Integer, db.ForeignKey("room.id"))
    members = db.relationship(
        "GovernmentMember", back_populates="government", lazy="subquery"
    )


class GovernmentMember(db.Model):
    __tablename__ = "government_member"
    id = db.Column(db.Integer, primary_key=True)
    government_id = db.Column(db.Integer, db.ForeignKey("government.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    role = db.Column(
        db.String(32), nullable=False
    )  # e.g. "leader", "advisor", "politburo"
    government = db.relationship("Government", back_populates="members")
    user = db.relationship("User")


def serialize_room(room):
    return {
        "id": room.id,
        "name": room.name,
        # Use room.id as owner if that's your convention (no created_by/owner_id columns)
        "owner_id": room.id,
        "government": serialize_government(room.government),
        "participants": [
            {
                "user_id": rp.userId,
                "username": (rp.user.username if hasattr(rp, "user") and rp.user else None),
                "job_tier": rp.job.tier if rp.job else None,
                "job_name": rp.job.name if rp.job else None,
                "bleed": rp.bleed,
            }
            for rp in room.participants
        ],
    }


def serialize_government(government):
    if not government:        return None
    return {
        "type": getattr(government, "type", None),
        "members": [
            {
                "user_id": gm.user_id,
                "username": gm.user.username if gm.user else None,
                "role": gm.role,
            }
            for gm in (government.members or [])
        ],
    }
