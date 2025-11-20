from app.models import db, serialize_room, serialize_government

from flask_socketio import emit, join_room, leave_room, send
from app import socketio
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, db, RoomParticipants, Room, Job, Government, GovernmentMember
import json
import re
from datetime import datetime, timedelta
from app.data_collections.loader import get_collections

def _is_room_member(room_id: int, user_id: int) -> bool:
    return RoomParticipants.query.filter_by(roomId=room_id, userId=user_id).first() is not None

def _get_user_participation(user_id, room_id=None):
    q = RoomParticipants.query.filter_by(userId=user_id)
    if room_id is not None:
        q = q.filter_by(roomId=room_id)
    return q.first()

@socketio.on("join")
@jwt_required()
def on_join(payload=None):
    user_id = get_jwt_identity()
    data = {}
    if isinstance(payload, (str, bytes)):
        try:
            data = json.loads(payload)
        except Exception:
            data = {}
    elif isinstance(payload, dict):
        data = payload or {}

    room_id = data.get("roomId")
    userData = _get_user_participation(user_id, room_id)
    if not userData:
        print(f"[join] No RoomParticipants for user {user_id} (roomId={room_id})")
        emit("error", {"message": "Join the room first"})
        return

    room = Room.query.get(userData.roomId)
    if not room:
        emit("error", {"message": "Room not found"})
        return

    join_room(room.id)
    print(f"[join] user {user_id} joined socket room {room.id}")

    # Send collections for dropdowns, then room state
    emit("updateCollectionData", {"data": get_collections()})
    emit("room_state", serialize_room(room), to=room.id)
    emit("setUserId", {"data": get_jwt_identity()})
    emit("updateClock", {"data": getClock(userData)})
    print("user joined room:", room.id)


@socketio.on("leave")
@jwt_required()
def on_leave(payload=None):
    user_id = get_jwt_identity()
    room_id = None
    if isinstance(payload, dict):
        room_id = payload.get("roomId")
    userData = _get_user_participation(user_id, room_id)
    if not userData:
        print(f"[leave] No participation for user {user_id} (roomId={room_id})")
        return
    leave_room(userData.roomId)
    print(f"[leave] user {user_id} left socket room {userData.roomId}")


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
    user_id = get_jwt_identity()
    print("attempting to change government")
    userData = RoomParticipants.query.filter_by(userId=user_id).first()
    if not userData:
        emit("error", {"message": "Not in a room"}); return

    action = json.loads(data) if isinstance(data, (str, bytes)) else dict(data)
    gov_type = (action.get("type") or "").strip()
    if gov_type not in {"Democracy", "Dictatorship", "Republic", "Communism"}:
        emit("error", {"message": "Invalid government type"}); return

    room = Room.query.get(userData.roomId)
    if not room:
        emit("error", {"message": "Room not found"}); return

    government = room.government or Government(type=gov_type, room_id=room.id)
    government.type = gov_type
    db.session.add(government)
    db.session.flush()

    GovernmentMember.query.filter_by(government_id=government.id).delete(synchronize_session=False)

    members_to_add = []
    if gov_type == "Dictatorship":
        dictator = action.get("dictator")
        if dictator is None or not _is_room_member(room.id, int(dictator)):
            db.session.rollback(); emit("error", {"message": "Invalid dictator"}); return
        members_to_add.append(("dictator", int(dictator)))
    elif gov_type == "Republic":
        head = action.get("head_of_state"); advisors = action.get("advisors") or []
        if head is None or len(advisors) != 2:
            db.session.rollback(); emit("error", {"message": "Need head_of_state + 2 advisors"}); return
        ids = [int(head)] + [int(a) for a in advisors]
        if len(set(ids)) != 3 or not all(_is_room_member(room.id, uid) for uid in ids):
            db.session.rollback(); emit("error", {"message": "Invalid republic members"}); return
        members_to_add.append(("head_of_state", int(head)))
        for adv in advisors:
            members_to_add.append(("advisor", int(adv)))
    elif gov_type == "Communism":
        politburo = action.get("politburo") or []
        if len(politburo) != 3:
            db.session.rollback(); emit("error", {"message": "Need 3 politburo members"}); return
        ids = [int(x) for x in politburo]
        if len(set(ids)) != 3 or not all(_is_room_member(room.id, uid) for uid in ids):
            db.session.rollback(); emit("error", {"message": "Invalid politburo members"}); return
        for pid in ids:
            members_to_add.append(("politburo", pid))

    for role, uid in members_to_add:
        db.session.add(GovernmentMember(government_id=government.id, user_id=uid, role=role))

    db.session.commit()
    print(serialize_room(room))
    emit("room_state", serialize_room(room), to=room.id)


@socketio.on("balanceChange")
@jwt_required()
def balanceChange(data=None):
    userData = getUserData()
    job_income = 0
    if userData.job:
        job_income = userData.job.tier * 10  # Example: tier 3 = 30 mins
        print(f"[balanceChange] User job: {userData.job.name}, tier: {userData.job.tier}, income: {job_income}")
    else:
        print(f"[balanceChange] User has no job")
    
    bleed_penalty = userData.bleed * 10
    net_income = job_income - bleed_penalty
    
    print(f"[balanceChange] Bleed: {userData.bleed}, penalty: {bleed_penalty}, net: {net_income}")
    
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


@socketio.on("updateBleed")
@jwt_required()
def update_bleed(data):
    print("attempting to update bleed" + data)
    userData = getUserData()
    action = json.loads(data)
    bleed_amount = int(action)
    userData.bleed += bleed_amount
    db.session.commit()
    room = Room.query.filter_by(id=userData.roomId).first()
    print(serialize_room(room))
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
