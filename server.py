import secrets
import time
from collections import defaultdict
from threading import Lock
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
from zoneinfo import ZoneInfo

app = FastAPI(title="Zarina Chat Server")
_lock = Lock()
_users = {}       # code -> token
_connections = {} # code -> peer code
_messages = defaultdict(list)
_counter = 0

class RegisterBody(BaseModel):
    pass

class ConnectBody(BaseModel):
    code: str
    token: str
    peer_code: str

class SendBody(BaseModel):
    code: str
    token: str
    peer_code: str
    text: str

@app.get("/")
def home():
    return {"status": "Zarina Chat server is running"}

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/register")
def register(_body: dict = {}):
    code = secrets.token_hex(3).upper()
    token = secrets.token_urlsafe(24)
    with _lock:
        _users[code] = token
        _messages[code] = []
    return {"code": code, "token": token}

def _auth(code: str, token: str):
    if not code or not token or _users.get(code) != token:
        raise HTTPException(status_code=401, detail="Kod və ya təhlükəsizlik tokeni yanlışdır.")

@app.post("/connect")
def connect(body: ConnectBody):
    with _lock:
        _auth(body.code, body.token)
        peer = body.peer_code.strip().upper()
        if peer not in _users:
            raise HTTPException(status_code=404, detail="Qarşı tərəfin kodu tapılmadı. O, əvvəlcə Zarina çatını açmalıdır.")
        _connections[body.code] = peer
        _connections[peer] = body.code
    return {"ok": True, "peer_code": peer}

@app.post("/send")
def send(body: SendBody):
    global _counter
    text = body.text.strip()
    with _lock:
        _auth(body.code, body.token)
        peer = body.peer_code.strip().upper()
        if not text:
            raise HTTPException(status_code=400, detail="Mesaj boşdur.")
        if peer not in _users:
            raise HTTPException(status_code=404, detail="Qarşı tərəfin kodu tapılmadı. O, əvvəlcə Zarina çatını açmalıdır.")
        _counter += 1
        stamp = datetime.now(ZoneInfo("Asia/Baku")).strftime("%H:%M")
        msg = {"id": str(_counter), "from_code": body.code, "to_code": peer, "text": text, "time": stamp}
        _messages[peer].append(msg)
        _messages[body.code].append(msg)
    return {"ok": True, "id": msg["id"]}

@app.get("/messages")
def messages(code: str = Query(...), token: str = Query(...)):
    with _lock:
        _auth(code, token)
        msgs = list(_messages.get(code, []))
    return {"messages": msgs[-300:]}
