from app.models import db

from flask_socketio import emit, join_room, leave_room, send
from app import socketio
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, db, RoomParticipants
import json
import re
from typing import List
from datetime import datetime, timedelta

@socketio.on('join')
@jwt_required()
def on_join():        
    userData = getUserData()
    room = userData.roomId  
    timeBank = getTimeBank(userData)
    clock = getClock(userData)

    join_room(room)
    emit('updateRoomId', {'data': room}, to=room)
    emit('updateClock', {'data': clock})
    emit('updateTimeBank', {'data': timeBank})

#NEED TO RETHINKING HOW THIS TIMEBANK/CLOCK IS STORED AND IN WHAT FORMAT. IS AN INTEGER REALLY THE SMARTEST IDEA?

@socketio.on('leave')
@jwt_required()
def on_leave():
    username = get_jwt_identity()
    user = db.session.query(User.id).filter_by(id=username).first()[0]
    room = RoomParticipants.query.filter_by(userId=user).first().roomId
    leave_room(room)
    print("disconnected fam")
    send(str(username) + ' has left the room.', to=room)

@socketio.on('updateClock')
@jwt_required()
def on_update(data):
    userData = getUserData()
    action = json.loads(data)
    if isinstance(action, int):
        userData.clock = userData.clock + timedelta(minutes=action)
    if re.match(r"[1-9•]{2}", action):
        diff_in_mins = getTimeDiff(action, userData.clock)
        userData.clock = userData.clock + timedelta(minutes=diff_in_mins)
    db.session.commit()
    clock = getClock(userData)
    emit('updateClock', {'data': clock})

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

    if re.match(r"[1-9•]{2}", action):
        diff_in_mins = getTimeDiff(action, userData.timeBank)
        userData.timeBank = userData.timeBank + timedelta(minutes=diff_in_mins)

    timeBank = getTimeBank(userData)
    clock = getClock(userData)
        
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

    return days+"•"+hours+"•"+minutes

def getClock(userData) -> datetime:
    return json.dumps(timeFormat(userData.clock), indent=4, sort_keys=True, default=str)

def getTimeBank(userData) -> datetime: 
    return json.dumps(timeFormat(userData.timeBank), indent=4, sort_keys=True, default=str)

def getTimeDiff(newTime: str, oldTime: datetime) -> int: 
    dhs = getDayHourSec(newTime)
    dhs = oldTime - newTime
    diff = dhs.total_seconds() / 60
    return diff

def getDayHourSec(time: str) -> datetime:
    ddhhmm = re.sub("[^0-9]", "", time)
    newTime = datetime.min
    newTime.day = str(ddhhmm)[:2] 
    newTime.hour = str(ddhhmm)[2:4] 
    newTime.minute = str(ddhhmm)[4:6]
    return newTime
