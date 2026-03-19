"""
WebSocket endpoint — /live-transcript
Streams meeting-ready events from DynamoDB to connected frontend clients.
"""
import asyncio
import json
from typing import Dict

import boto3
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.core.config import get_settings

router = APIRouter(tags=["realtime"])
settings = get_settings()


class ConnectionManager:
    def __init__(self):
        # meeting_id -> list of connected websockets
        self.connections: Dict[str, list[WebSocket]] = {}

    async def connect(self, meeting_id: str, ws: WebSocket):
        await ws.accept()
        self.connections.setdefault(meeting_id, []).append(ws)

    def disconnect(self, meeting_id: str, ws: WebSocket):
        conns = self.connections.get(meeting_id, [])
        if ws in conns:
            conns.remove(ws)

    async def broadcast(self, meeting_id: str, message: dict):
        for ws in self.connections.get(meeting_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@router.websocket("/ws/meeting/{meeting_id}")
async def meeting_websocket(meeting_id: str, websocket: WebSocket):
    """
    Client connects here after uploading a meeting.
    Server polls DynamoDB for MEETING_READY event and pushes to client.
    """
    await manager.connect(meeting_id, websocket)
    dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
    table = dynamodb.Table(settings.DYNAMODB_TABLE)

    try:
        # Poll DynamoDB every 5s for up to 10 minutes
        for _ in range(120):
            resp = table.get_item(Key={"pk": f"meeting#{meeting_id}", "sk": f"event#"})
            # Query for MEETING_READY events
            query_resp = table.query(
                KeyConditionExpression="pk = :pk AND begins_with(sk, :sk)",
                ExpressionAttributeValues={
                    ":pk": f"meeting#{meeting_id}",
                    ":sk": "event#",
                },
                Limit=1,
                ScanIndexForward=False,
            )
            items = query_resp.get("Items", [])
            if items and items[0].get("type") == "MEETING_READY":
                await websocket.send_json({
                    "type": "MEETING_READY",
                    "meeting_id": meeting_id,
                    "message": "Meeting analysis complete. Refresh to view summary.",
                })
                break

            await websocket.send_json({"type": "PROCESSING", "meeting_id": meeting_id})
            await asyncio.sleep(5)
        else:
            await websocket.send_json({"type": "TIMEOUT", "meeting_id": meeting_id})

    except WebSocketDisconnect:
        manager.disconnect(meeting_id, websocket)
