from app.models import db

from flask_socketio import emit, join_room, leave_room, send
from app import socketio
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, db, RoomParticipants
import json
from datetime import datetime, timedelta
from flask import current_app as app

@socketio.on('join')
@jwt_required()
def on_join():        
    username = get_jwt_identity()
    user = db.session.query(User.id).filter_by(id=username).first()[0]
    userData = RoomParticipants.query.filter_by(userId=user).first()
    room = userData.roomId
    
    timeBank = json.dumps(timeFormat(userData.timeBank), indent=4, sort_keys=True, default=str)
    clock = json.dumps(timeFormat(userData.clock), indent=4, sort_keys=True, default=str)

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
    if action.isnumeric():
        userData.clock = userData.clock + timedelta(minutes=action)
        db.session.commit()

@socketio.on('updateTimeBank')
@jwt_required()
def on_update(data):
    userData = getUserData()
    action = json.loads(data)
    if action.isnumeric():
        userData.timeBank = userData.timeBank + timedelta(minutes=data)
    if action == "clear" or action == "cashout":
        if action == "cashout":
            userData.clock + userData.timeBank
        userData.timeBank = datetime.min
    db.session.commit()

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
    
    