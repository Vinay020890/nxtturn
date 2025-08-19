# C:\Users\Vinay\Project\Loopline\community\signals.py

import re
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import UserProfile, Follow, Like, StatusPost, Notification, Comment
from .serializers import NotificationSerializer

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

User = get_user_model()

# --- HELPER FUNCTIONS ---

def send_realtime_notification(notification_instance):
    """Serializes and sends a notification to the correct user group."""
    serializer = NotificationSerializer(notification_instance)
    channel_layer = get_channel_layer()
    group_name = f'notifications_{notification_instance.recipient.id}'
    message_data = {
        'type': 'send_notification',
        'message': {'type': 'new_notification', 'payload': serializer.data}
    }
    async_to_sync(channel_layer.group_send)(group_name, message_data)
    print(f"!!! REAL-TIME ({notification_instance.notification_type}): Sent to group {group_name} !!!")

def parse_mentions(text):
    """Finds all @username patterns in a block of text and returns valid User objects."""
    mention_pattern = r'@(\w+)'
    usernames = re.findall(mention_pattern, text)
    if not usernames:
        return []
    return User.objects.filter(username__in=usernames)


# --- SIGNAL HANDLERS ---

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=Like)
def create_like_notification(sender, instance, created, **kwargs):
    if not created: return
    liked_object, liker, recipient, verb, target = instance.content_object, instance.user, None, "", None
    if isinstance(liked_object, (StatusPost, Comment)):
        recipient = liked_object.author
        verb = "liked your post" if isinstance(liked_object, StatusPost) else "liked your comment"
        target = liked_object
    if recipient and recipient != liker:
        notification = Notification.objects.create(recipient=recipient, actor=liker, verb=verb, notification_type=Notification.LIKE, action_object=instance, target=target)
        print(f"Notification (Like): Created for {recipient.username}")
        send_realtime_notification(notification)

@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    if not created: return
    followed_user, follower = instance.following, instance.follower
    if followed_user != follower:
        notification = Notification.objects.create(recipient=followed_user, actor=follower, verb="started following you", notification_type='follow', action_object=instance)
        print(f"Notification (Follow): Created for {followed_user.username}")
        send_realtime_notification(notification)

@receiver(post_save, sender=StatusPost)
def create_mention_notification_for_post(sender, instance, created, **kwargs):
    """Handles mentions in new StatusPost objects."""
    if created and instance.content:
        mentioned_users = parse_mentions(instance.content)
        for user in mentioned_users:
            if user != instance.author:
                notification = Notification.objects.create(
                    recipient=user,
                    actor=instance.author,
                    verb="mentioned you in a post",
                    notification_type=Notification.MENTION,
                    action_object=instance,
                    target=instance
                )
                print(f"Notification (Mention in Post): Created for {user.username}")
                send_realtime_notification(notification)

@receiver(post_save, sender=Comment)
def handle_new_comment_notifications(sender, instance, created, **kwargs):
    """
    A single, unified handler for all new comment notifications.
    It handles mentions, replies, and top-level comments, preventing duplicates.
    """
    if not created:
        return

    commenter = instance.author
    notified_users = {commenter} # Use a set for efficient duplicate checking

    # --- 1. Handle Mentions First ---
    if instance.content:
        mentioned_users = parse_mentions(instance.content)
        for user in mentioned_users:
            if user not in notified_users:
                notification = Notification.objects.create(
                    recipient=user,
                    actor=commenter,
                    verb="mentioned you in a comment",
                    notification_type=Notification.MENTION,
                    action_object=instance,
                    target=instance.content_object
                )
                print(f"Notification (Mention): Created for {user.username}")
                send_realtime_notification(notification)
                notified_users.add(user)

    # --- 2. Handle Reply Notification ---
    if instance.parent:
        parent_author = instance.parent.author
        # Only notify the parent author if they haven't already been notified by a mention
        if parent_author not in notified_users:
            notification = Notification.objects.create(
                recipient=parent_author,
                actor=commenter,
                verb="replied to your comment",
                notification_type=Notification.REPLY,
                action_object=instance,
                target=instance.parent
            )
            print(f"Notification (Reply): Created for {parent_author.username}")
            send_realtime_notification(notification)
            notified_users.add(parent_author)

    # --- 3. Handle Top-Level Comment Notification ---
    elif isinstance(instance.content_object, StatusPost):
        post_author = instance.content_object.author
        # Only notify the post author if they haven't already been notified by a mention
        if post_author not in notified_users:
            notification = Notification.objects.create(
                recipient=post_author,
                actor=commenter,
                verb="commented on your post",
                notification_type=Notification.COMMENT,
                action_object=instance,
                target=instance.content_object
            )
            print(f"Notification (Comment): Created for {post_author.username}")
            send_realtime_notification(notification)
            notified_users.add(post_author)