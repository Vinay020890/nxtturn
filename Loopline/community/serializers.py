import json
from rest_framework import serializers, validators
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Count
from .utils import process_mentions

# Updated model imports to include PostMedia
from .models import (
    UserProfile, Follow, StatusPost, PostMedia, ForumCategory, Group, 
    ForumPost, Comment, Like, Conversation, Message, Notification, Poll, PollOption
)

User = get_user_model() 

class PostMediaSerializer(serializers.ModelSerializer):
    # Change the 'file_url' to be a simple URLField that gets the URL directly.
    # DRF and Cloudinary will handle generating the full URL automatically.
    file_url = serializers.URLField(source='file.url', read_only=True)

    class Meta:
        model = PostMedia
        # We only need to expose the final URL, not the raw file object.
        fields = ['id', 'media_type', 'file_url']
    
class PollOptionSerializer(serializers.ModelSerializer):
    vote_count = serializers.SerializerMethodField()

    class Meta:
        model = PollOption
        fields = ['id', 'text', 'vote_count']
    
    def get_vote_count(self, obj):
        # The 'votes' related_name on PollVote is pre-counted in the PollSerializer context
        return self.context.get('vote_counts', {}).get(obj.id, 0)


class PollSerializer(serializers.ModelSerializer):
    options = PollOptionSerializer(many=True, read_only=True)
    total_votes = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()

    class Meta:
        model = Poll
        fields = ['id', 'question', 'options', 'total_votes', 'user_vote']

    def get_total_votes(self, obj):
        return obj.votes.count()

    def get_user_vote(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        vote = obj.votes.filter(user=request.user).first()
        return vote.option_id if vote else None

   # CORRECTED CODE
    def to_representation(self, instance):
        """
        Optimize vote counting to avoid N+1 queries.
        We count all votes for all options in one go.
        """
        # Get vote counts for all options of this poll, grouped by the option's ID
        vote_counts = {
            item['id']: item['count'] # <--- CORRECTED: Use the option's ID as the key
            for item in instance.options.annotate(count=Count('votes')).values('id', 'count') # <--- CORRECTED: Value is 'id', not 'option'
        }
        
        # Pass the pre-calculated counts to the child serializer via context
        self.context['vote_counts'] = vote_counts
        return super().to_representation(instance)

# In community/serializers.py

# community/serializers.py

class UserSerializer(serializers.ModelSerializer):
    picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'picture']

    def get_picture(self, obj):
        # This method safely gets the picture URL.
        # It checks for the existence of the profile and the picture field.
        try:
            if obj.userprofile and obj.userprofile.picture and hasattr(obj.userprofile.picture, 'url'):
                return obj.userprofile.picture.url
        except UserProfile.DoesNotExist:
            # This handles the case where a User was somehow created without a profile.
            pass
        
        # Return None if no picture is found.
        return None
    
# In community/serializers.py

class CustomRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        validators=[validators.UniqueValidator(queryset=User.objects.all())]
    )
    email = serializers.EmailField(
        required=True,
        validators=[validators.UniqueValidator(queryset=User.objects.all())]
    )
    password1 = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data

    @transaction.atomic
    def save(self, request):
        user = User.objects.create_user(
            username=self.validated_data['username'],
            email=self.validated_data['email'],
            password=self.validated_data['password1']
        )
        # The signal will automatically create the UserProfile
        return user

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
# In community/serializers.py

# --- HEAVILY REFACTORED StatusPostSerializer with UPDATE logic ---
# --- REPLACEMENT StatusPostSerializer with Polls and Fixes ---
class StatusPostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    is_liked_by_user = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    content_type_id = serializers.SerializerMethodField()
    object_id = serializers.SerializerMethodField()
    post_type = serializers.SerializerMethodField()   
    comment_count = serializers.SerializerMethodField()

    # --- Fields for Media ---
    media = PostMediaSerializer(many=True, read_only=True)
    images = serializers.ListField(child=serializers.ImageField(use_url=False), write_only=True, required=False)
    videos = serializers.ListField(child=serializers.FileField(use_url=False), write_only=True, required=False)
    media_to_delete = serializers.CharField(write_only=True, required=False)

    # --- NEW: Fields for Polls ---
    poll = PollSerializer(read_only=True, allow_null=True)
    poll_data = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = StatusPost
        fields = [
            'id', 'author', 'content', 'created_at', 'updated_at',
            'like_count', 'is_liked_by_user', 'content_type_id', 'object_id', 
            'post_type', 'comment_count',
            # Media fields
            'media',
            'images',
            'videos',
            'media_to_delete',
            # Poll fields
            'poll',
            'poll_data'
        ]
        read_only_fields = [
            'id', 'author', 'created_at', 'updated_at', 'like_count',
            'is_liked_by_user', 'content_type_id', 'object_id', 'post_type',
            'comment_count', 'media', 'poll' # Added 'poll' here
        ]

    def validate_poll_data(self, value):
        if not value:
            return None
        try:
            data = json.loads(value)
            if not isinstance(data, dict):
                raise serializers.ValidationError("Poll data must be a JSON object.")
            if 'question' not in data or not data['question'].strip():
                raise serializers.ValidationError("Poll question cannot be empty.")
            if 'options' not in data or not isinstance(data['options'], list):
                raise serializers.ValidationError("Poll options must be a list.")
            if len(data['options']) < 2:
                raise serializers.ValidationError("A poll must have at least two options.")
            
            options_text = [str(opt).strip() for opt in data['options']]
            if any(not opt for opt in options_text):
                raise serializers.ValidationError("Poll options cannot be empty.")
            
            data['options'] = options_text
            return data
        except json.JSONDecodeError:
            raise serializers.ValidationError("Invalid JSON format for poll data.")

    def validate(self, data):
        # This is the original validation logic from your file, now with poll support
        is_update = self.instance is not None
        
        # Determine current and incoming values
        content = data.get('content', self.instance.content if is_update else '').strip()
        new_images = data.get('images', [])
        new_videos = data.get('videos', [])
        poll_data = data.get('poll_data')

        if is_update:
            media_to_delete_ids = data.get('media_to_delete', [])
            surviving_media_count = self.instance.media.exclude(id__in=media_to_delete_ids).count()
            final_media_count = surviving_media_count + len(new_images) + len(new_videos)
            
            # On update, a post can't become empty.
            if not content and final_media_count == 0:
                # Note: We aren't checking for polls on update, as poll editing is not supported yet.
                raise serializers.ValidationError("A post cannot be empty. It must have text content or at least one media file.")
        else:
            # On create, the post must have something.
            if not content and not new_images and not new_videos and not poll_data:
                raise serializers.ValidationError("A post must have text content, media, or a poll.")
        
        return data

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        images_data = validated_data.pop('images', [])
        videos_data = validated_data.pop('videos', [])
        poll_data = validated_data.pop('poll_data', None)
        validated_data.pop('media_to_delete', None)
        
        validated_data['author'] = request.user
        post = StatusPost.objects.create(**validated_data)

        # Handle Media
        media_to_create = []
        for image_file in images_data:
            media_to_create.append(PostMedia(post=post, media_type='image', file=image_file))
        for video_file in videos_data:
            media_to_create.append(PostMedia(post=post, media_type='video', file=video_file))
        if media_to_create:
            PostMedia.objects.bulk_create(media_to_create)

        # Handle Poll Creation
        if poll_data:
            poll = Poll.objects.create(post=post, question=poll_data['question'])
            poll_options_to_create = [
                PollOption(poll=poll, text=option_text) for option_text in poll_data['options']
            ]
            PollOption.objects.bulk_create(poll_options_to_create)
        
        # --- THIS IS THE NEW LOGIC ---
        if post.content:
            process_mentions(actor=request.user, target_object=post, content_text=post.content)
        # --- END OF NEW LOGIC ---
            
        return post

    @transaction.atomic
    def update(self, instance, validated_data):
        # This is the full, original update method from your file.
        # Poll editing is NOT implemented in this step.
        images_data = validated_data.pop('images', [])
        videos_data = validated_data.pop('videos', [])
        media_to_delete_ids = validated_data.pop('media_to_delete', [])
        
        instance = super().update(instance, validated_data)

        if media_to_delete_ids:
            instance.media.filter(id__in=media_to_delete_ids).delete()

        media_to_create = []
        for image_file in images_data:
            media_to_create.append(PostMedia(post=instance, media_type='image', file=image_file))
        for video_file in videos_data:
            media_to_create.append(PostMedia(post=instance, media_type='video', file=video_file))
        
        if media_to_create:
            PostMedia.objects.bulk_create(media_to_create)
            
        instance.save()
        return instance

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

    # ... (all get_* methods remain the same)
# --- FeedItemSerializer and other serializers remain unchanged ---
# ... (rest of your serializers.py file) ...
# --- CORRECTED FeedItemSerializer with proper indentation ---
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
    media = PostMediaSerializer(many=True, read_only=True)
    poll = serializers.SerializerMethodField()

    def get_poll(self, obj):
        # Check if the object is a StatusPost and has a related poll
        if isinstance(obj, StatusPost) and hasattr(obj, 'poll'):
            # The context containing the 'request' is automatically passed down
            return PollSerializer(obj.poll, context=self.context).data
        return None
    
    # CORRECT INDENTATION: This is now a method of the class
    
    
    # CORRECT INDENTATION: This is now a method of the class
    def get_post_type(self, obj):
        return obj.__class__.__name__.lower()

    # CORRECT INDENTATION: This is now a method of the class
    def get_title(self, obj):
        return getattr(obj, 'title', None)

    # CORRECT INDENTATION: This is now a method of the class
    def get_like_count(self, obj):
        return obj.likes.count() if hasattr(obj, 'likes') else 0

    # CORRECT INDENTATION: This is now a method of the class
    def get_is_liked_by_user(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated: return False
        if obj.pk and hasattr(obj, 'likes'):
            content_type = ContentType.objects.get_for_model(obj)
            return Like.objects.filter(content_type=content_type, object_id=obj.pk, user=request.user).exists()
        return False

    # CORRECT INDENTATION: This is now a method of the class
    def get_content_type_id(self, obj):
        return ContentType.objects.get_for_model(obj).id

    # CORRECT INDENTATION: This is now a method of the class
    def get_object_id(self, obj):
        return obj.pk

    # CORRECT INDENTATION: This is now a method of the class
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

# --- Replace your existing CommentSerializer with this one ---
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

    def create(self, validated_data):
        """
        Custom create method to handle comment creation and mention processing.
        """
        # The view now provides all the context we need.
        request = self.context['request']
        view = self.context['view']
        
        content_type_model_name = view.kwargs.get('content_type').lower()
        object_id = view.kwargs.get('object_id')
        
        content_type = ContentType.objects.get(model=content_type_model_name)

        # Set the author and the generic foreign key fields
        validated_data['author'] = request.user
        validated_data['content_type'] = content_type
        validated_data['object_id'] = object_id
        
        # Create the comment instance
        comment = Comment.objects.create(**validated_data)

        # Now, process mentions in the comment's content
        if comment.content:
            process_mentions(
                actor=request.user,
                target_object=comment,
                content_text=comment.content
            )

        return comment

    def get_like_count(self, obj: Comment) -> int:
        return obj.likes.count()

    def get_is_liked_by_user(self, obj: Comment) -> bool:
        request = self.context.get('request')
        if not request or not request.user.is_authenticated: return False
        comment_model_content_type = ContentType.objects.get_for_model(Comment)
        return Like.objects.filter(content_type=comment_model_content_type, object_id=obj.pk, user=request.user).exists()

    def get_comment_content_type_id_for_like(self, obj: Comment) -> int:
        return ContentType.objects.get_for_model(Comment).id

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