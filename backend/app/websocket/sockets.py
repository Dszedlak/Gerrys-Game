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

    room_identifier = str(room.id)
    join_room(room_identifier)
    print(f"[join] user {user_id} joined socket room {room_identifier}")
    print(f"[join] userData.clock = {userData.clock}, formatted = {timeFormat(userData.clock)}")

    # Send collections for dropdowns, then room state
    emit("updateCollectionData", {"data": get_collections()})
    emit("room_state", serialize_room(room), to=room_identifier)
    emit("setUserId", {"data": get_jwt_identity()})
    emit("updateClock", {"data": getClock(userData)})
    print("user joined room:", room_identifier)


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
    
    # Emit to the user who made the update
    emit("updateClock", {"data": clock})
    
    # Broadcast this user's clock update to everyone in the room
    room = Room.query.get(userData.roomId)
    if room:
        formatted_clock = timeFormat(userData.clock)
        room_identifier = str(room.id)
        print(f"[updateClock] Broadcasting clock update for user {userData.userId}: {formatted_clock} to room {room_identifier}")
        socketio.emit("userClockUpdate", {
            "user_id": userData.userId,
            "clock": formatted_clock
        }, room=room_identifier)

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
    if gov_type not in {"Democracy", "Dictatorship", "Republic", "Communism", "Anarchy"}:
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
    emit("room_state", serialize_room(room), to=str(room.id))


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
    
    # Add perk bonus
    perk_bonus = 0
    if userData.perk == "Manager":
        perk_bonus = 10
    elif userData.perk == "Senior":
        perk_bonus = 20
    elif userData.perk == "Executive":
        perk_bonus = 30
    
    # Check if government is Communism
    room = Room.query.get(userData.roomId)
    communist_penalty = 0
    if room and room.government and room.government.type == "Communism":
        communist_penalty = 10
        print(f"[balanceChange] Communist government detected, applying -10 minute penalty")
    
    bleed_penalty = userData.bleed * 10
    net_income = job_income + perk_bonus - bleed_penalty - communist_penalty
    
    print(f"[balanceChange] Bleed: {userData.bleed}, penalty: {bleed_penalty}, perk: {userData.perk}, perk_bonus: {perk_bonus}, communist_penalty: {communist_penalty}, net: {net_income}")
    
    # Calculate new clock value, but don't let it go below datetime.min (00•00•00)
    try:
        new_clock = userData.clock + timedelta(minutes=net_income)
        # Ensure it doesn't go below datetime.min
        if new_clock < datetime.min:
            userData.clock = datetime.min
            print(f"[balanceChange] Clock would underflow, setting to 00•00•00")
        else:
            userData.clock = new_clock
    except (OverflowError, ValueError):
        # If overflow occurs, set to minimum
        userData.clock = datetime.min
        print(f"[balanceChange] Clock overflow detected, setting to 00•00•00")
    
    db.session.commit()
    
    # Emit to the user who made the update
    formatted_clock = timeFormat(userData.clock)
    emit("updateClock", {"data": formatted_clock})
    
    # Broadcast this user's clock update to everyone in the room
    if room:
        room_identifier = str(room.id)
        socketio.emit("userClockUpdate", {
            "user_id": userData.userId,
            "clock": formatted_clock
        }, room=room_identifier)


@socketio.on("updateJob")
@jwt_required()
def update_job(data):
    userData = getUserData()
    action = json.loads(data)
    job_id = action.get("job_id", None)

    job = None
    if job_id is None:
        userData.job_id = None
    else:
        job = Job.query.filter_by(id=job_id).first()
        if not job or job.tier > 6:
            emit("error", {"message": "Invalid job selection."})
            return
        userData.job_id = job.id

    db.session.commit()
    db.session.flush()  # Ensure changes are immediately visible
    
    # Send targeted update for just this user's job
    room = Room.query.filter_by(id=userData.roomId).first()
    socketio.emit("userJobUpdate", {
        "user_id": userData.userId,
        "job_name": job.name if job else None,
        "job_tier": job.tier if job else None
    }, room=str(room.id))
    
    print(f"[updateJob] Sent job update for user {userData.userId}: {job.name if job else 'None'}")


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
    emit("room_state", serialize_room(room), to=str(room.id))


@socketio.on("updatePerk")
@jwt_required()
def update_perk(data):
    print("attempting to update perk: " + str(data))
    userData = getUserData()
    action = json.loads(data) if isinstance(data, (str, bytes)) else data
    perk_value = action.get("perk", None) if isinstance(action, dict) else action
    
    # Validate perk value
    if perk_value not in [None, "Manager", "Senior", "Executive"]:
        emit("error", {"message": "Invalid perk value"})
        return
    
    userData.perk = perk_value
    db.session.commit()
    db.session.flush()  # Ensure changes are immediately visible
    
    room = Room.query.filter_by(id=userData.roomId).first()
    # Send targeted update for just this user's perk
    socketio.emit("userPerkUpdate", {
        "user_id": userData.userId,
        "perk": perk_value
    }, room=str(room.id))
    
    print(f"[updatePerk] Sent perk update for user {userData.userId}: {perk_value}")


@socketio.on("updateHeat")
@jwt_required()
def update_heat(data):
    print("attempting to update heat" + data)
    userData = getUserData()
    action = json.loads(data)
    heat_amount = int(action)
    userData.heat += heat_amount
    db.session.commit()
    room = Room.query.filter_by(id=userData.roomId).first()
    print(serialize_room(room))
    emit("room_state", serialize_room(room), to=str(room.id))


@socketio.on("balanceBooks")
@jwt_required()
def balance_books(data=None):
    print("[balanceBooks] Starting wealth redistribution")
    user_id = get_jwt_identity()
    userData = RoomParticipants.query.filter_by(userId=user_id).first()
    if not userData:
        emit("error", {"message": "Not in a room"})
        return
    
    room = Room.query.get(userData.roomId)
    if not room:
        emit("error", {"message": "Room not found"})
        return
    
    # Get all participants
    participants = RoomParticipants.query.filter_by(roomId=room.id).all()
    if len(participants) < 2:
        emit("error", {"message": "Need at least 2 players to balance books"})
        return
    
    # Calculate total minutes up to 12 hours per person
    TWELVE_HOURS_MINUTES = 12 * 60
    total_shareable_minutes = 0
    participant_data = []
    
    for p in participants:
        # Convert clock to total minutes from epoch
        clock_delta = p.clock - datetime.min
        total_minutes = int(clock_delta.total_seconds() / 60)
        
        shareable = min(total_minutes, TWELVE_HOURS_MINUTES)
        excess = max(0, total_minutes - TWELVE_HOURS_MINUTES)
        
        total_shareable_minutes += shareable
        participant_data.append({
            'participant': p,
            'total_minutes': total_minutes,
            'shareable': shareable,
            'excess': excess
        })
    
    # Calculate equal share (round to nearest 10 minutes)
    equal_share = total_shareable_minutes // len(participants)
    equal_share = round(equal_share / 10) * 10
    
    # Redistribute wealth
    for data in participant_data:
        p = data['participant']
        new_total = equal_share + data['excess']
        p.clock = datetime.min + timedelta(minutes=new_total)
    
    db.session.commit()
    print(f"[balanceBooks] Redistributed {total_shareable_minutes} minutes equally among {len(participants)} players")
    
    # Print each user's final clock value
    print("[balanceBooks] Final clock values:")
    for data in participant_data:
        p = data['participant']
        username = p.user.username if hasattr(p, 'user') and p.user else f"User_{p.userId}"
        clock_formatted = timeFormat(p.clock)
        print(f"  - {username} (ID: {p.userId}): {clock_formatted}")
    
    # Create a dict of all users' updated clocks
    all_clocks = {}
    for data in participant_data:
        p = data['participant']
        all_clocks[p.userId] = timeFormat(p.clock)
    
    # Broadcast all clock updates to the room
    socketio.emit("updateAllClocks", {"clocks": all_clocks}, to=str(room.id))
    
    # Broadcast room_state to update participant list
    emit("room_state", serialize_room(room), to=str(room.id))


def getUserData():
    username = get_jwt_identity()
    user = db.session.query(User.id).filter_by(id=username).first()[0]
    userData = RoomParticipants.query.filter_by(userId=user).first()
    return userData


@socketio.on("setApprovalStatus")
@jwt_required()
def set_approval_status(data=None):
    """Set player's approval status in government"""
    print("[setApprovalStatus] Received request")
    user_id = get_jwt_identity()
    
    try:
        payload = json.loads(data) if isinstance(data, str) else data
        approval_status = payload.get("status")  # 'approve', 'disapprove', 'abstain', or None to clear
    except Exception as e:
        print(f"[setApprovalStatus] Parse error: {e}")
        emit("error", {"message": "Invalid payload"})
        return
    
    userData = RoomParticipants.query.filter_by(userId=user_id).first()
    if not userData:
        emit("error", {"message": "Not in a room"})
        return
    
    room = Room.query.get(userData.roomId)
    if not room:
        emit("error", {"message": "Room not found"})
        return
    
    # Allow setting approval status even without government
    # Store in a custom field or use existing field
    if approval_status is None:
        # Clear approval status
        userData.perk = None
    else:
        userData.perk = f"approval:{approval_status}"
    db.session.commit()
    
    print(f"[setApprovalStatus] User {user_id} set approval to {approval_status}")
    
    # Broadcast to all players in room
    room_identifier = str(room.id)
    socketio.emit("approvalStatusUpdated", {
        "user_id": user_id,
        "username": db.session.query(User.username).filter_by(id=user_id).scalar(),
        "status": approval_status
    }, to=room_identifier)


@socketio.on("partakeGovVote")
@jwt_required()
def partake_gov_vote(data=None):
    """Player participates in government vote"""
    print("[partakeGovVote] Received request")
    user_id = get_jwt_identity()
    
    try:
        payload = json.loads(data) if isinstance(data, str) else data
        vote_choice = payload.get("choice")  # 'yes', 'no', 'abstain', or None to clear
    except Exception as e:
        print(f"[partakeGovVote] Parse error: {e}")
        emit("error", {"message": "Invalid payload"})
        return
    
    userData = RoomParticipants.query.filter_by(userId=user_id).first()
    if not userData:
        emit("error", {"message": "Not in a room"})
        return
    
    room = Room.query.get(userData.roomId)
    if not room:
        emit("error", {"message": "Room not found"})
        return
    
    # Update the participant's vote in the database
    userData.gov_vote = vote_choice
    db.session.commit()
    
    print(f"[partakeGovVote] User {user_id} voted {vote_choice}")
    
    # Broadcast vote to room
    room_identifier = str(room.id)
    socketio.emit("voteRecorded", {
        "user_id": user_id,
        "username": db.session.query(User.username).filter_by(id=user_id).scalar(),
        "vote": vote_choice
    }, to=room_identifier)

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


# Dictator bidding state storage (in-memory, per room)
dictator_bids = {}  # { room_id: { user_id: bid_amount, ... } }

@socketio.on("startDictatorBidding")
@jwt_required()
def start_dictator_bidding(data=None):
    """Initiates dictator bidding when admin selects Dictatorship"""
    print("[startDictatorBidding] Received request")
    user_id = get_jwt_identity()
    
    userData = RoomParticipants.query.filter_by(userId=user_id).first()
    if not userData:
        emit("error", {"message": "Not in a room"})
        return
    
    room = Room.query.get(userData.roomId)
    if not room:
        emit("error", {"message": "Room not found"})
        return
    
    # Initialize bidding for this room
    dictator_bids[room.id] = {}
    
    # Broadcast to all players to open bidding modal
    room_identifier = str(room.id)
    socketio.emit("startDictatorBidding", {}, to=room_identifier)
    print(f"[startDictatorBidding] Bidding started for room {room.id}")

@socketio.on("placeDictatorBid")
@jwt_required()
def place_dictator_bid(data=None):
    """Player places a bid for dictator"""
    print("[placeDictatorBid] Received request")
    user_id = get_jwt_identity()
    
    try:
        payload = json.loads(data) if isinstance(data, str) else data
        bid_amount = payload.get("bid_amount")
    except Exception as e:
        print(f"[placeDictatorBid] Parse error: {e}")
        emit("error", {"message": "Invalid payload"})
        return
    
    if not isinstance(bid_amount, (int, float)) or bid_amount <= 0:
        emit("error", {"message": "Invalid bid amount"})
        return
    
    userData = RoomParticipants.query.filter_by(userId=user_id).first()
    if not userData:
        emit("error", {"message": "Not in a room"})
        return
    
    room = Room.query.get(userData.roomId)
    if not room:
        emit("error", {"message": "Room not found"})
        return
    
    # Record the bid
    if room.id not in dictator_bids:
        dictator_bids[room.id] = {}
    
    dictator_bids[room.id][user_id] = bid_amount
    
    # Build tally for broadcast
    tally = {}
    for participant in RoomParticipants.query.filter_by(roomId=room.id):
        tally[participant.userId] = participant.userId in dictator_bids[room.id]
    
    # Broadcast tally update
    room_identifier = str(room.id)
    socketio.emit("biddingTallyUpdate", {"tally": tally}, to=room_identifier)
    print(f"[placeDictatorBid] User {user_id} bid {bid_amount} in room {room.id}")

@socketio.on("concludeDictatorBidding")
@jwt_required()
def conclude_dictator_bidding(data=None):
    """Admin concludes bidding and determines winner"""
    print("[concludeDictatorBidding] Received request")
    user_id = get_jwt_identity()
    
    userData = RoomParticipants.query.filter_by(userId=user_id).first()
    if not userData:
        emit("error", {"message": "Not in a room"})
        return
    
    room = Room.query.get(userData.roomId)
    if not room:
        emit("error", {"message": "Room not found"})
        return
    
    # Check if user is admin (first participant in room by roomId, sorted by userId)
    first_participant = RoomParticipants.query.filter_by(roomId=room.id).order_by(RoomParticipants.userId.asc()).first()
    if not first_participant or first_participant.userId != user_id:
        emit("error", {"message": "Only admin can conclude bidding"})
        return
    
    # Find winner (highest bid)
    room_bids = dictator_bids.get(room.id, {})
    if not room_bids:
        emit("error", {"message": "No bids placed"})
        return
    
    winner_id = max(room_bids.keys(), key=lambda k: room_bids[k])
    winner_bid_minutes = room_bids[winner_id]
    winner_name = db.session.query(User.username).filter_by(id=winner_id).scalar()
    
    # Update winner's clock (subtract the bid amount in minutes)
    winner_participant = RoomParticipants.query.filter_by(userId=winner_id, roomId=room.id).first()
    if winner_participant:
        winner_participant.clock = winner_participant.clock - timedelta(minutes=winner_bid_minutes)
        db.session.commit()
        print(f"[concludeDictatorBidding] Winner {winner_name} (ID: {winner_id}) clock reduced by {winner_bid_minutes} min")
    
    # Create or update government for this room
    government = room.government or Government(type="Dictatorship", room_id=room.id)
    government.type = "Dictatorship"
    db.session.add(government)
    db.session.flush()
    
    # Clear old government members
    GovernmentMember.query.filter_by(government_id=government.id).delete(synchronize_session=False)
    
    # Add dictator as government member
    gov_member = GovernmentMember(
        government_id=government.id,
        user_id=winner_id,
        role="dictator"
    )
    db.session.add(gov_member)
    db.session.commit()
    
    # Clear bidding data
    if room.id in dictator_bids:
        del dictator_bids[room.id]
    
    # Broadcast winner to all players
    room_identifier = str(room.id)
    socketio.emit("dictatorWinner", {
        "winner_id": winner_id,
        "winner_name": winner_name
    }, to=room_identifier)
    
    # Refresh room to get updated participant data
    db.session.refresh(room)
    
    # Broadcast room state update
    room_state = serialize_room(room)
    socketio.emit("room_state", room_state, to=room_identifier)
    
    print(f"[concludeDictatorBidding] Winner: {winner_name} (ID: {winner_id}) in room {room.id}")


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
