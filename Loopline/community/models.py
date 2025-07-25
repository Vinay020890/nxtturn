import os
from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver

User = settings.AUTH_USER_MODEL

# --- Helper Function for Dynamic Upload Paths ---
def get_post_media_path(instance, filename):
    """
    Dynamically determine the upload path based on the media type.
    Images go into 'post_images/' and videos into 'post_videos/'.
    """
    if instance.media_type == 'image':
        return os.path.join('post_images', filename)
    elif instance.media_type == 'video':
        return os.path.join('post_videos', filename)
    return os.path.join('post_media_other', filename)
# --- End Helper Function ---


# --- MODELS START HERE ---

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    location_city = models.CharField(max_length=100, blank=True, null=True)
    location_state = models.CharField(max_length=100, blank=True, null=True)
    college_name = models.CharField(max_length=255, blank=True, null=True)
    major = models.CharField(max_length=255, blank=True, null=True)
    graduation_year = models.IntegerField(blank=True, null=True)
    linkedin_url = models.URLField(max_length=512, blank=True, null=True)
    portfolio_url = models.URLField(max_length=512, blank=True, null=True)
    skills = ArrayField(models.CharField(max_length=100), blank=True, null=True, default=list)
    interests = ArrayField(models.CharField(max_length=100), blank=True, null=True, default=list)
    picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True, max_length=255)
    updated_at = models.DateTimeField(auto_now=True)

   
    saved_posts = models.ManyToManyField(
        'StatusPost', # Forward reference using string
        related_name='saved_by',
        blank=True
    )
    

    def __str__(self):
        try:
            return self.user.username
        except AttributeError:
            return f"UserProfile object (User ID: {self.user_id})"

class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')
        constraints = [
            models.CheckConstraint(check=~models.Q(follower=models.F('following')), name='prevent_self_follow')
        ]

    def __str__(self):
        follower_username = self.follower.username if self.follower else 'Unknown'
        following_username = self.following.username if self.following else 'Unknown'
        return f"{follower_username} follows {following_username}"

class StatusPost(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='status_posts')
    content = models.TextField(blank=True, null=True) # Now optional, validation moves to serializer

    group = models.ForeignKey('Group', on_delete=models.CASCADE, related_name='status_posts', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = GenericRelation('Like', related_query_name='statuspost_likes')

    # --- REMOVED in favor of PostMedia model ---
    # image = models.ImageField(upload_to='post_images/', null=True, blank=True)
    # video = models.FileField(upload_to='post_videos/', null=True, blank=True)
    # ---------------------------------------------

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        """
        Model-level validation is now simpler. The complex validation
        (post must have content OR media) is handled in the serializer,
        which has access to the incoming file data.
        """
        super().clean()
        # The check for content/image/video is removed from here.

    def __str__(self):
        author_username = self.author.username if self.author else 'Unknown Author'
        return f"Post by {author_username}: {self.content[:50] if self.content else 'Media Post'}..."

# --- NEW MODEL for handling multiple media files per post ---
class PostMedia(models.Model):
    """
    Represents a single media file (image or video) linked to a StatusPost.
    This allows a post to have a gallery of multiple media items.
    """
    MEDIA_TYPE_CHOICES = (
        ('image', 'Image'),
        ('video', 'Video'),
    )

    post = models.ForeignKey(StatusPost, related_name='media', on_delete=models.CASCADE)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    file = models.FileField(upload_to=get_post_media_path, max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at'] # Order media by upload time

    def __str__(self):
        return f"{self.media_type.capitalize()} for Post ID {self.post.id}"
# --- END NEW MODEL ---


class ForumCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Forum Categories"

    def __str__(self):
        return self.name

class Group(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_groups')
    members = models.ManyToManyField(User, related_name='joined_groups', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # --- NEW FIELD: privacy_level ---
    PRIVACY_CHOICES = [
        ('public', 'Public - Anyone can view content and join directly'),
        ('private', 'Private - Only members can view content, requires approval to join'),
    ]
    privacy_level = models.CharField(
        max_length=10,
        choices=PRIVACY_CHOICES,
        default='public', # Default to public unless specified otherwise
        help_text="Defines who can view content and how users can join."
    )
    # --- END NEW FIELD ---

    def __str__(self):
        return self.name

class ForumPost(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_posts')
    category = models.ForeignKey(ForumCategory, on_delete=models.SET_NULL, blank=True, null=True, related_name='posts')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True, related_name='forum_posts')
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = GenericRelation('Like', related_query_name='forumpost_likes')

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=(
                    (models.Q(category__isnull=False) & models.Q(group__isnull=True)) |
                    (models.Q(category__isnull=True) & models.Q(group__isnull=False))
                ),
                name='forumpost_has_one_target'
            )
        ]

    def __str__(self):
        return self.title

class Comment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='replies')
    likes = GenericRelation('Like', related_query_name='comment_likes')

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        author_username = self.author.username if self.author else 'Unknown Author'
        try:
            target = self.content_object if self.content_object else f"{self.content_type} ID:{self.object_id}"
            target_str = str(target)
        except Exception:
             target_str = f"related object (ContentType ID: {self.content_type_id}, Object ID: {self.object_id})"
        return f"Comment by {author_username} on {target_str[:50]}"

class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        try:
            target_str = str(self.content_object)
            return f'{self.user.username} likes "{target_str[:30]}..."'
        except Exception:
             return f'{self.user.username} liked object ID {self.object_id} of type {self.content_type.model}'

class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notifications_received', on_delete=models.CASCADE)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notifications_sent', on_delete=models.CASCADE)
    verb = models.CharField(max_length=255)
    LIKE = 'like'
    COMMENT = 'comment'
    REPLY = 'reply'
    MENTION = 'mention'
    NOTIFICATION_TYPE_CHOICES = [
        (LIKE, 'Like on your Post'),
        (COMMENT, 'Comment on your Post'),
        (REPLY, 'Reply to your Comment'),
        (MENTION, 'Mention in a Post/Comment'),
    ]
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES, blank=True, null=True)
    action_object_content_type = models.ForeignKey(ContentType, related_name='notification_action_object', on_delete=models.CASCADE, null=True, blank=True)
    action_object_object_id = models.PositiveIntegerField(null=True, blank=True)
    action_object = GenericForeignKey('action_object_content_type', 'action_object_object_id')
    target_content_type = models.ForeignKey(ContentType, related_name='notification_target', on_delete=models.CASCADE, null=True, blank=True)
    target_object_object_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey('target_content_type', 'target_object_object_id')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-timestamp']),
        ]

    def __str__(self):
        parts = [str(self.actor.username)]
        parts.append(self.verb)
        if self.target:
            parts.append(f"on your {self.target_content_type.model}")
        status = "Read" if self.is_read else "Unread"
        return f"To: {self.recipient.username} - {' '.join(parts)} - {status}"


class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        usernames = ", ".join([user.username for user in self.participants.all()])
        return f"Conversation between {usernames}" if usernames else "Empty Conversation"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.sender.username} in Convo ID {self.conversation.id} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
class Poll(models.Model):
    """
    Represents a poll attached to a StatusPost.
    """
    post = models.OneToOneField(StatusPost, on_delete=models.CASCADE, related_name='poll')
    question = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Poll for Post ID {self.post.id}: {self.question}"

class PollOption(models.Model):
    """
    Represents one choice/option within a Poll.
    """
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Option for Poll ID {self.poll.id}: {self.text}"

class PollVote(models.Model):
    """
    Represents a single user's vote on a poll option.
    Ensures a user can only vote once per poll.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='poll_votes')
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='votes')
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name='votes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'poll') # One vote per user per poll
        ordering = ['-created_at']

    def __str__(self):
        return f"Vote by {self.user.username} on Poll ID {self.poll.id}"
    
# === PASTE THIS NEW MODEL AFTER PollVote AND BEFORE THE @receiver FUNCTIONS ===

class Report(models.Model):
    # --- Report Details ---
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submitted_reports')

    # The generic link to the content being reported.
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # The reason for the report.
    REASON_CHOICES = [
        ('SPAM', 'Spam or Misleading'),
        ('HARASSMENT', 'Harassment or Bullying'),
        ('HATE_SPEECH', 'Hate Speech'),
        ('VIOLENCE', 'Violence or Graphic Content'),
        ('OTHER', 'Other'),
    ]
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    details = models.TextField(blank=True, null=True, help_text="Provide more details if 'Other' is selected.")

    # --- Moderation Status ---
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('REVIEWED', 'Under Review'),
        ('ACTION_TAKEN', 'Action Taken'),
        ('DISMISSED', 'Dismissed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    # Who handled the report and when.
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='moderated_reports'
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderator_notes = models.TextField(blank=True, null=True, help_text="Notes for internal review.")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        # A user can only report a specific piece of content once.
        unique_together = ('reporter', 'content_type', 'object_id')

    def __str__(self):
        return f"Report by {self.reporter.username} on {self.content_object} ({self.get_reason_display()})"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

# The save_user_profile signal is commented out as it's often redundant.
# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     if hasattr(instance, 'userprofile'):
#          instance.userprofile.save()
#     else:
#         UserProfile.objects.get_or_create(user=instance)