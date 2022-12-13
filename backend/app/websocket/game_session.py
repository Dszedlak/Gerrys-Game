from app.models import Room, User, db, RoomParticipants
import json

class GameSession:
    
    def __init__(self, room = None):
        self._room = room

    def getRoom(self) -> int:
        return self._room
        
    def obj_dict(self):
        return self

    def get_room_id(self, username) -> int:
        user = db.session.query(User.id).filter_by(id=username).first()[0]
        self._room = RoomParticipants.query.filter_by(userId=user).first().roomId
        print(self._room)
        return self._room

    def load_ready_partipants(self, session_id):
        players=[]
        session_query = Room.query.filter_by(id=session_id).first()

        for participant in session_query.participants:
            players.append(db.session.query(User.username).filter_by(id=participant.userId).first()[0])
            #tmp = {"User": db.session.query(User.username).filter_by(id=participant.userId).first()[0], "Job": participant.job}
        jsonString = json.dumps(players)
            
        print(jsonString)    

        return jsonString
        #return json.dumps(participant, default=obj_dict)