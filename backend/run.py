from app import createApp, socketio
from os import getenv

configName = getenv("FLASK_ENV")
app = createApp(configName)

if __name__ == "__main__":
    socketio.run(app)