from app.models import db, serialize_room, serialize_government

from flask_socketio import emit, join_room, leave_room, send
from app import socketio
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, db, RoomParticipants, Room, Job
import json
import re
from datetime import datetime, timedelta


@socketio.on("join")
@jwt_required()
def on_join():
    userData = getUserData()
    room = Room.query.filter_by(id=userData.roomId).first()
    join_room(room.id)
    emit("room_state", serialize_room(room), to=room.id)
    emit("setUserId", {"data": get_jwt_identity()})
    emit("updateClock", {"data": getClock(userData)})


@socketio.on("leave")
@jwt_required()
def on_leave():
    userData = getUserData()
    room = userData.roomId
    leave_room(room)
    print("disconnected fam")
    send(str(get_jwt_identity()) + " has left the room.", to=room)


@socketio.on("updateClock")
@jwt_required()
def on_update(data):
    userData = getUserData()
    action = json.loads(data)

    if isinstance(action, int):
        userData.clock = userData.clock + timedelta(minutes=action)
    print(action)

    pattern = re.compile(r"\d{2}•\d{2}•\d{2}")
    if isinstance(action, str) and re.match(pattern, action):
        diff_in_mins = getTimeDiff(action, userData.clock)
        userData.clock = userData.clock - timedelta(minutes=diff_in_mins)
    db.session.commit()
    clock = getClock(userData)
    emit("updateClock", {"data": clock})


@socketio.on("connect")
@jwt_required()
def on_connect():
    print("Client Connected")


@socketio.on("disconnect")
def disconnect():
    print("Client Disconnected")


@socketio.on("updateGovernment")
@jwt_required()
def update_government(data):
    userData = getUserData()
    action = json.loads(data)

    if isinstance(action, dict):
        government = userData.room.government
        if government:
            government.type = action.get("type", government.type)
            government.description = action.get("description", government.description)
            db.session.commit()
            # Notify all clients in the room of the updated room state
            room = Room.query.filter_by(id=userData.roomId).first()
            emit("room_state", serialize_room(room), to=room.id)


@socketio.on("balanceChange")
@jwt_required()
def balanceChange():
    userData = getUserData()
    job_income = 0
    if userData.job:
        job_income = userData.job.tier * 10  # Example: tier 3 = 30 mins
    bleed_penalty = userData.bleed * 10
    net_income = job_income - bleed_penalty
    userData.clock += timedelta(minutes=net_income)
    db.session.commit()
    emit("updateClock", {"data": getClock(userData)})


@socketio.on("updateJob")
@jwt_required()
def update_job(data):
    userData = getUserData()
    action = json.loads(data)
    job_id = action.get("job_id", None)

    if job_id is None:
        userData.job_id = None
    else:
        job = Job.query.filter_by(id=job_id).first()
        if not job or job.tier > 6:
            emit("error", {"message": "Invalid job selection."})
            return
        userData.job_id = job.id

    db.session.commit()
    # Notify all clients in the room of the updated room state
    room = Room.query.filter_by(id=userData.roomId).first()
    emit("room_state", serialize_room(room), to=room.id)


def getUserData():
    username = get_jwt_identity()
    user = db.session.query(User.id).filter_by(id=username).first()[0]
    userData = RoomParticipants.query.filter_by(userId=user).first()
    return userData


def timeFormat(time: datetime):
    days = ""
    if time.day == 1:
        days = "00"
    else:
        time = time - timedelta(days=1)
        days = str(time)[8:10]

    hours = str(time)[11:13]
    minutes = str(time)[14:16]

    return days + "•" + hours + "•" + minutes


def getClock(userData) -> datetime:
    return json.dumps(timeFormat(userData.clock), indent=4, sort_keys=True, default=str)


def getTimeDiff(newTime: str, oldTime: datetime) -> int:
    dhs = getDayHourSec(newTime)
    dhs = oldTime - dhs
    diff = dhs.total_seconds() / 60
    return diff


def getDayHourSec(time: str) -> datetime:
    ddhhmm = re.sub("[^0-9]", "", time)
    newTime = datetime.min
    newTime = newTime + timedelta(
        days=int(str(ddhhmm)[:2]),
        hours=int(str(ddhhmm)[2:4]),
        minutes=int(str(ddhhmm)[4:6]),
    )
    return newTime
