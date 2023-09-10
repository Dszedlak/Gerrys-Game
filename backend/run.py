from app import createApp, socketio, db
from os import getenv
from app.websocket.game_session import GameSession

configName = "production"
app = createApp(configName)
app.app_context().push()

# @app.before_first_request
# def before_first_request_func():
#     t = GameSession("roogy")
#     t.run()
#     print("test game sessions running.")
#     e = GameSession("test")
#     e.run()

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000)
    