# C:\Users\Vinay\Project\Loopline\community\signals.py
# --- FINAL VERSION WITH SAFER DUPLICATE CHECKING ---

import re
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from .models import UserProfile, Follow, Like, StatusPost, Notification, Comment

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .serializers import NotificationSerializer, LivePostSerializer

User = get_user_model()

# --- HELPER FUNCTION ---
def send_realtime_notification(notification_instance):
    """Serializes and sends a notification to the correct user group."""
    serializer = NotificationSerializer(notification_instance)
    channel_layer = get_channel_layer()
    group_name = f'user_{notification_instance.recipient.id}'
    message_data = {
        'type': 'send_notification',
        'message': {'type': 'new_notification', 'payload': serializer.data}
    }
    async_to_sync(channel_layer.group_send)(group_name, message_data)
    print(f"!!! REAL-TIME ({notification_instance.notification_type}): Sent to group {group_name} !!!")


# --- SIGNAL HANDLERS (All updated with the safer .exists() check) ---

@receiver(post_save, sender=User, dispatch_uid="create_user_profile_signal")
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

# In community/signals.py

# ... (other signal handlers) ...

# --- REPLACE the entire create_like_notification function with this one ---
@receiver(post_save, sender=Like, dispatch_uid="create_like_notification_signal")
def create_like_notification(sender, instance, created, **kwargs):
    if not created: return

    liked_object = instance.content_object
    liker = instance.user
    
    # Use our new helper property to get the top-level post.
    # This works for both likes on posts and likes on comments.
    post_target = instance.parent_post

    # Determine the recipient and verb based on the type of the liked object
    if isinstance(liked_object, StatusPost):
        recipient = liked_object.author
        verb = "liked your post"
        # For a like on a post, the target is the post itself.
        notification_target = liked_object
    elif isinstance(liked_object, Comment):
        recipient = liked_object.author
        verb = "liked your reply" if liked_object.parent else "liked your comment"
        # For a like on a comment, the target is ALSO the comment itself.
        notification_target = liked_object
    else:
        return # Do not handle likes for other types of objects

    if recipient and recipient != liker:
        action_object_content_type = ContentType.objects.get_for_model(instance)
        
        # Check if a notification for this specific action already exists
        if not Notification.objects.filter(
            recipient=recipient, actor=liker,
            action_object_content_type=action_object_content_type,
            action_object_object_id=instance.id
        ).exists():
            notification = Notification.objects.create(
                recipient=recipient, 
                actor=liker, 
                verb=verb,
                notification_type=Notification.LIKE,
                action_object=instance, 
                # This is the key: the target is now correctly set.
                target=notification_target
            )
            print(f"Notification (Like): Created for {recipient.username} with verb: '{verb}'")
            send_realtime_notification(notification)

@receiver(post_save, sender=Follow, dispatch_uid="create_follow_notification_signal")
def create_follow_notification(sender, instance, created, **kwargs):
    if not created: return

    followed_user, follower = instance.following, instance.follower

    if followed_user != follower:
        action_object_content_type = ContentType.objects.get_for_model(instance)
        if not Notification.objects.filter(
            recipient=followed_user, actor=follower, verb="started following you",
            action_object_content_type=action_object_content_type,
            action_object_object_id=instance.id
        ).exists():
            notification = Notification.objects.create(
                recipient=followed_user, actor=follower, verb="started following you",
                notification_type=Notification.FOLLOW, action_object=instance
            )
            print(f"Notification (Follow): Created for {followed_user.username}")
            send_realtime_notification(notification)

@receiver(post_save, sender=Comment, dispatch_uid="create_comment_reply_notification_signal")
def create_comment_and_reply_notification(sender, instance, created, **kwargs):
    if not created: return

    commenter, post = instance.author, instance.content_object
    
    if instance.parent: # This is a reply
        recipient, verb, notification_type = instance.parent.author, "replied to your comment", Notification.REPLY
    else: # This is a top-level comment
        recipient, verb, notification_type = post.author, "commented on your post", Notification.COMMENT

    mentioned_usernames = set(re.findall(r'@(\w+)', instance.content or ''))
    if recipient != commenter and recipient.username not in mentioned_usernames:
        action_object_content_type = ContentType.objects.get_for_model(instance)
        if not Notification.objects.filter(
            recipient=recipient, actor=commenter, verb=verb,
            action_object_content_type=action_object_content_type,
            action_object_object_id=instance.id
        ).exists():
            notification = Notification.objects.create(
                recipient=recipient, actor=commenter, verb=verb,
                notification_type=notification_type,
                action_object=instance, target=post
            )
            print(f"Notification ({notification_type}): Created for {recipient.username}")
            send_realtime_notification(notification)

@receiver(post_save, sender=StatusPost, dispatch_uid="post_mention_handler_signal")
@receiver(post_save, sender=Comment, dispatch_uid="comment_mention_handler_signal")
def create_mention_notifications(sender, instance, created, **kwargs):
    if not created: return
    
    if sender is StatusPost:
        verb, target = "mentioned you in a post", instance
    elif sender is Comment:
        verb = "mentioned you in a reply" if instance.parent else "mentioned you in a comment"
        target = instance.content_object
    else: return

    actor = instance.author
    mentioned_users = set(re.findall(r'@(\w+)', instance.content or ''))
    action_object_content_type = ContentType.objects.get_for_model(instance)

    for username in mentioned_users:
        try:
            recipient = User.objects.get(username=username)
            if recipient != actor:
                if not Notification.objects.filter(
                    recipient=recipient, actor=actor, verb=verb,
                    action_object_content_type=action_object_content_type,
                    action_object_object_id=instance.id
                ).exists():
                    notification = Notification.objects.create(
                        recipient=recipient, actor=actor, verb=verb,
                        notification_type=Notification.MENTION,
                        target=target, action_object=instance
                    )
                    print(f"Notification (Mention): Created for {recipient.username} with verb: '{verb}'")
                    send_realtime_notification(notification)
        except User.DoesNotExist:
            continue

@receiver(post_save, sender=StatusPost, dispatch_uid="live_post_to_followers_signal")
def send_live_post_to_followers(sender, instance, created, **kwargs):
    if not created: return

    author = instance.author
    followers = Follow.objects.filter(following=author).select_related('follower')
    
    if not followers:
        print(f"Live Post: Author {author.username} has no followers. No message sent.")
        return

    serializer = LivePostSerializer(instance)
    channel_layer = get_channel_layer()
    message_data = {
        'type': 'send_live_post',
        'message': {
            'type': 'new_post',
            'payload': serializer.data
        }
    }

    for follow_relation in followers:
        follower = follow_relation.follower
        group_name = f'user_{follower.id}'
        async_to_sync(channel_layer.group_send)(group_name, message_data)
        print(f"!!! REAL-TIME (New Post): Sent post ID {instance.id} to group {group_name} for user {follower.username} !!!")