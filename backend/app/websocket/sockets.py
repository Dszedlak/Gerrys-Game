from app.models import db

from flask_socketio import emit, join_room, leave_room, send
from app import socketio
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, db, RoomParticipants

from flask import current_app as app
#For Every room in rooms, open up a seperate thread.

@socketio.on('join')
@jwt_required()
def on_join():        
    username = get_jwt_identity()
    user = db.session.query(User.id).filter_by(id=username).first()[0]
    room = RoomParticipants.query.filter_by(userId=user).first().roomId
    print(room)
    join_room(room)
    
    emit('updateRoomId', {'data': room}, to=room)

@socketio.on('leave')
@jwt_required()
def on_leave():
    username = get_jwt_identity()
    user = db.session.query(User.id).filter_by(id=username).first()[0]
    room = RoomParticipants.query.filter_by(userId=user).first().roomId
    leave_room(room)
    print("disconnected fam")
    send(str(username) + ' has left the room.', to=room)

@socketio.on('connect')
@jwt_required()
def on_connect():
    print("Client Connected")

@socketio.on('disconnect')
def disconnect():
    print("Client Disconnected")

