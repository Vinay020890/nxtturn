# C:\Users\Vinay\Project\Loopline\community\signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import UserProfile, Follow, Like, StatusPost, Notification, Comment

from .serializers import NotificationSerializer

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# This utility function will help us avoid repeating code
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


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

# --- VERSION 2: HANDLES LIKES ON POSTS AND COMMENTS ---
@receiver(post_save, sender=Like)
def create_like_notification(sender, instance, created, **kwargs):
    if not created:
        return

    liked_object = instance.content_object
    liker = instance.user
    
    recipient = None
    verb = ""
    target = None

    # Case 1: The liked object is a StatusPost
    if isinstance(liked_object, StatusPost):
        recipient = liked_object.author
        verb = "liked your post"
        target = liked_object

    # Case 2: The liked object is a Comment
    elif isinstance(liked_object, Comment):
        recipient = liked_object.author
        verb = "liked your comment"
        target = liked_object
    
    # If we have a valid recipient and they are not liking their own content
    if recipient and recipient != liker:
        notification = Notification.objects.create(
            recipient=recipient,
            actor=liker,
            verb=verb,
            notification_type=Notification.LIKE,
            action_object=instance,
            target=target
        )
        print(f"Notification (Like): Created for {recipient.username}")
        send_realtime_notification(notification)


# --- VERSION 2: HANDLES COMMENTS & REPLIES WITH REAL-TIME PUSH ---
@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if not created:
        return

    commented_on_object = instance.content_object
    commenter = instance.author

    # --- Case 1: The comment is a REPLY to a parent comment ---
    if instance.parent:
        parent_comment_author = instance.parent.author
        
        # Only notify if someone is replying to another person's comment.
        if parent_comment_author != commenter:
            notification = Notification.objects.create(
                recipient=parent_comment_author,
                actor=commenter,
                verb="replied to your comment",
                notification_type=Notification.REPLY,
                action_object=instance,
                target=instance.parent
            )
            print(f"Notification (Reply): Created for {parent_comment_author.username}")
            send_realtime_notification(notification)
            # We are done. We don't also need to notify the original post author.
            return 

    # --- Case 2: The comment is a TOP-LEVEL comment on a post ---
    # This code only runs if the "if instance.parent:" block above did not run and return.
    if isinstance(commented_on_object, StatusPost):
        post_author = commented_on_object.author
        
        # Only notify if someone is commenting on another person's post.
        if post_author != commenter:
            notification = Notification.objects.create(
                recipient=post_author,
                actor=commenter,
                verb="commented on your post",
                notification_type=Notification.COMMENT,
                action_object=instance,
                target=commented_on_object
            )
            print(f"Notification (Comment): Created for {post_author.username}")
            send_realtime_notification(notification)

@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    """
    Create a notification when a Follow object is created.
    """
    if not created:
        return

    followed_user = instance.following
    follower = instance.follower

    # Prevent self-notification (though your model constraint should already prevent this)
    if followed_user != follower:
        # 1. Create the database notification
        notification = Notification.objects.create(
            recipient=followed_user,
            actor=follower,
            verb="started following you",
            notification_type='follow', # We will need to add 'follow' to the model choices
            action_object=instance # The Follow instance itself
        )
        print(f"Notification (Follow): Created for {followed_user.username}")

        # 2. Send the real-time message
        send_realtime_notification(notification)