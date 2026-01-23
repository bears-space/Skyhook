from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)

# warning: this is unsafe if we ever expose the site
# to anyone other than us
app.config["SECRET_KEY"] = "secret"
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on("connect")
def handle_connect():
    print("Client connected")
    emit("message", {"data": "Connected to backend"})

@socketio.on("ping")
def handle_ping(data):
    emit("pong", {"data": data})

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)

