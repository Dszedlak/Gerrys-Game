from app import createApp, socketio, db
from os import getenv
from app.websocket.game_session import GameSession

configName = getenv("FLASK_ENV")
app = createApp(configName)
app.app_context().push()

@app.before_first_request
def before_first_request_func():
    game = GameSession("roogy")
    game2 = GameSession("test")
    game.run()
    game2.run()
    print("cock")

if __name__ == "__main__":
    socketio.run(app)
    