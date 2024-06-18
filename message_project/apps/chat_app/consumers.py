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







# videocall/consumers.py
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

class CallConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.my_name = self.scope['user'].username  # Assuming user is authenticated and username is available
        async_to_sync(self.channel_layer.group_add)(
            self.my_name,
            self.channel_name
        )
        self.send(text_data=json.dumps({
            'type': 'connection',
            'data': {
                'message': "Connected"
            }
        }))

    def disconnect(self, close_code):
        if hasattr(self, 'my_name'):
            async_to_sync(self.channel_layer.group_discard)(
                self.my_name,
                self.channel_name
            )

    def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            event_type = text_data_json.get('type')
            data = text_data_json.get('data', {})

            if event_type == 'call':
                name = data.get('name')
                rtc_message = data.get('rtcMessage')
                if name and rtc_message:
                    async_to_sync(self.channel_layer.group_send)(
                        name,
                        {
                            'type': 'call_received',
                            'data': {
                                'caller': self.my_name,
                                'rtcMessage': rtc_message
                            }
                        }
                    )
                else:
                    self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Invalid call data'
                    }))

            elif event_type == 'answer_call':
                caller = data.get('caller')
                rtc_message = data.get('rtcMessage')
                if caller and rtc_message:
                    async_to_sync(self.channel_layer.group_send)(
                        caller,
                        {
                            'type': 'call_answered',
                            'data': {
                                'rtcMessage': rtc_message
                            }
                        }
                    )
                else:
                    self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Invalid answer call data'
                    }))

            elif event_type == 'ICEcandidate':
                user = data.get('user')
                rtc_message = data.get('rtcMessage')
                if user and rtc_message:
                    async_to_sync(self.channel_layer.group_send)(
                        user,
                        {
                            'type': 'ICEcandidate',
                            'data': {
                                'rtcMessage': rtc_message
                            }
                        }
                    )
                else:
                    self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Invalid ICE candidate data'
                    }))

            elif event_type == 'end_call':
                user = data.get('user')
                if user:
                    async_to_sync(self.channel_layer.group_send)(
                        user,
                        {
                            'type': 'call_ended'
                        }
                    )
                else:
                    self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'User not provided for ending call'
                    }))

            else:
                self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Unknown event type'
                }))

        except json.JSONDecodeError:
            self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON received'
            }))
        except KeyError as e:
            self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Missing key: {str(e)}'
            }))
        except Exception as e:
            self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error: {str(e)}'
            }))

    def call_received(self, event):
        self.send(text_data=json.dumps({
            'type': 'call_received',
            'data': event['data']
        }))

    def call_answered(self, event):
        self.send(text_data=json.dumps({
            'type': 'call_answered',
            'data': event['data']
        }))

    def ICEcandidate(self, event):
        self.send(text_data=json.dumps({
            'type': 'ICEcandidate',
            'data': event['data']
        }))

    def call_ended(self, event):
        self.send(text_data=json.dumps({
            'type': 'call_ended'
        }))
