from app.models import Room, User, db, RoomParticipants, serialize_room
import json
from threading import Lock
from threading import Thread
from flask import copy_current_request_context

from app import socketio

thread_lock = Lock()


class GameSession:

    def __init__(self, roomname):
        self._room = db.session.query(Room.id).filter_by(name=roomname).first()[0]
        self._socketio = socketio
        self.thread = None

    def getRoom(self) -> int:
        return self._room

    def obj_dict(self):
        return self

    def closeRoom(self):
        self._room = 0
        self.thread = None

    def load_ready_partipants(self):
        players = []
        session_query = (
            db.session.query(RoomParticipants.userId).filter_by(roomId=self._room).all()
        )

        for participant in session_query:
            players.append(
                db.session.query(User.username).filter_by(id=participant[0]).first()[0]
            )
        jsonString = json.dumps(players)

        print(jsonString)
        return jsonString

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
            while self._room > 0:
                print(self.getRoom())
                participants = self.load_ready_partipants()
                self._socketio.emit(
                    "UpdateUserStatus", {"data": participants}, to=self._room
                )
                room_obj = Room.query.get(self._room)
                if room_obj:
                    self._socketio.emit("room_state", serialize_room(room_obj), to=room_obj.id)
                self._socketio.sleep(1)
            if self._room == 0:
                return
