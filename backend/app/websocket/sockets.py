from app.models import db

from flask_socketio import emit, join_room, leave_room, send
from app import socketio
from flask_jwt_extended import jwt_required, get_jwt_identity, current_user
from app.models import User, db, RoomParticipants
import json
from flask import current_app as app
#For Every room in rooms, open up a seperate thread.

@socketio.on('join')
@jwt_required()
def on_join():        
    username = get_jwt_identity()
    user = db.session.query(User.id).filter_by(id=username).first()[0]
    room = RoomParticipants.query.filter_by(userId=user).first().roomId
    userData = RoomParticipants.query.filter_by(userId=user).first()
    
    timeBank = json.dumps(userData.timeBank, indent=4, sort_keys=True, default=str)
    clock = json.dumps(userData.clock, indent=4, sort_keys=True, default=str)
    print("Timebank: " + str(userData.timeBank)[8:])
    print("Clock: " + clock)
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
    print("timebank == OOF!!")

@socketio.on('updateTimeBank')
@jwt_required()
def on_update(data):
    print("Clock == COCK!!")

@socketio.on('connect')
@jwt_required()
def on_connect():
    print("Client Connected")

@socketio.on('disconnect')
def disconnect():
    print("Client Disconnected")

