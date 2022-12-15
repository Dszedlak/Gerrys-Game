from app.models import Room, User, db, RoomParticipants
import json

class GameSession:
    
    def __init__(self, isPolling = None):
        self._isPolling = isPolling

    def getIsPolling(self) -> bool:
        return self._isPolling

    def setIsPolling(self, isPolling: bool):
        self._isPolling = isPolling

    def __init__(self, room = None):
        self._room = room

    def getRoom(self) -> int:
        return self._room
        
    def obj_dict(self):
        return self

    def get_room_id(self, username) -> int:
        user = db.session.query(User.id).filter_by(id=username).first()[0]
        self._room = RoomParticipants.query.filter_by(userId=user).first().roomId
        return self._room

    def load_ready_partipants(self, session_id):
        players=[]
        session_query = db.session.query(RoomParticipants.userId).filter_by(roomId=self.get_room_id(session_id)).all()

        for participant in session_query:
            players.append(db.session.query(User.username).filter_by(id=participant[0]).first()[0])
            #tmp = {"User": db.session.query(User.username).filter_by(id=participant.userId).first()[0], "Job": participant.job}
        jsonString = json.dumps(players)
            
        print(jsonString)    

        return jsonString
        #return json.dumps(participant, default=obj_dict)