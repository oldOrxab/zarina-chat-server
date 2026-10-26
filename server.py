import os
import secrets
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()
rooms = {}

@app.get("/")
async def home():
    return {"status": "Zarina Chat server is running"}

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/new-code")
async def new_code():
    return {"code": secrets.token_hex(3).upper()}

@app.websocket("/ws/{room}")
async def chat(websocket: WebSocket, room: str):
    await websocket.accept()
    rooms.setdefault(room, set()).add(websocket)
    try:
        while True:
            message = await websocket.receive_text()
            for client in list(rooms.get(room, set())):
                if client != websocket:
                    await client.send_text(message)
    except WebSocketDisconnect:
        rooms.get(room, set()).discard(websocket)
