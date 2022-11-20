import re
from app.models import Room, RoomState, User, db, RoomParticipants
from flask import request
from flask_socketio import Namespace, emit
from flask_jwt_extended import jwt_required, get_jwt_identity
import json

class QuizNamespace(Namespace):
    @jwt_required()
    def on_connect(self):
        current_user = get_jwt_identity()
        participants = load_ready_partipants(current_user)
    
        emit('UpdateUserStatus', {'data':participants}, broadcast=True)
        pass

    @jwt_required()
    def on_oof(self, data):
        print(data)
        pass

    @jwt_required()
    def on_disconnect(self):
        pass

    @jwt_required()
    def on_join_session_request(self, data):
        #Someone has joined the session
        pass

    @jwt_required()
    def on_start_session_request(self, data):
        #Quiz master wants to start the session
        pass

    @jwt_required()
    def on_end_session_request(self, data):
        #Quiz master wants to end the session
        pass

    @jwt_required() 
    def on_next_question_request(self, data):
        #Quiz master wants to start the next question
        pass

    @jwt_required()
    def on_end_question_request(self, data):
        #Quiz master wants to end the answering period for this question
        pass

def load_ready_partipants(session_id):
    ready_users_id=[]
    ready_users=[]
    session_query = Room.query.filter_by(id=session_id).first()
    participants = session_query.participants

    for participants in session_query.participants:
        if participants.isReady == True:
            ready_users_id.append(participants.userId)
    
    for user_id in ready_users_id:
        tmp = db.session.query(User.username).filter_by(id=user_id).first()
        ready_users.append(tmp[0])
    
    return json.dumps(ready_users)