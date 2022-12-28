from app.models import db
from .game_session import GameSession

from flask_socketio import emit, join_room, leave_room, send
from app import socketio
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Room, User, db, RoomParticipants

#For Every room in rooms, open up a seperate thread.

@socketio.on('join')
@jwt_required()
def on_join():
    username = get_jwt_identity()
    user = db.session.query(User.id).filter_by(id=username).first()[0]
    room = RoomParticipants.query.filter_by(userId=user).first().roomId
    join_room(room)

    game = GameSession("test")
    gametwo = GameSession("roogy")
    game.run()
    gametwo.run()
    
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

