import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Room, Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        
        # Check if room exists
        if not await self.get_room():
            await self.close()
            return
            
        self.room_group_name = f'chat_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        username = text_data_json['username']

        # Save message and get the message object
        message_obj = await self.save_message(username, message)
        if not message_obj:
            return

        # Send initial message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
                'message_id': message_obj.id,
                'timestamp': message_obj.created_at.isoformat(),
            }
        )

        # Start moderation in background
        from .tasks import moderate_message_content
        result = moderate_message_content.delay(message_obj.id)
        
        # Wait for moderation result (with timeout)
        try:
            moderation_result = result.get(timeout=2)  # 2 second timeout
            if moderation_result.get('is_flagged', False):
                # Send moderation result to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'moderation_update',
                        'message_id': message_obj.id,
                        'status': 'flagged',
                        'notes': moderation_result.get('notes', {})
                    }
                )
        except Exception as e:
            print(f'Error getting moderation result: {e}')

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'username': event['username'],
            'message_id': event['message_id'],
            'timestamp': event['timestamp']
        }))

    async def moderation_update(self, event):
        # Send moderation update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'moderation',
            'message_id': event['message_id'],
            'status': event['status'],
            'notes': event['notes']
        }))

    @database_sync_to_async
    def get_room(self):
        """Get room by name or slugified name"""
        from django.utils.text import slugify
        try:
            # Try exact name match first
            return Room.objects.get(name=self.room_name)
        except Room.DoesNotExist:
            try:
                # Try to find by slugified name
                rooms = Room.objects.all()
                return next((r for r in rooms if slugify(r.name) == self.room_name), None)
            except Exception:
                return None

    @database_sync_to_async
    def save_message(self, username, message):
        try:
            user = User.objects.get(username=username)
            room = self._get_room_sync()
            if not room:
                raise Room.DoesNotExist(f'Room {self.room_name} not found')
                
            message_obj = Message.objects.create(user=user, room=room, content=message)
            
            return message_obj
        except Exception as e:
            print(f'Error saving message: {e}')
            return None
            
    def _get_room_sync(self):
        """Synchronous version of get_room"""
        from django.utils.text import slugify
        try:
            # Try exact name match first
            return Room.objects.get(name=self.room_name)
        except Room.DoesNotExist:
            try:
                # Try to find by slugified name
                rooms = Room.objects.all()
                return next((r for r in rooms if slugify(r.name) == self.room_name), None)
            except Exception:
                return None
