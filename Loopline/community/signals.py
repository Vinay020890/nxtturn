# community/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
# Import the UserProfile model from models.py in the same directory
from .models import UserProfile, Like, StatusPost, Notification, Comment

# Get the currently active User model (best practice)


# community/signals.py

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Uses get_or_create to ensure a UserProfile exists for every User.
    Creates one if it's missing (handles new users and existing users saved later).
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)
    
# ---- ADD THE NEW SIGNAL HANDLER BELOW ----
@receiver(post_save, sender=Like)
def create_like_notification(sender, instance, created, **kwargs):
    """
    Create a notification when a Like object is created,
    if the liked object is a StatusPost.
    """
    if created: # Only run when a new Like instance is created
        liked_object = instance.content_object # This is the StatusPost (or could be ForumPost, etc.)
        
        # Check if the liked object is an instance of StatusPost
        if isinstance(liked_object, StatusPost):
            status_post_author = liked_object.author
            liker = instance.user # The user who created the Like

            # Prevent self-notification
            if status_post_author != liker:
                Notification.objects.create(
                    recipient=status_post_author,
                    actor=liker,
                    verb="liked", 
                    notification_type=Notification.LIKE,
                    
                    action_object_content_type=ContentType.objects.get_for_model(instance), # The Like instance
                    action_object_object_id=instance.pk,
                    
                    target_content_type=ContentType.objects.get_for_model(liked_object), # The StatusPost
                    target_object_object_id=liked_object.pk
                )
                print(f"Notification created: {liker.username} liked {status_post_author.username}'s status post (ID: {liked_object.pk})")
        # else:
            # print(f"Like created on a non-StatusPost object: {type(liked_object)}") # For debugging other types
# ---- END OF NEW SIGNAL HANDLER ----

# ---- HANDLER 3 (NEW - For Comments) ----
@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created:
        commented_on_object = instance.content_object # e.g., StatusPost
        commenter = instance.author

        # --- Notification for the author of the main post (StatusPost) ---
        if isinstance(commented_on_object, StatusPost):
            status_post_author = commented_on_object.author
            if status_post_author != commenter: # Don't notify if commenting on own post
                Notification.objects.create(
                    recipient=status_post_author,
                    actor=commenter,
                    verb="commented on",
                    notification_type=Notification.COMMENT,
                    action_object=instance, # The comment itself
                    target=commented_on_object # The StatusPost
                )
                print(f"Notification (Comment on Post): {commenter.username} commented on {status_post_author.username}'s post (ID: {commented_on_object.pk})")

        # --- Notification for the author of the parent comment (if it's a reply) ---
        if instance.parent: # Check if this comment is a reply (has a parent comment)
            parent_comment_author = instance.parent.author
            
            # Don't notify if replying to own comment
            # Also, don't double-notify if the parent comment author is the same as the post author
            # (and they already received a "commented on your post" notification for this same new comment instance)
            
            # Condition to send reply notification:
            # 1. Parent comment author is not the current commenter.
            # 2. Parent comment author is not the same as the main post author (if main post author was already notified above).
            #    OR if the commented_on_object was not a StatusPost (so no post author notification was sent).

            send_reply_notification = False
            if parent_comment_author != commenter:
                if isinstance(commented_on_object, StatusPost):
                    if parent_comment_author != commented_on_object.author:
                        send_reply_notification = True
                else: # If not a StatusPost, then no previous notification to post author, so notify parent comment author
                    send_reply_notification = True
            
            if send_reply_notification:
                Notification.objects.create(
                    recipient=parent_comment_author,
                    actor=commenter,
                    verb="replied to", # Or "replied to your comment"
                    notification_type=Notification.REPLY, # Using the constant
                    action_object=instance, # The new reply (current comment instance)
                    target=instance.parent  # The parent comment is the target
                )
                print(f"Notification (Reply to Comment): {commenter.username} replied to {parent_comment_author.username}'s comment (ParentCommentID: {instance.parent.pk})")