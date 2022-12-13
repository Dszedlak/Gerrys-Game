from app.models import RoomParticipants, User, db
from .game_session import GameSession

from flask_socketio import emit, join_room, leave_room, send
from app import socketio
from flask_jwt_extended import jwt_required, get_jwt_identity
from threading import Lock
import json

thread = None
thread_lock = Lock()
game_session = GameSession()

@socketio.on('join')
@jwt_required()
def on_join():
    username = get_jwt_identity()
    room = game_session.get_room_id(username)
    join_room(room)

    global thread
    print("Successfully joined room: " +  str(game_session._room))

    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread())

@socketio.on('connect')
@jwt_required()
def on_connect():
    print("Client Connected")

@socketio.on('leave')
@jwt_required()
def on_leave():
    username = get_jwt_identity()
    room = game_session.get_room_id(username)
    leave_room(room)
    send(str(username) + ' has left the room.', to=room)  
            
@jwt_required()
def background_thread():
    print("cock!")
    while True:
        current_user = get_jwt_identity()
        participants = game_session.load_ready_partipants(current_user)
        emit('UpdateUserStatus', {'data':participants}, to=game_session.getRoom())
        socketio.sleep(2)