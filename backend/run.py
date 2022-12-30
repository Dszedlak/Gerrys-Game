from app import createApp, socketio
from os import getenv

configName = getenv("FLASK_ENV")
app = createApp(configName)

@app.before_first_request
def before_first_request_func():
    with app.app_context():
        from app.websocket.game_session import GameSession

        game = GameSession("test")
        game.run()

        gametwo = GameSession("roogy")
        gametwo.run()

        print("YourMum")
        print("YourMum")    
        print("YourMum")

if __name__ == "__main__":
    print(app.before_first_request_funcs)
    socketio.run(app)