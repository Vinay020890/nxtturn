# community/consumers.py

import json
from urllib.parse import parse_qs
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from rest_framework.authtoken.models import Token

def get_user_from_token(token_key):
    try:
        token = Token.objects.get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return None

class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        query_string = self.scope['query_string'].decode('utf-8')
        query_params = parse_qs(query_string)
        token_key = query_params.get('token', [None])[0]

        if token_key is None:
            self.close()
            return

        user = get_user_from_token(token_key)
        
        if user is None:
            self.close()
            return

        self.scope['user'] = user
        self.room_group_name = f'notifications_{user.id}'
        
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name,
                self.channel_name
            )

    def send_notification(self, event):
        message = event['message']
        self.send(text_data=json.dumps({
            'type': 'notification',
            'message': message
        }))