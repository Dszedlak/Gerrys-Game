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
    
    # If dictator bidding is active for this room, send bidding state to reconnecting user
    if bidding_active.get(room.id, False):
        tally = {}
        bid_amounts = {}
        for participant in RoomParticipants.query.filter_by(roomId=room.id):
            if room.id in dictator_bids and participant.userId in dictator_bids[room.id]:
                tally[participant.userId] = True
                bid_amounts[participant.userId] = dictator_bids[room.id][participant.userId]
            else:
                tally[participant.userId] = False
        emit("startDictatorBidding", {"reconnect": True, "tally": tally, "bid_amounts": bid_amounts})
    
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
        if len(politburo) != 2:
            db.session.rollback(); emit("error", {"message": "Need 2 politburo members"}); return
        ids = [int(x) for x in politburo]
        if len(set(ids)) != 2 or not all(_is_room_member(room.id, uid) for uid in ids):
            db.session.rollback(); emit("error", {"message": "Invalid politburo members"}); return
        for pid in ids:
            members_to_add.append(("politburo", pid))

    for role, uid in members_to_add:
        db.session.add(GovernmentMember(government_id=government.id, user_id=uid, role=role))

    db.session.commit()
    print(serialize_room(room))
    emit("room_state", serialize_room(room), to=str(room.id))


@socketio.on("startPolitburoSpin")
@jwt_required()
def start_politburo_spin(data=None):
    """Broadcasts the politburo wheel spin to all players in the room"""
    print("[startPolitburoSpin] Received request")
    user_id = get_jwt_identity()
    
    # Parse data to get rotation
    rotation = None
    if data:
        try:
            parsed_data = json.loads(data) if isinstance(data, str) else data
            rotation = parsed_data.get('rotation')
        except:
            pass
    
    userData = RoomParticipants.query.filter_by(userId=user_id).first()
    if not userData:
        emit("error", {"message": "Not in a room"})
        return
    
    room = Room.query.get(userData.roomId)
    if not room:
        emit("error", {"message": "Room not found"})
        return
    
    # Broadcast to all players in the room with the rotation data
    room_identifier = str(room.id)
    socketio.emit("startPolitburoSpin", {"rotation": rotation}, to=room_identifier)
    print(f"[startPolitburoSpin] Broadcast spin event to room {room.id} with rotation {rotation}")


@socketio.on("updatePolitburoMembers")
@jwt_required()
def update_politburo_members(data=None):
    """Broadcasts politburo member updates to all players in the room"""
    print("[updatePolitburoMembers] Received request")
    user_id = get_jwt_identity()
    
    # Parse data
    members = []
    if data:
        try:
            parsed_data = json.loads(data) if isinstance(data, str) else data
            members = parsed_data.get('members', [])
        except:
            pass
    
    userData = RoomParticipants.query.filter_by(userId=user_id).first()
    if not userData:
        emit("error", {"message": "Not in a room"})
        return
    
    room = Room.query.get(userData.roomId)
    if not room:
        emit("error", {"message": "Room not found"})
        return
    
    # Broadcast to all players in the room
    room_identifier = str(room.id)
    socketio.emit("politburoMembersUpdate", {"members": members}, to=room_identifier)
    print(f"[updatePolitburoMembers] Broadcast members {members} to room {room.id}")


@socketio.on("closePolitburoModal")
@jwt_required()
def close_politburo_modal(data=None):
    """Broadcasts to all players to close the politburo selection modal"""
    print("[closePolitburoModal] Received request")
    user_id = get_jwt_identity()
    
    userData = RoomParticipants.query.filter_by(userId=user_id).first()
    if not userData:
        return
    
    room = Room.query.get(userData.roomId)
    if not room:
        return
    
    room_identifier = str(room.id)
    socketio.emit("closePolitburoModal", {}, to=room_identifier)
    print(f"[closePolitburoModal] Broadcast to room {room.id}")


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
    
    # Get room and government info
    room = Room.query.get(userData.roomId)
    government_bonus = 0
    
    if room and room.government:
        gov_type = room.government.type
        user_id = userData.userId
        
        # Check if user is in government
        gov_member = GovernmentMember.query.filter_by(
            government_id=room.government.id,
            user_id=user_id
        ).first()
        
        if gov_type == "Communism":
            if gov_member and gov_member.role == "politburo":
                # Politburo members get +10 mins
                government_bonus = 10
                print(f"[balanceChange] Communism: User is politburo member, bonus: +10")
            else:
                # Non-politburo members get -20 mins
                government_bonus = -20
                print(f"[balanceChange] Communism: User is NOT politburo member, penalty: -20")
        
        elif gov_type == "Dictatorship":
            if gov_member and gov_member.role == "dictator":
                # Dictator gets +10 mins
                government_bonus = 10
                print(f"[balanceChange] Dictatorship: User is dictator, bonus: +10")
            else:
                print(f"[balanceChange] Dictatorship: User is not dictator, no special bonus")
    
    bleed_penalty = userData.bleed * 10
    net_income = job_income + perk_bonus + government_bonus - bleed_penalty
    
    print(f"[balanceChange] Bleed: {userData.bleed}, penalty: {bleed_penalty}, perk: {userData.perk}, perk_bonus: {perk_bonus}, government_bonus: {government_bonus}, net: {net_income}")
    
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


@socketio.on("getOutOfJail")
@jwt_required()
def get_out_of_jail(data=None):
    """Handle player paying jail fee - deducts 8 hours (or 12 during dictatorship)"""
    userData = getUserData()
    
    if not userData or not userData.roomId:
        emit("error", {"message": "User not found in a room"})
        return
    
    # Get room and government to determine jail fee
    room = Room.query.get(userData.roomId)
    
    # Default jail fee is 8 hours (480 minutes) for Democracy/Communism/Anarchy/Republic
    # Dictatorship has 12 hours (720 minutes)
    jail_fee = 480  # 8 hours in minutes
    
    if room and room.government and room.government.type == "Dictatorship":
        jail_fee = 720  # 12 hours in minutes for Dictatorship
        print(f"[getOutOfJail] Dictatorship government - jail fee is 12 hours")
    else:
        print(f"[getOutOfJail] Non-dictatorship government - jail fee is 8 hours")
    
    # Check if player has enough time
    current_clock_minutes = (userData.clock - datetime.min).total_seconds() / 60
    if current_clock_minutes < jail_fee:
        emit("error", {"message": f"Not enough time to pay jail fee. Need {jail_fee} minutes, have {int(current_clock_minutes)}"})
        return
    
    # Deduct jail fee
    time_delta = timedelta(minutes=jail_fee)
    userData.clock -= time_delta
    
    db.session.commit()
    
    print(f"[getOutOfJail] User {userData.userId} paid {jail_fee} minutes for jail")
    
    # Emit to the user
    emit("updateClock", {"data": timeFormat(userData.clock)})
    
    # Broadcast room state update
    room = Room.query.filter_by(id=userData.roomId).first()
    if room:
        room_identifier = str(room.id)
        socketio.emit("room_state", serialize_room(room), room=room_identifier)


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
    
    # Get all participants in the room
    all_participants = RoomParticipants.query.filter_by(roomId=room.id).all()
    
    # Filter out dead players (clock at 00•00•00 or very close to it)
    # Dead players have clock at datetime.min which is day=1, hour=0, min=0, sec=0
    # We consider a player "dead" if their clock is less than 1 minute (00•00•00)
    def is_alive(p):
        clock_delta = p.clock - datetime.min
        total_seconds = clock_delta.total_seconds()
        # If total seconds is 0 or negative (somehow), player is dead
        # If clock is exactly 00•00•00 (datetime.min), total_seconds = 0
        is_dead = total_seconds <= 0
        if is_dead:
            username = p.user.username if hasattr(p, 'user') and p.user else f"User_{p.userId}"
            print(f"[balanceBooks] Excluding DEAD player: {username} (clock: {timeFormat(p.clock)})")
        return not is_dead
    
    participants = [p for p in all_participants if is_alive(p)]
    
    print(f"[balanceBooks] Total participants: {len(all_participants)}, Alive (included): {len(participants)}")
    
    if len(participants) < 2:
        emit("error", {"message": "Need at least 2 active players to balance books"})
        return
    
    # Calculate mean average of all revealed times and excess for each player
    TWELVE_HOURS_MINUTES = 12 * 60
    total_minutes_sum = 0
    participant_data = []
    
    for p in participants:
        # Convert clock to total minutes from epoch
        clock_delta = p.clock - datetime.min
        total_minutes = int(clock_delta.total_seconds() / 60)
        
        # Calculate excess (time over 12 hours)
        excess = max(0, total_minutes - TWELVE_HOURS_MINUTES)
        
        total_minutes_sum += total_minutes
        participant_data.append({
            'participant': p,
            'total_minutes': total_minutes,
            'excess': excess
        })
    
    # Calculate mean average of all revealed times
    mean_average = total_minutes_sum // len(participants)
    mean_average = round(mean_average / 10) * 10  # Round to nearest 10 minutes
    
    # Redistribute wealth: each player gets mean average + their excess
    for data in participant_data:
        p = data['participant']
        new_total = mean_average + data['excess']
        p.clock = datetime.min + timedelta(minutes=new_total)
    
    db.session.commit()
    print(f"[balanceBooks] Redistributed based on mean average ({mean_average} minutes) plus individual excess for {len(participants)} players")
    
    # Print each user's final clock value
    print("[balanceBooks] Final clock values:")
    for data in participant_data:
        p = data['participant']
        username = p.user.username if hasattr(p, 'user') and p.user else f"User_{p.userId}"
        clock_formatted = timeFormat(p.clock)
        print(f"  - {username} (ID: {p.userId}): {clock_formatted} (was {data['total_minutes']} mins, excess: {data['excess']} mins)")
    
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
        approval_status = payload.get("status")  # 'approve', 'reject', 'abstain', or None to clear
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
    # Store in the approval_status field
    if approval_status is None:
        # Clear approval status
        userData.approval_status = None
    else:
        userData.approval_status = approval_status
    db.session.commit()
    
    print(f"[setApprovalStatus] User {user_id} set approval to {approval_status}")
    
    # Broadcast to all players in room
    room_identifier = str(room.id)
    socketio.emit("approvalStatusUpdated", {
        "user_id": user_id,
        "username": db.session.query(User.username).filter_by(id=user_id).scalar(),
        "status": approval_status
    }, to=room_identifier)


@socketio.on("startVoting")
@jwt_required()
def start_voting(data=None):
    """Admin initiates a voting session - votes are secret until concluded"""
    print("[startVoting] Received request")
    user_id = get_jwt_identity()
    
    try:
        payload = json.loads(data) if isinstance(data, str) else data
        question = payload.get("question", "Cast your vote on the current matter")
    except Exception as e:
        print(f"[startVoting] Parse error: {e}")
        question = "Cast your vote on the current matter"
    
    userData = RoomParticipants.query.filter_by(userId=user_id).first()
    if not userData:
        emit("error", {"message": "Not in a room"})
        return
    
    room = Room.query.get(userData.roomId)
    if not room:
        emit("error", {"message": "Room not found"})
        return
    
    # Initialize voting for this room
    voting_ballots[room.id] = {}
    voting_active[room.id] = True
    voting_question[room.id] = question
    
    # Clear any existing votes in DB
    for participant in RoomParticipants.query.filter_by(roomId=room.id):
        participant.gov_vote = None
    db.session.commit()
    
    # Build initial tally
    tally = {}
    for participant in RoomParticipants.query.filter_by(roomId=room.id):
        tally[participant.userId] = False
    
    # Broadcast to all players to open voting modal
    room_identifier = str(room.id)
    socketio.emit("startVoting", {
        "question": question,
        "tally": tally
    }, to=room_identifier)
    print(f"[startVoting] Voting started for room {room.id} with question: {question}")


@socketio.on("partakeGovVote")
@jwt_required()
def partake_gov_vote(data=None):
    """Player participates in government vote - vote is kept secret until voting is concluded"""
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
    
    room_identifier = str(room.id)
    
    # Check if this is a secret voting session
    if voting_active.get(room.id):
        # Store vote secretly (only in memory, not DB yet)
        if room.id not in voting_ballots:
            voting_ballots[room.id] = {}
        
        voting_ballots[room.id][user_id] = vote_choice
        
        # Build tally (who has voted, not what they voted)
        tally = {}
        for participant in RoomParticipants.query.filter_by(roomId=room.id):
            tally[participant.userId] = participant.userId in voting_ballots[room.id]
        
        # Broadcast tally update WITHOUT revealing votes
        socketio.emit("voteTallyUpdate", {
            "tally": tally,
            "user_id": user_id  # Just to indicate who just voted
        }, to=room_identifier)
        
        print(f"[partakeGovVote] User {user_id} cast secret vote in room {room.id}")
    else:
        # Legacy behavior: Update the participant's vote in the database and broadcast
        userData.gov_vote = vote_choice
        db.session.commit()
        
        print(f"[partakeGovVote] User {user_id} voted {vote_choice}")
        
        # Broadcast vote to room (old behavior)
        socketio.emit("voteRecorded", {
            "user_id": user_id,
            "username": db.session.query(User.username).filter_by(id=user_id).scalar(),
            "vote": vote_choice
        }, to=room_identifier)


@socketio.on("concludeVoting")
@jwt_required()
def conclude_voting(data=None):
    """Admin concludes voting and reveals all votes"""
    print("[concludeVoting] Received request")
    user_id = get_jwt_identity()
    
    userData = RoomParticipants.query.filter_by(userId=user_id).first()
    if not userData:
        emit("error", {"message": "Not in a room"})
        return
    
    room = Room.query.get(userData.roomId)
    if not room:
        emit("error", {"message": "Room not found"})
        return
    
    # Check if user is admin (room creator)
    if room.id != user_id:
        emit("error", {"message": "Only admin can conclude voting"})
        return
    
    # Get all the secret votes
    ballots = voting_ballots.get(room.id, {})
    
    # Build results with usernames
    results = {}
    for voter_id, vote in ballots.items():
        username = db.session.query(User.username).filter_by(id=voter_id).scalar()
        results[voter_id] = {
            "vote": vote,
            "username": username
        }
        
        # Also update the database
        participant = RoomParticipants.query.filter_by(userId=voter_id, roomId=room.id).first()
        if participant:
            participant.gov_vote = vote
    
    db.session.commit()
    
    # Calculate vote counts
    yes_count = sum(1 for v in ballots.values() if v == 'yes')
    no_count = sum(1 for v in ballots.values() if v == 'no')
    abstain_count = sum(1 for v in ballots.values() if v == 'abstain')
    
    # Determine outcome
    if yes_count > no_count:
        outcome = "PASSED"
    elif no_count > yes_count:
        outcome = "REJECTED"
    else:
        outcome = "TIE"
    
    # Clear voting state
    if room.id in voting_ballots:
        del voting_ballots[room.id]
    if room.id in voting_active:
        del voting_active[room.id]
    if room.id in voting_question:
        del voting_question[room.id]
    
    # Broadcast results to all players
    room_identifier = str(room.id)
    socketio.emit("votingConcluded", {
        "results": results,
        "counts": {
            "yes": yes_count,
            "no": no_count,
            "abstain": abstain_count,
            "total": len(ballots)
        },
        "outcome": outcome
    }, to=room_identifier)
    
    print(f"[concludeVoting] Voting concluded in room {room.id}: {outcome} (Y:{yes_count} N:{no_count} A:{abstain_count})")

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
bidding_active = {}  # { room_id: True/False }

# Voting state storage (in-memory, per room)
# Votes are kept secret until admin concludes voting
voting_ballots = {}  # { room_id: { user_id: vote_choice, ... } }
voting_active = {}  # { room_id: True/False }
voting_question = {}  # { room_id: question_text }

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
    bidding_active[room.id] = True
    
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
    
    # Build tally with bid amounts for broadcast
    tally = {}
    bid_amounts = {}
    for participant in RoomParticipants.query.filter_by(roomId=room.id):
        if participant.userId in dictator_bids[room.id]:
            tally[participant.userId] = True
            bid_amounts[participant.userId] = dictator_bids[room.id][participant.userId]
        else:
            tally[participant.userId] = False
    
    # Broadcast tally update with bid amounts
    room_identifier = str(room.id)
    socketio.emit("biddingTallyUpdate", {"tally": tally, "bid_amounts": bid_amounts}, to=room_identifier)
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
    
    # Check if user is admin (room creator: room.id == user_id)
    if room.id != user_id:
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
    
    # Build leaderboard sorted by bid amount (highest first)
    leaderboard = []
    for user_id_bid, bid_amount in sorted(room_bids.items(), key=lambda x: x[1], reverse=True):
        username = db.session.query(User.username).filter_by(id=user_id_bid).scalar()
        leaderboard.append({
            "user_id": user_id_bid,
            "username": username,
            "bid_amount": bid_amount,
            "is_winner": user_id_bid == winner_id
        })
    
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
    if room.id in bidding_active:
        del bidding_active[room.id]
    
    # Broadcast winner to all players
    room_identifier = str(room.id)
    socketio.emit("dictatorWinner", {
        "winner_id": winner_id,
        "winner_name": winner_name,
        "leaderboard": leaderboard
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
