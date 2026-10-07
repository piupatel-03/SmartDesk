import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone


class TicketConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope.get("user")

        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.user = user

        role = await self.get_user_role(user)

        if role == "Manager":
            self.group_name = "managers"

        elif role == "Agent":
            self.group_name = f"agent_{user.id}"

        else:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        await self.accept()

        await self.send(
            text_data=json.dumps({
                "event": "connected",
                "data": {
                    "message": "Connected to SmartDesk notifications"
                },
                "timestamp": timezone.now().isoformat(),
            })
        )

    @database_sync_to_async
    def get_user_role(self, user):
        if user.groups.filter(name="Manager").exists():
            return "Manager"

        if user.groups.filter(name="Agent").exists():
            return "Agent"

        return None

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        if data.get("action") == "ping":
            await self.send(
                text_data=json.dumps({
                    "event": "pong",
                    "timestamp": timezone.now().isoformat(),
                })
            )

    async def ticket_event(self, event):
        await self.send(
            text_data=json.dumps({
                "event": event["event"],
                "ticket_id": event["ticket_id"],
                "data": event.get("data", {}),
                "timestamp": event.get(
                    "timestamp",
                    timezone.now().isoformat(),
                ),
            })
        )