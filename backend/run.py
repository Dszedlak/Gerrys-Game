from app import createApp, socketio
from os import getenv
from app.websocket.game_session import GameSession

configName = getenv("FLASK_ENV")
app = createApp(configName)

@app.before_first_request
def before_first_request_func():
    with app.app_context():
        game = GameSession("test")
        game.run()
        print("cock")
        
if __name__ == "__main__":
    socketio.run(app)