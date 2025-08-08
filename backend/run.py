import eventlet
eventlet.monkey_patch()

from app import createApp, socketio

configName = "production"
app = createApp(configName)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)