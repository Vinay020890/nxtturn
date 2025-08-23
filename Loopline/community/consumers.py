# C:\Users\Vinay\Project\Loopline\community\consumers.py
# --- UPGRADED AND GENERALIZED VERSION ---

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

# --- RENAMED: from NotificationConsumer to UserActivityConsumer ---
class UserActivityConsumer(WebsocketConsumer):
    def connect(self):
        # ... (Connect logic is unchanged)
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
        # --- RENAMED: from 'notifications_{id}' to 'user_{id}' for broader use ---
        self.room_group_name = f'user_{user.id}'
        
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()
        print(f"CONSUMER-DEBUG: User '{user.username}' successfully CONNECTED and JOINED group '{self.room_group_name}'.\n")

    def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name,
                self.channel_name
            )

    # --- EXISTING METHOD: Handles receiving notification events from signals ---
    def send_notification(self, event):
        message_data = event['message']
        self.send(text_data=json.dumps({
            'type': 'notification',
            'message': message_data
        }))
        print(f"!!! CONSUMER-DEBUG: Sent 'new_notification' to browser for group '{self.room_group_name}'")

    # --- NEW METHOD: Handles receiving new post events from signals ---
    def send_live_post(self, event):
        message_data = event['message']
        self.send(text_data=json.dumps({
            'type': 'live_post',
            'message': message_data
        }))
        print(f"!!! CONSUMER-DEBUG: Sent 'new_post' to browser for group '{self.room_group_name}'")