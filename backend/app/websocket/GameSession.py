from app.models import Room, User, db
from flask_socketio import emit
from app import socketio
from flask_jwt_extended import jwt_required, get_jwt_identity
from threading import Lock
import json

thread = None
thread_lock = Lock()

@jwt_required()
@socketio.on('connect')
def on_connect():

    global thread
    print('Client connected')

    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread())
            
@jwt_required()
def background_thread():
    print("cock!")
    while True:
        current_user = get_jwt_identity()
        participants = load_ready_partipants(current_user)
        emit('UpdateUserStatus', {'data':participants}, broadcast=True)
        socketio.sleep(1)

def obj_dict(obj):
    return obj  

def load_ready_partipants(session_id):
    players=[]
    session_query = Room.query.filter_by(id=session_id).first()

    for participant in session_query.participants:
        players.append(db.session.query(User.username).filter_by(id=participant.userId).first()[0])
        #tmp = {"User": db.session.query(User.username).filter_by(id=participant.userId).first()[0], "Job": participant.job}
    jsonString = json.dumps(players)
        
    print(jsonString)    

    return jsonString
    #return json.dumps(participant, default=obj_dict)