from fastapi import FastAPI
from socket_manager import sio
import socketio

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Server running 🚀"}

app = socketio.ASGIApp(sio, other_asgi_app=app)
