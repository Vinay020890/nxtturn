# community/consumers.py --- SUPER DEBUG VERSION

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
        print("\nCONSUMER-DEBUG: New connection attempt.")
        query_string = self.scope['query_string'].decode('utf-8')
        query_params = parse_qs(query_string)
        token_key = query_params.get('token', [None])[0]

        if token_key is None:
            print("CONSUMER-DEBUG: Connection REJECTED - No token.")
            self.close()
            return

        user = get_user_from_token(token_key)
        if user is None:
            print("CONSUMER-DEBUG: Connection REJECTED - Invalid token.")
            self.close()
            return

        self.scope['user'] = user
        self.room_group_name = f'notifications_{user.id}'
        
        # This is the most important log for subscribing
        print(f"CONSUMER-DEBUG: User '{user.username}' attempting to JOIN group '{self.room_group_name}'")
        
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        
        self.accept()
        print(f"CONSUMER-DEBUG: User '{user.username}' successfully CONNECTED and JOINED group '{self.room_group_name}'.\n")

    def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            print(f"CONSUMER-DEBUG: User disconnecting from group '{self.room_group_name}'")
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name,
                self.channel_name
            )
            print("CONSUMER-DEBUG: Disconnected.\n")

    # This is the method that should receive the message from the view
    def send_notification(self, event):
        # This is the most important log for receiving
        print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"!!! CONSUMER-DEBUG: 'send_notification' method was TRIGGERED for group '{self.room_group_name}'")
        
        message = event['message']
        print(f"!!! CONSUMER-DEBUG: Message content is: {message}")
        
        self.send(text_data=json.dumps({
            'type': 'notification',
            'message': message
        }))
        
        print(f"!!! CONSUMER-DEBUG: Message has been sent down the WebSocket to the browser.")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")