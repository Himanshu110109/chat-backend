import socketio
from models import rooms
from utils import generate_password, sanitize_message
from datetime import datetime
import pytz

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

def get_timestamp():
    ist = pytz.timezone("Asia/Kolkata")
    return datetime.now(ist).strftime("%I:%M %p")

@sio.event
async def connect(sid, environ):
    print(f"User connected: {sid}")
    await sio.emit("connected", {"sid": sid}, to=sid)

@sio.event
async def create_room(sid, data):
    room_name = data["room"]
    username = data["username"]
    print(room_name, username)
    password = data["password"]

    if room_name in rooms:
        await sio.emit("error",{
            "error": "Room already exists"
        }, to=sid)
        return

    if not password:
        password = generate_password()

    rooms[room_name] = {
        "password": password,
        "users": {
            sid: {
                "username": username,
                "is_owner": True
            }
        },
        "messages": []
    }

    await sio.enter_room(sid, room_name)

    await sio.emit("room_created", {
        "room": room_name,
        "password": password
    }, to=sid)

    await sio.emit("users_update", {
        "users": [
            {
                "username": u["username"],
                "is_owner": u["is_owner"]
            }
            for u in rooms[room_name]["users"].values()
        ]
    }, room=room_name)

    print("room created")

@sio.event
async def get_users(sid, data):
    room = data["room"]

    if room in rooms:
        await sio.emit("users_update", {
            "users": [
                {
                    "username": u["username"],
                    "is_owner": u["is_owner"]
                }
                for u in rooms[room]["users"].values()
            ]
        }, to=sid)

@sio.event
async def join_room(sid, data):
    room = data["room"]
    password = data["password"]
    username = data["username"]

    if room not in rooms:
        await sio.emit("error", {"msg": "Room not found"}, to=sid)
        return

    if rooms[room]["password"] != password:
        await sio.emit("error", {"msg": "Wrong password"}, to=sid)
        return

    rooms[room]["users"][sid] = {
        "username": username,
        "is_owner": False
    }

    await sio.enter_room(sid, room)

    await sio.emit("room_joined", {"room": room}, to=sid)

    await sio.emit("user_joined", {
        "username": username
    }, room=room)

    await sio.emit("users_update", {
        "users": [
            {
                "username": u["username"],
                "is_owner": u["is_owner"]
            }
            for u in rooms[room]["users"].values()
        ]
    }, room=room)

    print("joined the room")

@sio.event
async def send_message(sid, data):
    room = data["room"]
    message = sanitize_message(data["message"])

    user = rooms[room]["users"][sid]["username"]

    msg_obj = {
        "user": user,
        "text": message,
        "time": get_timestamp(),
        "is_owner": rooms[room]["users"][sid]["is_owner"],
    }

    rooms[room]["messages"].append(msg_obj)

    # Keep only last 100
    if len(rooms[room]["messages"]) > 100:
        rooms[room]["messages"].pop(0)

    await sio.emit("new_message", msg_obj, room=room)

@sio.event
async def disconnect(sid):
    print(f"Disconnected: {sid}")

    for room in list(rooms.keys()):
        if sid in rooms[room]["users"]:
            username = rooms[room]["users"][sid]["username"]

            del rooms[room]["users"][sid]

            await sio.emit("user_left", {"username": username}, room=room)

            await sio.emit("users_update", {
                "users": [
                    {
                        "username": u["username"],
                        "is_owner": u["is_owner"]
                    }
                    for u in rooms[room]["users"].values()
                ]
            }, room=room)
            # delete room if empty
            if not rooms[room]["users"]:
                del rooms[room]

            break

@sio.event
async def typing_start(sid, data):
    room = data["room"]
    username = data["username"]

    await sio.emit("typing_indicator", {
        "username": username,
        "typing": True
    }, room=room, skip_sid=sid)

@sio.event
async def typing_stop(sid, data):
    room = data["room"]
    username = data["username"]

    await sio.emit("typing_indicator", {
        "username": username,
        "typing": False
    }, room=room, skip_sid=sid)
