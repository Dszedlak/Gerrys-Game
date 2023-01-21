from app.models import Room, User, db, RoomParticipants
import json
from threading import Lock
from threading import Thread
import time
from flask_socketio import emit, join_room, leave_room, send
from flask import copy_current_request_context

from flask_jwt_extended import jwt_required, get_jwt_identity
from app import socketio
from flask import current_app as app

thread_lock = Lock()

class GameSession():

    def __init__(self, roomname):
        self._room = db.session.query(Room.id).filter_by(name=roomname).first()[0]
        self._socketio = socketio
        self.thread = None


    def getRoom(self) -> int:
        return self._room
        
    def obj_dict(self):
        return self

    def load_ready_partipants(self):
        players=[]
        session_query = db.session.query(RoomParticipants.userId).filter_by(roomId=self._room).all()

        for participant in session_query:
            players.append(db.session.query(User.username).filter_by(id=participant[0]).first()[0])
            #tmp = {"User": db.session.query(User.username).filter_by(id=participant.userId).first()[0], "Job": participant.job}
        jsonString = json.dumps(players)
            
        print(jsonString)

        return jsonString
        #return json.dumps(participant, default=obj_dict)

    def run(self):
        with thread_lock:
            if self.thread is None:
                @copy_current_request_context
                def start():
                    self.background_thread()
                self.thread = Thread(target=start)
                self.thread.daemon = True
                self.thread.start()

    def background_thread(self):
        while True:
            participants = self.load_ready_partipants()
            self._socketio.emit('UpdateUserStatus', {'data':participants}, to=self._room)
            self._socketio.sleep(1)
            
