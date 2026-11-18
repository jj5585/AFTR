import asyncio
import json
import uuid
import logging
from typing import Dict, Set, Optional
from fastapi import WebSocket

logger = logging.getLogger("aftr.realtime")


class ConnectionManager:
    def __init__(self):
        # Map conversation_id -> set of active WebSockets
        self._conversations: Dict[uuid.UUID, Set[WebSocket]] = {}
        # Map websocket -> persona_id
        self._socket_personas: Dict[WebSocket, uuid.UUID] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, conversation_id: uuid.UUID, persona_id: uuid.UUID):
        await websocket.accept()
        async with self._lock:
            if conversation_id not in self._conversations:
                self._conversations[conversation_id] = set()
            self._conversations[conversation_id].add(websocket)
            self._socket_personas[websocket] = persona_id

    async def disconnect(self, websocket: WebSocket, conversation_id: uuid.UUID):
        async with self._lock:
            if conversation_id in self._conversations:
                self._conversations[conversation_id].discard(websocket)
                if not self._conversations[conversation_id]:
                    del self._conversations[conversation_id]
            self._socket_personas.pop(websocket, None)

    async def broadcast_to_conversation(
        self,
        conversation_id: uuid.UUID,
        payload: dict,
        exclude_socket: Optional[WebSocket] = None,
    ):
        """
        Broadcast message dictionary to all active sockets connected to conversation_id.
        Notice: Content is NOT logged here.
        """
        async with self._lock:
            sockets = list(self._conversations.get(conversation_id, set()))

        dead_sockets = []
        for socket in sockets:
            if exclude_socket and socket == exclude_socket:
                continue
            try:
                await socket.send_json(payload)
            except Exception:
                dead_sockets.append(socket)

        if dead_sockets:
            async with self._lock:
                for socket in dead_sockets:
                    if conversation_id in self._conversations:
                        self._conversations[conversation_id].discard(socket)
                    self._socket_personas.pop(socket, None)

    def is_persona_online(self, conversation_id: uuid.UUID, persona_id: uuid.UUID) -> bool:
        """Check if a specific persona is currently connected to the conversation."""
        sockets = self._conversations.get(conversation_id, set())
        for s in sockets:
            if self._socket_personas.get(s) == persona_id:
                return True
        return False


# Global singleton instance
ws_manager = ConnectionManager()
