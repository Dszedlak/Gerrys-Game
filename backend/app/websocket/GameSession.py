import re
import threading
from app.models import Room, User, db
from flask import request
from flask_socketio import Namespace, emit
from flask_jwt_extended import jwt_required, get_jwt_identity
import json

class GameNamespace(Namespace):

    @jwt_required()
    def on_connect(self):
        current_user = get_jwt_identity()
        participants = load_ready_partipants(current_user)
    
        sleep(10)
        emit('UpdateUserStatus', {'data':participants}, broadcast=True)
        pass

    @jwt_required()
    def on_oof(self, data):
        print(data)
        pass
    
    @jwt_required()
    def update_users(self):
        print("I HATE POO!!!!")
        current_user = get_jwt_identity()
        participants = load_ready_partipants(current_user)
        emit('UpdateUserStatus', {'data':participants}, broadcast=True)
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

    def ping_in_intervals(self):
        while True:
            sleep(1)

        

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

    