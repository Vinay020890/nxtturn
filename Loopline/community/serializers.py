import json
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

# Updated model imports to include PostMedia
from .models import (
    UserProfile, Follow, StatusPost, PostMedia, ForumCategory, Group, 
    ForumPost, Comment, Like, Conversation, Message, Notification
)

User = get_user_model() 

class PostMediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    class Meta:
        model = PostMedia
        fields = ['id', 'media_type', 'file_url']
    def get_file_url(self, obj):
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url if obj.file else None

# In community/serializers.py

class UserSerializer(serializers.ModelSerializer):
    # Add a new field to get the picture URL
    picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'picture'] # Add 'picture' to fields

    def get_picture(self, obj):
        # 'obj' is the User instance.
        # We try to get the related userprofile and its picture.
        # This is safe and won't crash if a profile or picture doesn't exist.
        try:
            profile = obj.userprofile
            if profile.picture:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(profile.picture.url)
                return profile.picture.url
        except UserProfile.DoesNotExist:
            return None
        return None

# ... (Keep GenericRelatedObjectSerializer, NotificationSerializer, UserProfileSerializer, UserProfileUpdateSerializer as they are) ...
class GenericRelatedObjectSerializer(serializers.Serializer):
    type = serializers.CharField(read_only=True, source='_meta.model_name') 
    id = serializers.IntegerField(read_only=True, source='pk')
    display_text = serializers.CharField(read_only=True, source='__str__') 

class NotificationSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)
    target = GenericRelatedObjectSerializer(read_only=True, allow_null=True)
    action_object = GenericRelatedObjectSerializer(read_only=True, allow_null=True)
    class Meta:
        model = Notification
        fields = ['id', 'actor', 'verb', 'notification_type', 'target', 'action_object', 'timestamp', 'is_read']
        read_only_fields = fields 

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    skills = serializers.ListField(child=serializers.CharField(max_length=100), required=False, allow_null=True)
    interests = serializers.ListField(child=serializers.CharField(max_length=100), required=False, allow_null=True)
    is_followed_by_request_user = serializers.SerializerMethodField()
    picture = serializers.ImageField(read_only=True)
    class Meta:
        model = UserProfile
        fields = ['user', 'bio', 'location_city', 'location_state', 'college_name', 'major', 'graduation_year', 'linkedin_url', 'portfolio_url', 'skills', 'interests', 'picture', 'updated_at', 'is_followed_by_request_user']
        read_only_fields = ['user', 'updated_at', 'is_followed_by_request_user']
    def get_is_followed_by_request_user(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Follow.objects.filter(follower=request.user, following=obj.user).exists()

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    skills = serializers.ListField(child=serializers.CharField(max_length=100), required=False, allow_null=True)
    interests = serializers.ListField(child=serializers.CharField(max_length=100), required=False, allow_null=True)
    picture = serializers.ImageField(required=False, allow_null=True, use_url=False)
    class Meta:
        model = UserProfile
        fields = ['bio', 'location_city', 'location_state', 'college_name', 'major', 'graduation_year', 'linkedin_url', 'picture', 'skills', 'interests']


# --- HEAVILY REFACTORED StatusPostSerializer with UPDATE logic ---
class StatusPostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    is_liked_by_user = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    content_type_id = serializers.SerializerMethodField()
    object_id = serializers.SerializerMethodField()
    post_type = serializers.SerializerMethodField()   
    comment_count = serializers.SerializerMethodField()

    # --- Fields for Displaying and Creating/Updating Media ---
    media = PostMediaSerializer(many=True, read_only=True)
    
    # For creating/updating with new media (write-only)
    images = serializers.ListField(child=serializers.ImageField(use_url=False), write_only=True, required=False)
    videos = serializers.ListField(child=serializers.FileField(use_url=False), write_only=True, required=False)

    # --- NEW: Field for deleting existing media during an update ---
    # We expect a JSON string like "[1, 2, 5]" from the FormData
    media_to_delete = serializers.CharField(write_only=True, required=False)


    class Meta:
        model = StatusPost
        fields = [
            'id', 'author', 'content', 'created_at', 'updated_at',
            'like_count', 'is_liked_by_user', 'content_type_id', 'object_id', 
            'post_type', 'comment_count',
            # Fields for media
            'media',
            'images',
            'videos',
            'media_to_delete' # New write-only field
        ]
        read_only_fields = [
            'id', 'author', 'created_at', 'updated_at', 'like_count',
            'is_liked_by_user', 'content_type_id', 'object_id', 'post_type',
            'comment_count', 'media'
        ]

    def validate_media_to_delete(self, value):
        """
        Validate and parse the JSON string of media IDs to delete.
        """
        try:
            ids = json.loads(value)
            if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
                raise serializers.ValidationError("'media_to_delete' must be a JSON string of a list of integers.")
            return ids
        except (json.JSONDecodeError, TypeError):
            raise serializers.ValidationError("Invalid JSON format for 'media_to_delete'.")

    def validate(self, data):
        """
        Validate that on update, the post will not become empty.
        """
        if self.instance: # This is an update (PATCH/PUT)
            content = data.get('content', self.instance.content)
            new_images = data.get('images', [])
            new_videos = data.get('videos', [])
            media_to_delete_ids = data.get('media_to_delete', [])

            # Calculate what the final media count will be
            current_media_count = self.instance.media.count()
            surviving_media_count = self.instance.media.exclude(id__in=media_to_delete_ids).count()
            
            final_media_count = surviving_media_count + len(new_images) + len(new_videos)

            if not (content and content.strip()) and final_media_count == 0:
                raise serializers.ValidationError("A post cannot be empty. It must have text content or at least one media file.")
        
        else: # This is a creation (POST)
            content = data.get('content', '').strip()
            images = data.get('images', [])
            videos = data.get('videos', [])
            if not content and not images and not videos:
                raise serializers.ValidationError("A post must have text content, an image, or a video.")
        
        return data

    def create(self, validated_data):
        # ... (create method remains unchanged) ...
        request = self.context.get('request')
        images_data = validated_data.pop('images', [])
        videos_data = validated_data.pop('videos', [])
        validated_data.pop('media_to_delete', None) # Remove if present, not used in create
        
        validated_data['author'] = request.user
        post = StatusPost.objects.create(**validated_data)

        media_to_create = []
        for image_file in images_data:
            media_to_create.append(PostMedia(post=post, media_type='image', file=image_file))
        for video_file in videos_data:
            media_to_create.append(PostMedia(post=post, media_type='video', file=video_file))
        if media_to_create:
            PostMedia.objects.bulk_create(media_to_create)
        return post

    # --- NEW: Custom update method to handle gallery edits ---
    @transaction.atomic
    def update(self, instance, validated_data):
        # 1. Pop the media-related, non-model fields
        images_data = validated_data.pop('images', [])
        videos_data = validated_data.pop('videos', [])
        media_to_delete_ids = validated_data.pop('media_to_delete', [])
        
        # 2. Update the StatusPost content field if it's provided
        # The base `update` method handles this well.
        instance = super().update(instance, validated_data)

        # 3. Delete specified media items
        if media_to_delete_ids:
            # Important: ensure we only delete media belonging to this post and owned by the user
            instance.media.filter(id__in=media_to_delete_ids).delete()

        # 4. Create new media items
        media_to_create = []
        for image_file in images_data:
            media_to_create.append(PostMedia(post=instance, media_type='image', file=image_file))
        for video_file in videos_data:
            media_to_create.append(PostMedia(post=instance, media_type='video', file=video_file))
        
        if media_to_create:
            PostMedia.objects.bulk_create(media_to_create)
            
        instance.save()
        return instance

    # --- get_* methods remain unchanged ---
    def get_like_count(self, obj):
        return obj.likes.count() if hasattr(obj, 'likes') else 0

    def get_is_liked_by_user(self, obj):
        user = self.context.get('request').user
        if user and user.is_authenticated:
            content_type = ContentType.objects.get_for_model(obj)
            return Like.objects.filter(content_type=content_type, object_id=obj.pk, user=user).exists()
        return False

    def get_content_type_id(self, obj):
        return ContentType.objects.get_for_model(obj).id

    def get_object_id(self, obj):
        return obj.pk

    def get_post_type(self, obj):
        return obj.__class__.__name__.lower()
    
    def get_comment_count(self, obj):
        if obj and obj.pk:
            content_type = ContentType.objects.get_for_model(obj)
            return Comment.objects.filter(content_type=content_type, object_id=obj.pk).count()
        return 0

# --- FeedItemSerializer and other serializers remain unchanged ---
# ... (rest of your serializers.py file) ...
class FeedItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    author = UserSerializer(read_only=True)
    content = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    like_count = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()
    content_type_id = serializers.SerializerMethodField()
    object_id = serializers.SerializerMethodField()
    post_type = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    media = serializers.SerializerMethodField()
    def get_media(self, obj):
        if hasattr(obj, 'media') and obj.media.exists():
            return PostMediaSerializer(obj.media.all(), many=True, context=self.context).data
        return []
    def get_post_type(self, obj): return obj.__class__.__name__.lower()
    def get_title(self, obj): return getattr(obj, 'title', None)
    def get_like_count(self, obj): return obj.likes.count() if hasattr(obj, 'likes') else 0
    def get_is_liked_by_user(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated: return False
        if obj.pk and hasattr(obj, 'likes'):
            content_type = ContentType.objects.get_for_model(obj)
            return Like.objects.filter(content_type=content_type, object_id=obj.pk, user=request.user).exists()
        return False
    def get_content_type_id(self, obj): return ContentType.objects.get_for_model(obj).id
    def get_object_id(self, obj): return obj.pk
    def get_comment_count(self, obj):
        if obj and obj.pk:
            content_type = ContentType.objects.get_for_model(obj)
            return Comment.objects.filter(content_type=content_type, object_id=obj.pk).count()
        return 0

# ... (ForumCategorySerializer, ForumPostSerializer, GroupSerializer, etc. remain the same)
class ForumCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ForumCategory
        fields = ['id', 'name', 'description']

class ForumPostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    group_name = serializers.CharField(source='group.name', read_only=True, allow_null=True)
    class Meta:
        model = ForumPost
        fields = ['id', 'author', 'category', 'group', 'category_name', 'group_name', 'title', 'content', 'created_at', 'updated_at']
        read_only_fields = ['author', 'created_at', 'updated_at', 'category_name', 'group_name']

class GroupSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    member_count = serializers.IntegerField(source='members.count', read_only=True)
    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'creator', 'member_count', 'members', 'created_at']
        read_only_fields = ['creator', 'member_count', 'created_at']

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    parent = serializers.PrimaryKeyRelatedField(queryset=Comment.objects.all(), allow_null=True, required=False)
    like_count = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()
    comment_content_type_id = serializers.SerializerMethodField(method_name='get_comment_content_type_id_for_like')
    class Meta:
        model = Comment
        fields = ['id', 'author', 'content', 'created_at', 'updated_at', 'content_type_id', 'object_id', 'parent', 'like_count', 'is_liked_by_user', 'comment_content_type_id']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at', 'content_type_id', 'object_id', 'like_count', 'is_liked_by_user', 'comment_content_type_id']
    def get_like_count(self, obj: Comment) -> int: return obj.likes.count()
    def get_is_liked_by_user(self, obj: Comment) -> bool:
        request = self.context.get('request')
        if not request or not request.user.is_authenticated: return False
        comment_model_content_type = ContentType.objects.get_for_model(Comment)
        return Like.objects.filter(content_type=comment_model_content_type, object_id=obj.pk, user=request.user).exists()
    def get_comment_content_type_id_for_like(self, obj: Comment) -> int: return ContentType.objects.get_for_model(Comment).id

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'content', 'timestamp']
        read_only_fields = ['id', 'sender', 'timestamp']

class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'created_at', 'updated_at']
        read_only_fields = ['id', 'participants', 'created_at', 'updated_at']

class MessageCreateSerializer(serializers.Serializer):
    recipient_username = serializers.CharField(max_length=150, write_only=True)
    content = serializers.CharField(write_only=True)
    def validate_recipient_username(self, value):
        if not User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Recipient user does not exist.")
        return value