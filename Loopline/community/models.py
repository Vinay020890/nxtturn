from django.db import models
# from django.contrib.auth.models import User # Old way
from django.conf import settings # Import Django settings
from django.contrib.postgres.fields import ArrayField # Import ArrayField for lists

# Imports needed for Generic Relations in Comment model
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

# Define User using settings (best practice)
User = settings.AUTH_USER_MODEL

# Create your models here.

class UserProfile(models.Model):
    """
    Stores extended information for a user, linked one-to-one with the base User model.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True) # Links to the User model
    bio = models.TextField(blank=True, null=True) # Allows empty bio
    location_city = models.CharField(max_length=100, blank=True, null=True)
    location_state = models.CharField(max_length=100, blank=True, null=True)
    college_name = models.CharField(max_length=255, blank=True, null=True)
    major = models.CharField(max_length=255, blank=True, null=True)
    graduation_year = models.IntegerField(blank=True, null=True)
    linkedin_url = models.URLField(max_length=512, blank=True, null=True)
    portfolio_url = models.URLField(max_length=512, blank=True, null=True)
    # Use ArrayField for PostgreSQL to store lists of text
    skills = ArrayField(models.CharField(max_length=100), blank=True, null=True, default=list)
    interests = ArrayField(models.CharField(max_length=100), blank=True, null=True, default=list)
    # profile_picture_url = models.URLField(max_length=512, blank=True, null=True) # Simple URL field for now

    # --- ADD NEW ImageField ---
    picture = models.ImageField(
        upload_to='profile_pics/',  # Images will be stored in MEDIA_ROOT/profile_pics/
        null=True,                  # Allows the field to be empty in the database
        blank=True                  # Allows the field to be empty in forms/admin
    )
    # --- END NEW ImageField ---
    
    updated_at = models.DateTimeField(auto_now=True) # Automatically updates on save

    def __str__(self):
        # Access username via the user relation correctly
        # Assuming the related User model has a 'username' attribute
        try:
            return self.user.username
        except AttributeError:
            return f"UserProfile object (User ID: {self.user_id})"


class Follow(models.Model):
    """
    Represents a relationship where one user follows another.
    """
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE) # User doing the following
    following = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE) # User being followed
    created_at = models.DateTimeField(auto_now_add=True) # Automatically set on creation

    class Meta:
        # Ensures a user cannot follow the same person multiple times
        unique_together = ('follower', 'following')
        # Optional: Add ordering if needed when querying
        # ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(check=~models.Q(follower=models.F('following')), name='prevent_self_follow')
        ]


    def __str__(self):
        # Ensure users exist before accessing username
        follower_username = self.follower.username if self.follower else 'Unknown'
        following_username = self.following.username if self.following else 'Unknown'
        return f"{follower_username} follows {following_username}"

class StatusPost(models.Model):
    """
    Represents a simple status update posted by a user, not tied to a specific forum or group.
    """
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='status_posts') # User who wrote the post
    content = models.TextField() # The main text content of the post
    image = models.ImageField(upload_to='post_images/', null=True, blank=True)
    video = models.FileField(upload_to='post_videos/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True) # Timestamp when created
    updated_at = models.DateTimeField(auto_now=True) # Timestamp when last updated

    # Inside class StatusPost(models.Model):
    # ... author, content, created_at, updated_at fields ...

    likes = GenericRelation('Like', related_query_name='statuspost_likes') # <-- ADD THIS LINE

    class Meta:
        ordering = ['-created_at'] # Default order is newest first

    def clean(self):
        super().clean() # It's good practice to call the parent's clean method
        if not self.content and not self.image and not self.video:
            raise ValidationError('A post must have either text content, an image, or a video.')


    def __str__(self):
        # Ensure author exists before accessing username
        author_username = self.author.username if self.author else 'Unknown Author'
        return f"{author_username}: {self.content[:50]}..."

class ForumCategory(models.Model):
    """
    Top-level categories for forums (e.g., Academics, Career Advice).
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    # slug = models.SlugField(unique=True) # Optional: for clean URLs later

    class Meta:
        verbose_name_plural = "Forum Categories" # Correct plural in admin

    def __str__(self):
        return self.name

class Group(models.Model):
    """
    Represents a community group users can join.
    """
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_groups')
    members = models.ManyToManyField(User, related_name='joined_groups', blank=True) # Users who are part of the group
    created_at = models.DateTimeField(auto_now_add=True)
    # slug = models.SlugField(unique=True) # Optional: for clean URLs later
    # is_public = models.BooleanField(default=True) # To distinguish public/private later

    def __str__(self):
        return self.name

class ForumPost(models.Model):
    """
    Represents a thread/post within a Forum Category or a Group.
    Can also be used for Group posts.
    """
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_posts')
    category = models.ForeignKey(ForumCategory, on_delete=models.SET_NULL, blank=True, null=True, related_name='posts') # Link to ForumCategory (optional)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True, related_name='posts') # Link to Group (optional)
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Inside class ForumPost(models.Model):
    # ... other fields like author, group, title, content etc. ...

    likes = GenericRelation('Like', related_query_name='forumpost_likes') # <-- ADD THIS LINE

    class Meta:
        ordering = ['-created_at']
        # Add constraint to ensure a post belongs to EITHER a category OR a group, but not both/neither
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

# Note: The line `ForumPost.add_to_class(...)` is no longer needed as 'group' is defined directly above.

# --- Updated Comment Model using Generic Relations ---
class Comment(models.Model):
    """
    Represents a comment using Generic Relations to link to various content types.
    """
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- Generic Relation Fields ---
    # Stores the type of the object being commented on (e.g., StatusPost, ForumPost)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    # Stores the ID (primary key) of the specific object being commented on
    object_id = models.PositiveIntegerField()
    # Helper field to easily access the related object (StatusPost, ForumPost, etc.)
    # Uses the 'content_type' and 'object_id' fields above
    content_object = GenericForeignKey('content_type', 'object_id')
    # --- End of Generic Relation Fields ---

    # parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='replies') # Keep commented out for now (for nested replies later)

    class Meta:
        ordering = ['created_at'] # Show oldest comments first
        # Add indexes for faster lookups based on the generic relation fields
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        # Ensure author exists
        author_username = self.author.username if self.author else 'Unknown Author'
        # Attempt to get the related object's string representation for clarity
        try:
            # Accessing self.content_object can trigger a DB query
            target = self.content_object if self.content_object else f"{self.content_type} ID:{self.object_id}"
            target_str = str(target) # Get string representation
        except Exception: # Catch potential errors if object/content_type is missing
             target_str = f"related object (ContentType ID: {self.content_type_id}, Object ID: {self.object_id})"
        return f"Comment by {author_username} on {target_str[:50]}" # Limit length for display

# --- End of Updated Comment Model ---


# --- Replace your existing Like model with this in models.py ---
class Like(models.Model):
    """
    Represents a 'like' given by a user to another object (e.g., StatusPost, ForumPost).
    Uses Generic Relations to point to different types of objects.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes')

    # --- Fields required for Generic Relation ---
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField() # Stores the ID of the liked object
    content_object = GenericForeignKey('content_type', 'object_id') # The actual generic link
    # --- End of Generic Relation fields ---

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensure a user cannot like the same object multiple times
        unique_together = ('user', 'content_type', 'object_id')
        ordering = ['-created_at']
        # Add indexes for faster lookups
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        # Try to get a meaningful representation
        try:
            # Limit target object string length for admin/logs if needed
            target_str = str(self.content_object)
            return f'{self.user.username} likes "{target_str[:30]}..."'
        except Exception:
             return f'{self.user.username} liked object ID {self.object_id} of type {self.content_type.model}'
# --- End of replacement ---

# --- Signals ---
# Import necessary modules for signals
from django.db.models.signals import post_save
from django.dispatch import receiver

# Ensure User is correctly defined above using settings.AUTH_USER_MODEL

# --- Add these models for Private Messaging ---

class Conversation(models.Model):
    """
    Represents a private conversation thread between two or more users.
    For simplicity, starting with exactly two participants.
    """
    # Using ManyToManyField to link participants to the conversation
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Tracks last message time

    class Meta:
        ordering = ['-updated_at'] # Show most recently active conversations first

    def __str__(self):
        # Generate a string representation, e.g., listing participant usernames
        usernames = ", ".join([user.username for user in self.participants.all()])
        return f"Conversation between {usernames}" if usernames else "Empty Conversation"

class Message(models.Model):
    """
    Represents a single message within a Conversation.
    """
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    # Optional: Add a 'read_at' field later for read receipts
    # read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp'] # Show messages in chronological order

    def __str__(self):
        return f"Message from {self.sender.username} in Convo ID {self.conversation.id} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

# --- End of Private Messaging Models ---

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal receiver that creates a UserProfile instance automatically
    when a new User instance is created and saved.
    """
    if created: # Only run for newly created User instances
        UserProfile.objects.create(user=instance)

# Note: The save_user_profile signal might be redundant if profile creation is robust
# and updates happen via profile serializers/views. Consider if it's strictly needed.
# If kept, ensure it handles potential race conditions or unique constraint errors if needed.
# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     """
#     Signal receiver that saves the UserProfile instance automatically
#     when the related User instance is saved.
#     (Useful if UserProfile might be created by other means later)
#     """
#     # Check if profile exists before trying to save
#     # This check might be slightly redundant if create_user_profile always runs first on creation,
#     # but it adds robustness.
#     if hasattr(instance, 'userprofile'):
#          instance.userprofile.save()
#     else:
#         # If profile doesn't exist (e.g., for existing users created before this signal), create it.
#         # This handles cases where the create_user_profile might have failed or wasn't active previously.
#         UserProfile.objects.get_or_create(user=instance) # Use get_or_create for safety