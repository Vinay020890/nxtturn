from rest_framework import serializers
# from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from .models import UserProfile, Follow, StatusPost, ForumCategory, Group, ForumPost, Comment, Like, Conversation, Message

User = get_user_model() 

# Basic serializer for the built-in User model (to nest in profile)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # Select only the fields needed publicly for the profile view
        fields = ['id', 'username', 'first_name', 'last_name']
        read_only_fields = ['id', 'username'] # Usually username isn't changed here

# Serializer for our UserProfile model
class UserProfileSerializer(serializers.ModelSerializer):
    # Nest the UserSerializer to include basic user info when reading
    user = UserSerializer(read_only=True)
    # Explicitly declare ArrayFields if needed, though ModelSerializer might handle basic cases
    skills = serializers.ListField(child=serializers.CharField(max_length=100), required=False, allow_null=True)
    interests = serializers.ListField(child=serializers.CharField(max_length=100), required=False, allow_null=True)
    is_followed_by_request_user = serializers.SerializerMethodField()
    picture = serializers.ImageField(read_only=True) # <-- ADDED THIS LINE

    class Meta:
        model = UserProfile
        # List all fields from UserProfile model you want in the API response
        # Note: 'user' field here refers to the foreign key ID when writing,
        # but the nested UserSerializer when reading (due to read_only=True above)
        fields = [
            'user',
            'bio',
            'location_city',
            'location_state',
            'college_name',
            'major',
            'graduation_year',
            'linkedin_url',
            'portfolio_url',
            'skills',
            'interests',
            # 'profile_picture_url',
            'picture',
            'updated_at',
            'is_followed_by_request_user'
        ]
        # Make profile fields writable (except user and updated_at)
        # The 'user' field on the profile itself shouldn't be changed via this API
        read_only_fields = ['user', 'updated_at', 'is_followed_by_request_user']

    def get_is_followed_by_request_user(self, obj):
        """
        Checks if the user making the request is following the user profile being serialized.
        'obj' here is the UserProfile instance.
        """
        # Get the request user from the context (passed by the view)
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return False # Anonymous users don't follow anyone

        request_user = request.user
        profile_user = obj.user # The user whose profile this is

        if request_user == profile_user:
            return False # Cannot follow yourself

        # Check if a Follow relationship exists
        # Need to import the Follow model
        from .models import Follow # Make sure this import is at the TOP of the file
        is_following = Follow.objects.filter(
            follower=request_user,
            following=profile_user
        ).exists()
        return is_following
    # --- END ADD METHOD ---

# Serializer specifically for UPDATING the profile (doesn't need nested user)
class UserProfileUpdateSerializer(serializers.ModelSerializer):
    # Explicitly declare ArrayFields for writing/updating
    skills = serializers.ListField(child=serializers.CharField(max_length=100), required=False, allow_null=True)
    interests = serializers.ListField(child=serializers.CharField(max_length=100), required=False, allow_null=True)
    picture = serializers.ImageField(required=False, allow_null=True, use_url=False)

    class Meta:
        model = UserProfile
        # Only include fields that the user is allowed to update
        fields = [
            'bio',
            'location_city',
            'location_state',
            'college_name',
            'major',
            'graduation_year',
            'linkedin_url',
            # 'portfolio_url',
            'picture',
            'skills',
            'interests',
            # 'profile_picture_url',
            'picture', # <-- ADDED THIS LINE
        ]


# Add this serializer below UserProfileUpdateSerializer

# --- UPDATED StatusPostSerializer ---
class StatusPostSerializer(serializers.ModelSerializer):
    """
    Serializer for StatusPost model. Includes author info, like status, and IDs for liking.
    """
    author = UserSerializer(read_only=True) # Use the UserSerializer
    is_liked_by_user = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField() # Use the model property
    content_type_id = serializers.SerializerMethodField()
    object_id = serializers.SerializerMethodField()
    post_type = serializers.SerializerMethodField()   
    comment_count = serializers.SerializerMethodField()   # <-- ADD THIS LINE 

     # ---- 1. EXPLICITLY DEFINE 'content' and 'image' FIELDS ----
    content = serializers.CharField(
        required=False,        # Makes it optional
        allow_blank=True,      # Allows empty string ""
        allow_null=True,       # Allows null (None)
        style={'base_template': 'textarea.html'} # Optional: for DRF browsable API
    )
    image = serializers.ImageField(
        max_length=None,       # Default
        use_url=True,          # Ensures URL is returned in responses
        required=False,        # Makes it optional
        allow_null=True,       # Allows null (None)
        allow_empty_file=True  # Allow empty file submission to clear image (DRF default is False, but allow_null=True often handles this)
                               # For clearing, usually client sends 'image': null.
                               # We'll primarily rely on required=False and allow_null=True.
    )
    # ---- END OF EXPLICIT FIELD DEFINITIONS ----   

    class Meta:
        model = StatusPost
        fields = [
            'id',
            'author',           # Nested UserSerializer
            'content',
            'image',
            'created_at',
            'updated_at',
            'like_count',       # Added
            'is_liked_by_user', # Added
            'content_type_id',  # Added for constructing like URL
            'object_id',        # Added for constructing like URL
            'post_type',        # <-- ADDED/ENSURED PRESENT
            'comment_count',    # <-- ADDED/ENSURED PRESENT
            
            
        ]
        # Ensure all read-only fields are listed
        read_only_fields = [
            'id', 'author', 'created_at', 'updated_at', 'like_count',
            'is_liked_by_user', 'content_type_id', 'object_id', 'post_type', 'comment_count'    
        ]
    # ---- 2. ADD THE 'validate' METHOD ----
    # A good place is after Meta and before get_... methods
    def validate(self, data):
        """
        Validate that either content or an image is provided.
        'data' here contains validated data for fields that were sent by the client.
        """
        # Get the prospective values.
        # If a field is not in `data` (client didn't send it), and it's optional (required=False),
        # its value for validation will depend on whether we are creating or updating.

        # For 'create', if a field is not sent, it's considered missing.
        # For 'update', if a field is not sent, it means "don't change this field".

        is_creating = self.instance is None

        # Determine the final state of content and image
        # Content: if 'content' in data, use that. Otherwise, if updating, use existing.
        final_content_value = data.get('content', self.instance.content if not is_creating else None)
        final_content_str = str(final_content_value).strip() if final_content_value else ""

        # Image:
        # If 'image' is in data, client is trying to set/change/clear it.
        # data['image'] could be an UploadedFile or None (if client sent null to clear).
        # If 'image' is NOT in data (only for updates), it means client isn't touching the image.
        final_image_exists = False
        if 'image' in data: # Client sent something for the image field
            if data['image']: # It's an UploadedFile
                final_image_exists = True
            # else: data['image'] is None (client wants to clear it) -> final_image_exists remains False
        elif not is_creating and self.instance.image: # Updating and client didn't send 'image', so keep existing
            final_image_exists = True

        if not final_content_str and not final_image_exists:
            raise serializers.ValidationError("A post must have either text content or an image (or both).")

        return data
    # ---- END OF 'validate' METHOD ---
     

     # --- Add this method ---
    def get_like_count(self, obj):
        """
        Returns the like count for the post instance.
        Accesses the 'like_count' property or calculates it.
        """
        # Check if the object is already saved (has a pk)
        # For a newly created object *before* the response, obj.likes might work if relations are set up
        # Or access the property if defined on the model
        if hasattr(obj, 'like_count'): # Check if property exists (preferred)
             # For a new object, this property should return 0
             return obj.like_count
        elif hasattr(obj, 'pk') and obj.pk is not None and hasattr(obj, 'likes'): # Fallback if property doesn't exist but object is saved
             return obj.likes.count()
        return 0 # Default for unsaved or non-likable objects
    # --- End added method ---

    def get_is_liked_by_user(self, obj):
        """ Check if the current user (from context) has liked this post. """
        user = self.context.get('request').user
        if user and user.is_authenticated:
            content_type = ContentType.objects.get_for_model(obj)
            return Like.objects.filter(
                content_type=content_type,
                object_id=obj.pk,
                user=user
            ).exists()
        return False

    def get_content_type_id(self, obj):
        """ Get the ContentType ID for the StatusPost model. """
        content_type = ContentType.objects.get_for_model(obj)
        return content_type.id

    def get_object_id(self, obj):
        """ Get the primary key of the StatusPost instance. """
        return obj.pk

    # Ensure the create method sets the author from the request context if needed
    # (This might be handled in the View, but good practice to have here too
    # if this serializer is used for creation directly)
     # ---- 3. MODIFY THE 'create' METHOD ----
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['author'] = request.user
        
        # REMOVE this check, as content is now optional, and 'validate' method handles the combined check.
        # if 'content' not in validated_data: # OLD CHECK
        #      raise serializers.ValidationError({"content": "Content field is required."}) # OLD CHECK
        
        return super().create(validated_data)
    # ---- END OF 'create' METHOD MODIFICATION ----
    
    def get_post_type(self, obj):
    # obj is the StatusPost instance here
        return obj.__class__.__name__.lower() # Should return 'statuspost'
    
    def get_comment_count(self, obj):
    # obj is the StatusPost instance
        if obj and hasattr(obj, 'pk') and obj.pk is not None:
        # Import ContentType and Comment models here if not already imported at top
        # from django.contrib.contenttypes.models import ContentType
        # from .models import Comment # Assuming Comment model is in the same app
        
            content_type = ContentType.objects.get_for_model(obj)
            return Comment.objects.filter(content_type=content_type, object_id=obj.pk).count()
        return 0


# Add these serializers

class ForumCategorySerializer(serializers.ModelSerializer):
    """Serializer for ForumCategory model."""
    class Meta:
        model = ForumCategory
        fields = ['id', 'name', 'description'] # Add 'slug' later if implemented

class ForumPostSerializer(serializers.ModelSerializer):
    """
    Serializer for ForumPost model. Includes basic author info.
    Used for listing posts and retrieving detail.
    """
    author = UserSerializer(read_only=True)
    # category_id = serializers.PrimaryKeyRelatedField(queryset=ForumCategory.objects.all(), source='category', write_only=True, required=False, allow_null=True) # For writing category link
    # group_id = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), source='group', write_only=True, required=False, allow_null=True) # For writing group link
    # We might need separate serializers for create/update if linking gets complex

    # Optionally include category name when reading list/detail
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    # Optionally include group name when reading list/detail
    group_name = serializers.CharField(source='group.name', read_only=True, allow_null=True)


    class Meta:
        model = ForumPost
        fields = [
            'id',
            'author',
            'category', # Foreign key ID on write/read (can be null)
            'group',    # Foreign key ID on write/read (can be null)
            'category_name', # Read-only name
            'group_name',    # Read-only name
            'title',
            'content',
            'created_at',
            'updated_at',
            # Add comment/like counts later
        ]
        read_only_fields = ['author', 'created_at', 'updated_at', 'category_name', 'group_name']
        # Make category/group writable by ID, but author/timestamps read-only

# Potentially needed for creating/updating posts, simpler input
class ForumPostCreateUpdateSerializer(serializers.ModelSerializer):
     class Meta:
        model = ForumPost
        fields = [
            'category', # Expecting category ID
            'group',    # Expecting group ID (only one should be provided)
            'title',
            'content',
        ]
        # Add validation later to ensure either category OR group is provided, not both/neither


# Add this serializer for Groups

class GroupSerializer(serializers.ModelSerializer):
    """
    Serializer for the Group model. Includes creator info and member count.
    """
    # Use UserSerializer for creator, make read-only as creator doesn't change
    creator = UserSerializer(read_only=True)
    # Add a count of members (read-only)
    member_count = serializers.IntegerField(source='members.count', read_only=True)

    class Meta:
        model = Group
        fields = [
            'id',
            'name',
            'description',
            'creator',      # Nested UserSerializer on read
            'member_count', # Calculated field
            'members',      # Shows list of member IDs (can customize later if needed)
            'created_at',
            # 'slug',       # Add later if using slugs
            # 'is_public',  # Add later if implementing privacy
        ]
        # Make certain fields read-only in this context
        read_only_fields = ['creator', 'member_count', 'created_at']
        # We might need a separate Create serializer if 'members' shouldn't be set directly on creation

# Optional: A simpler serializer for creating a group if needed later
# class GroupCreateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Group
#         fields = ['name', 'description'] # Only allow setting these on creation


# --- Add this new serializer ---

class LikeSerializer(serializers.ModelSerializer):
    """
    Serializer for the Like model.
    Handles serialization for creating and viewing likes.
    Uses the existing UserSerializer for author details.
    """
    # Use your existing UserSerializer for read-only user representation
    user = UserSerializer(read_only=True)

    # Fields for linking to the specific post type when CREATING a like.
    # These are write-only because we don't need to send them back when reading a like.
    # The 'source' argument maps these input fields to the actual model fields.
    status_post_id = serializers.PrimaryKeyRelatedField(
        queryset=StatusPost.objects.all(), source='status_post', write_only=True, required=False, allow_null=True
    )
    forum_post_id = serializers.PrimaryKeyRelatedField(
        queryset=ForumPost.objects.all(), source='forum_post', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Like
        fields = [
            'id',
            'user',          # Uses UserSerializer for reading (shows nested user info)
            'status_post',   # Read-only representation (shows the related post ID by default)
            'forum_post',    # Read-only representation (shows the related post ID by default)
            'created_at',

            # These fields are only used for INPUT (writing/creating):
            'status_post_id',
            'forum_post_id',
        ]
        # User is set automatically, timestamps are auto, linked posts are shown via read-only fields
        read_only_fields = ['id', 'user', 'created_at', 'status_post', 'forum_post']

    def validate(self, data):
        """
        Check that exactly one of status_post_id or forum_post_id is provided
        when creating a like via the API.
        Note: 'status_post' and 'forum_post' in 'data' here refer to the resolved
        model instances derived from status_post_id/forum_post_id inputs.
        """
        status_post_linked = data.get('status_post') # Check if status_post was linked
        forum_post_linked = data.get('forum_post')   # Check if forum_post was linked

        if not status_post_linked and not forum_post_linked:
            raise serializers.ValidationError("Input must include either 'status_post_id' or 'forum_post_id'.")
        if status_post_linked and forum_post_linked:
            raise serializers.ValidationError("Input cannot include both 'status_post_id' and 'forum_post_id'.")
        return data
    

# --- Add this new serializer ---

class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Comment model. Uses Generic Relations.
    """
    # Use your existing UserSerializer for read-only author representation
    author = UserSerializer(read_only=True)

    # Fields for identifying the parent object when CREATING a comment
    # These are write-only; they are not part of the Comment model itself.
    # We'll use these in the view to find the parent object.
    # content_type = serializers.CharField(write_only=True, help_text="Model name of the parent object (e.g., 'statuspost', 'forumpost')")
    # object_id = serializers.IntegerField(write_only=True, help_text="ID of the parent object")

    class Meta:
        model = Comment
        fields = [
            'id',
            'author',       # Nested UserSerializer for reading
            'content',
            'created_at',
            'updated_at',
            # Read-only fields related to the generic foreign key (useful for frontend)
            'content_type_id', # ID of the ContentType model instance
            'object_id',       # ID of the related object

            # Write-only fields for creation input
            # 'content_type',
            #'object_id',
        ]
        read_only_fields = [
            'id',
            'author',
            'created_at',
            'updated_at',
            'content_type_id', # Read-only representation of the GenericFK link
            'object_id',       # Read-only representation of the GenericFK link
        ]
        # Note: The 'content_type' and 'object_id' fields in the Meta.fields list
        # are overridden by the explicit field definitions above for write_only behavior.
        # We explicitly list 'content_type_id' and 'object_id' (from the model)
        # for read operations.
     
    

    # No need for a specific validate method here for the GFK link itself,
    # the view will handle resolving content_type string to ContentType object.
    # Validation for 'content' length etc. could be added if needed.

    # We will set the author and link the comment to the content_object
    # within the API view's perform_create method.


# --- Add this new Serializer for Feed Items ---

class FeedItemSerializer(serializers.Serializer):
    """
    Serializes different feed item types (StatusPost, ForumPost)
    into a common format for the /api/feed/ endpoint.
    """
    # --- Common fields expected by the frontend ---
    id = serializers.IntegerField(read_only=True) # Usually the object's pk
    author = UserSerializer(read_only=True) # Use the consistent UserSerializer
    content = serializers.CharField(read_only=True) # Assuming 'content' exists
    # image = serializers.ImageField(source='image', read_only=True, allow_null=True, use_url=True)
    image = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    like_count = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()
    content_type_id = serializers.SerializerMethodField()
    object_id = serializers.SerializerMethodField()
    post_type = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField() # Use method field for consistency
    comment_count = serializers.SerializerMethodField() # <-- ADDED FIELD

      # ---- ADD THIS METHOD ----
    def get_image(self, obj):
        # Check if the object has an 'image' attribute
        if hasattr(obj, 'image') and obj.image:
            request = self.context.get('request')
            if request:
                # Build the full URL correctly
                return request.build_absolute_uri(obj.image.url)
            # Fallback if no request in context (less ideal, might not be full URL)
            # but obj.image.url should usually be absolute or relative to MEDIA_URL
            return obj.image.url
        return None # Return None if no image attribute or no image file
    # ---- END OF METHOD ----

    def get_post_type(self, obj):
        """ Return a string identifying the type of the post object. """
        return obj.__class__.__name__.lower() # e.g., 'statuspost', 'forumpost'

    def get_title(self, obj):
        """ Get the title if it exists. """
        return getattr(obj, 'title', None) # Return None if no 'title' attribute

    def get_like_count(self, obj):
        """ Get like count using the 'likes' relation. """
        if hasattr(obj, 'likes'): # Check if the object has the 'likes' relation manager
             return obj.likes.count()
        return 0 # Default if not likable

    def get_is_liked_by_user(self, obj):
        """ Check if the current user liked this object. """
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
             return False

        user = request.user
        # Ensure the object is saved before checking likes
        if hasattr(obj, 'pk') and obj.pk is not None and hasattr(obj, 'likes'):
            content_type = ContentType.objects.get_for_model(obj)
            return Like.objects.filter(
                content_type=content_type,
                object_id=obj.pk,
                user=user
            ).exists()
        return False

    def get_content_type_id(self, obj):
        content_type = ContentType.objects.get_for_model(obj)
        return content_type.id

    def get_object_id(self, obj):
        return obj.pk

    # --- ADD THIS METHOD ---
    def get_comment_count(self, obj):
        """ Gets the count of comments for the given object (StatusPost or ForumPost). """
        if obj and hasattr(obj, 'pk') and obj.pk is not None:
            content_type = ContentType.objects.get_for_model(obj)
            # Use the Comment model directly to filter comments related to this object
            return Comment.objects.filter(content_type=content_type, object_id=obj.pk).count()
        return 0
    # --- END ADD METHOD ---

# --- Add these serializers for Private Messaging ---

class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for the Message model.
    """
    # Use UserSerializer for nested sender details (read-only)
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = [
            'id',
            'conversation', # Show the conversation ID it belongs to
            'sender',       # Nested user details
            'content',
            'timestamp',
            # 'read_at' # Add later if implementing read receipts
        ]
        # On creation via API, we only need 'content' and 'conversation' ID.
        # Sender will be set from request.user in the view.
        read_only_fields = ['id', 'sender', 'timestamp']

class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Conversation model. Includes participant details.
    """
    # Use UserSerializer for nested participant details (read-only)
    # `many=True` because participants is a ManyToManyField
    participants = UserSerializer(many=True, read_only=True)
    # Optional: Include latest message snippet or unread count later

    class Meta:
        model = Conversation
        fields = [
            'id',
            'participants', # List of nested user details
            'created_at',
            'updated_at', # Useful for sorting conversations by last activity
            # Add latest_message or unread_count fields later if needed
        ]
        # Most fields are read-only in this context, as conversations
        # might be created implicitly when the first message is sent.
        read_only_fields = ['id', 'participants', 'created_at', 'updated_at']

# --- End of Private Messaging Serializers ---

# --- Add this simple serializer for SendMessageView Input ---

class MessageCreateSerializer(serializers.Serializer):
    """Serializer for validating input when sending a message."""
    recipient_username = serializers.CharField(max_length=150, write_only=True)
    content = serializers.CharField(write_only=True)

    def validate_recipient_username(self, value):
        """Check if the recipient user exists."""
        # Need to get User model correctly here too
        User = get_user_model() # Get User model inside the method or ensure it's available globally
        if not User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Recipient user does not exist.")
        # Optional: Prevent sending messages to oneself
        # Check context if request object is passed in view
        # request = self.context.get('request')
        # if request and request.user.username == value:
        #     raise serializers.ValidationError("You cannot send a message to yourself.")
        return value

# --- End of MessageCreateSerializer ---


# --- End of new serializer ---

