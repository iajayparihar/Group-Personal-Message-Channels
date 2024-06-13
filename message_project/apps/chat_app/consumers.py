import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from chat_app.models import Group, GroupMessage, PersonalMessage
from django.contrib.auth.models import User

class ChatConsumerMixin:
    async def connect(self):
        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        sender_username = data.get('username', self.scope['user'].username)
        await self.save_message(sender_username, message)
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender_username
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender']
        }))

class GroupChatConsumer(ChatConsumerMixin, AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = self.scope['url_route']['kwargs']['group_name']
        self.room_name = f'group_{self.group_name}'
        await super().connect()

    @database_sync_to_async
    def save_message(self, sender_username, message):
        user = User.objects.select_related().get(username=sender_username)
        group = Group.objects.prefetch_related('members').get(name=self.group_name)
        GroupMessage.objects.create(sender=user, group=group, content=message)

class PersonalChatConsumer(ChatConsumerMixin, AsyncWebsocketConsumer):
    async def connect(self):
        from channels.auth import get_user
        self.user = await get_user(self.scope)
        self.friend_username = self.scope['url_route']['kwargs']['friend_username']

        # Sort usernames to ensure a consistent room name
        usernames = sorted([self.user.username, self.friend_username])
        self.room_name = f'personal_{usernames[0]}_{usernames[1]}'
        
        await super().connect()

    @database_sync_to_async
    def save_message(self, sender_username, message):
        sender = User.objects.select_related().get(username=sender_username)
        receiver = User.objects.select_related().get(username=self.friend_username)
        PersonalMessage.objects.create(sender=sender, receiver=receiver, content=message)
