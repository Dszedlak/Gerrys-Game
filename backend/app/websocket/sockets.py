from app.models import db

from flask_socketio import emit, join_room, leave_room, send
from app import socketio
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, db, RoomParticipants, Room
import json
import re
from typing import List
from datetime import datetime, timedelta, date
from math import ceil

@socketio.on('join')
@jwt_required()
def on_join():        
    userData = getUserData()
    print(userData)
    room = userData.roomId  
    timeBank = getTimeBank(userData)
    clock = getClock(userData)
    interestRate = getInterestRate(room).interest_rate
    join_room(room)
    emit('updateRoomId', {'data': room}, to=room)
    emit('setUserId', {'data':get_jwt_identity()})
    emit('updateClock', {'data': clock})
    emit('updateTimeBank', {'data': timeBank})
    emit('updateInterestRate', {'data': interestRate})

#NEED TO RETHINKING HOW THIS TIMEBANK/CLOCK IS STORED AND IN WHAT FORMAT. IS AN INTEGER REALLY THE SMARTEST IDEA?

@socketio.on('leave')
@jwt_required()
def on_leave():
    userData = getUserData()
    room = userData.roomId  
    leave_room(room)
    print("disconnected fam")
    send(str(get_jwt_identity()) + ' has left the room.', to=room)

@socketio.on('updateClock')
@jwt_required()
def on_update(data):
    userData = getUserData()
    action = json.loads(data)

    if isinstance(action, int):
        userData.clock = userData.clock + timedelta(minutes=action)
    print(action)

    pattern = re.compile(r'\d{2}•\d{2}•\d{2}')
    if isinstance(action, str) and re.match(pattern, action):
        diff_in_mins = getTimeDiff(action, userData.clock)
        userData.clock = userData.clock - timedelta(minutes=diff_in_mins)
    db.session.commit()
    clock = getClock(userData)
    emit('updateClock', {'data': clock})

@socketio.on('updateInterestRate')
@jwt_required()
def updateInterest(data):
    userData = getUserData()
    roomid = userData.roomId
    action = json.loads(data)
    room = Room.query.filter_by(id=roomid).first()
    room.interest_rate = action
    db.session.commit()
    interestRate = getInterestRate(roomid).interest_rate
    print(interestRate)
    emit('updateInterestRate', {'data': interestRate})


@socketio.on('updateTimeBank')
@jwt_required()
def on_update(data):
    userData = getUserData()
    action = json.loads(data)
    if isinstance(action, int):
        userData.timeBank = userData.timeBank + timedelta(minutes=action)
    if action == 'clear' or action == 'cashout':
        if action == 'cashout':
            userData.clock = userData.clock + timedelta(days=userData.timeBank.day - 1, hours=userData.timeBank.hour, minutes=userData.timeBank.minute)
        userData.timeBank = datetime.min
    elif action == 'addInterest':
        time_in_mins = ((userData.timeBank - datetime.min).total_seconds()) / 60
        total_interest = (time_in_mins * Room.query.filter_by(id=userData.roomId).first().interest_rate) - time_in_mins
        userData.timeBank = userData.timeBank + timedelta(minutes=total_interest)
        if not userData.timeBank.minute % 5 == 0:
            discard = timedelta(minutes=userData.timeBank.minute % 10)
            userData.timeBank -= discard
            if discard >= timedelta(minutes=5):
                userData.timeBank += timedelta(minutes=10)
    pattern = re.compile(r'\d{2}•\d{2}•\d{2}')
    if isinstance(action, str) and re.match(pattern, action):
        diff_in_mins = getTimeDiff(action, userData.timeBank)
        userData.timeBank = userData.timeBank - timedelta(minutes=diff_in_mins)
            
    db.session.commit()
    timeBank = getTimeBank(userData)
    clock = getClock(userData)
    emit('updateTimeBank', {'data': timeBank})
    emit('updateClock', {'data': clock})

@socketio.on('connect')
@jwt_required()
def on_connect():
    print("Client Connected")

@socketio.on('disconnect')
def disconnect():
    print("Client Disconnected")

def getUserData():
    username = get_jwt_identity()
    user = db.session.query(User.id).filter_by(id=username).first()[0]
    print(user)
    userData = RoomParticipants.query.filter_by(userId=user).first()
    print(userData)
    return userData

def getInterestRate(room_num: int):
    room = Room.query.filter_by(id=room_num).first()
    return room

def timeFormat(time: datetime):
    days = ""
    if time.day == 1:
        days = "00"
    else:
        time = time - timedelta(days=1)
        days = str(time)[8:10]
    
    hours = str(time)[11:13]
    minutes = str(time)[14:16]

    return days+"•"+hours+"•"+minutes

def getClock(userData) -> datetime:
    return json.dumps(timeFormat(userData.clock), indent=4, sort_keys=True, default=str)

def getTimeBank(userData) -> datetime: 
    return json.dumps(timeFormat(userData.timeBank), indent=4, sort_keys=True, default=str)

def getTimeDiff(newTime: str, oldTime: datetime) -> int: 
    dhs = getDayHourSec(newTime)
    dhs = oldTime - dhs
    diff = dhs.total_seconds() / 60
    return diff

def getDayHourSec(time: str) -> datetime:
    ddhhmm = re.sub("[^0-9]", "", time)
    newTime = datetime.min
    newTime = newTime + timedelta(days=int(str(ddhhmm)[:2]), hours=int(str(ddhhmm)[2:4]), minutes=int(str(ddhhmm)[4:6]))
    return newTime
