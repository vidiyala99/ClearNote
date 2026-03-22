import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # Maps user_id (str) -> list of connected WebSockets
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_text(json.dumps(message))

    async def broadcast_to_user(self, user_id: str, message: dict):
        """
        Send a notification payload to all active sockets belonging to a single user.
        """
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception:
                    pass

    async def listen_to_redis(self):
        """
        Listen to Redis pubsub and broadcast payloads to local connected clients.
        """
        import redis.asyncio as aioredis

        from app.config import settings
        
        try:
            r = aioredis.from_url(settings.redis_url)
            pubsub = r.pubsub()
            await pubsub.subscribe("notifications")
            
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message:
                    try:
                        data = json.loads(message["data"])
                        user_id = data.get("user_id")
                        if user_id:
                            await self.broadcast_to_user(user_id, data)
                    except Exception:
                        pass
                import asyncio
                await asyncio.sleep(0.1) # Cooloff loop
        except Exception:
             pass

manager = ConnectionManager()

@router.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket, user_id: str = Query(...)):
    """
    WebSocket endpoint for real-time job updates.
    Connection URL: ws://localhost:8000/api/v1/ws/notifications?user_id={user_id}
    """
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Continuous listening to keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
