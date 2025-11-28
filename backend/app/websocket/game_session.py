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
        print(f"[GameSession] Initialized for room {roomname} (ID: {self._room})")

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
                print(f"[GameSession] Background thread started for room {self._room}")

    def background_thread(self):
        snapshot_counter = 0  # Track iterations for periodic snapshots
        while True:
            while self._room > 0:
                print(self.getRoom())
                room_obj = Room.query.get(self._room)
                if room_obj:
                    # Save clock snapshots every 5 seconds (every 5 iterations)
                    snapshot_counter += 1
                    if snapshot_counter >= 5:
                        snapshot_counter = 0
                        self._save_clock_snapshots(room_obj)
                
                self._socketio.sleep(1)
            if self._room == 0:
                return

    def _save_clock_snapshots(self, room):
        """Save current clock values for all participants to history"""
        from app.models import ClockHistory
        try:
            snapshot_count = 0
            for participant in room.participants:
                snapshot = ClockHistory(
                    room_id=room.id,
                    user_id=participant.userId,
                    clock_value=participant.clock
                )
                db.session.add(snapshot)
                snapshot_count += 1
            db.session.commit()
            print(f"[ClockHistory] Saved {snapshot_count} snapshots for room {room.id}")
        except Exception as e:
            print(f"[ClockHistory] Error saving snapshots: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
