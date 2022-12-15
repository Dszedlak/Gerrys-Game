from app.models import db
from .game_session import GameSession

from flask_socketio import emit, join_room, leave_room, send
from app import socketio
from flask_jwt_extended import jwt_required, get_jwt_identity
from threading import Lock

thread = None
thread_lock = Lock()
game_session = GameSession()

class Polling:
    def __init__(self):
        self.is_polling = False
    
    def poll(self):
        self.is_polling = True
    
    def stop(self):
        self.is_polling = False

polling = Polling()

#For Every room in rooms, open up a seperate thread.

@socketio.on('join')
@jwt_required()
def on_join():
    username = get_jwt_identity()
    room = game_session.get_room_id(username)
    join_room(room)
    polling.poll()
    
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread(polling))

    print(polling.is_polling)

@socketio.on('connect')
@jwt_required()
def on_connect():
    print("Client Connected")

@socketio.on('disconnect')
def disconnect():
    print("Client Disconnected")

@socketio.on('leave')
@jwt_required()
def on_leave():
    username = get_jwt_identity()
    room = game_session.get_room_id(username)
    leave_room(room)
    print("disconnected fam")
    polling.stop()
    send(str(username) + ' has left the room.', to=room)

@jwt_required()
def background_thread(polling: Polling):
    while True:
        if polling.is_polling:
            current_user = get_jwt_identity()
            participants = game_session.load_ready_partipants(current_user)
            emit('UpdateUserStatus', {'data':participants}, to=game_session.getRoom())
            socketio.sleep(1)
        else:
            current_user = get_jwt_identity()
            participants = game_session.load_ready_partipants(current_user)
            emit('UpdateUserStatus', {'data':participants}, to=game_session.getRoom())
            socketio.sleep(5)
