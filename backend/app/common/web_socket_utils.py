import asyncio
from fastapi import WebSocket
from collections import defaultdict


class WebSocketManager:
    def __init__(self):
        self.active_connections = defaultdict(set)

    async def connect(self, websocket: WebSocket, channel_id: str):
        await websocket.accept()
        self.active_connections[channel_id].add(websocket)

    def disconnect(self, websocket: WebSocket, channel_id: str):
        self.active_connections[channel_id].remove(websocket)
        if not self.active_connections[channel_id]:
            del self.active_connections[channel_id]

    async def broadcast(self, message: dict, channel_id: str):
        if channel_id in self.active_connections:
            await asyncio.gather(
                *[connection.send_json(message) for connection in self.active_connections[channel_id]]
            )


websocket_manager = WebSocketManager()
