import json

from channels.generic.websocket import AsyncWebsocketConsumer


class TicketConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope.get("user")

        if not user:
            await self.close(code=4001)
            return

        await self.accept()

        await self.send(text_data=json.dumps({
            "message": "Connected to SmartDesk",
            "user": user.username,
        }))

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)

        await self.send(text_data=json.dumps({
            "message": "Message received",
            "data": data
        }))