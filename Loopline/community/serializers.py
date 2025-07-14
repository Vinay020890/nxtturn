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
    ForumPost, Comment, Like, Conversation, Message, Notification, Poll, PollOption, Report
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
            # FIXED: Use .profile, which is the new 'related_name'.
            if hasattr(obj, 'profile') and obj.profile.picture and hasattr(obj.profile.picture, 'url'):
                return obj.profile.picture.url
        except UserProfile.DoesNotExist:
            # This handles the case where a User was somehow created without a profile.
            pass
        
        # Return None if no picture is found.
        return None
    
# In community/serializers.py

# In Loopline/community/serializers.py

# Replace your entire CustomRegisterSerializer with this one.
class CustomRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        validators=[validators.UniqueValidator(queryset=User.objects.all())]
    )
    email = serializers.EmailField(
        required=True,
        validators=[validators.UniqueValidator(queryset=User.objects.all())]
    )
    # FIX 1: The field is now named 'password' to match the frontend
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        # FIX 2: The validation now compares 'password' and 'password2'
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data

    @transaction.atomic
    def save(self, request):
        user = User.objects.create_user(
            username=self.validated_data['username'],
            email=self.validated_data['email'],
            # FIX 3: The user is created using the 'password' field
            password=self.validated_data['password']
        )
        # The signal will automatically create the UserProfile
        return user
    
# === PASTE THIS NEW SERIALIZER AFTER CustomRegisterSerializer ===

class ReportSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and viewing content reports.
    """
    # Display the reporter's username for read operations, but don't require it for write.
    reporter = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Report
        # These are the fields we will show in the API response
        fields = [
            'id', 
            'reporter', 
            'reason', 
            'details', 
            'status', 
            'created_at'
        ]
        # These fields are set by the server, not the client
        read_only_fields = [
            'id', 
            'reporter', 
            'status', 
            'created_at'
        ]

    def validate(self, data):
        """
        Custom validation to check for duplicate reports and existence of the content object.
        """
        request = self.context.get('request')
        view = self.context.get('view')
        
        ct_id = view.kwargs.get('ct_id')
        obj_id = view.kwargs.get('obj_id')

        # 1. Validate that the content object actually exists
        try:
            content_type = ContentType.objects.get_for_id(ct_id)
            model_class = content_type.model_class()
            # We just need to check if it exists, no need to fetch the whole object here
            if not model_class.objects.filter(pk=obj_id).exists():
                raise serializers.ValidationError("The content you are trying to report does not exist.")
        except ContentType.DoesNotExist:
            raise serializers.ValidationError("Invalid content type for report.")

        # 2. Validate that the user hasn't already reported this exact item
        if Report.objects.filter(
            reporter=request.user, 
            content_type=content_type, 
            object_id=obj_id
        ).exists():
            raise serializers.ValidationError({"detail": "You have already reported this content."})

        # 3. If reason is 'OTHER', details must be provided
        if data.get('reason') == 'OTHER' and not data.get('details', '').strip():
            raise serializers.ValidationError({"details": "Details are required when selecting 'Other' as the reason."})

        return data

    def create(self, validated_data):
        """
        Create a new Report instance, setting the reporter and content object
        from the request context and URL kwargs.
        """
        request = self.context.get('request')
        view = self.context.get('view')
        
        ct_id = view.kwargs.get('ct_id')
        obj_id = view.kwargs.get('obj_id')
        
        content_type = ContentType.objects.get_for_id(ct_id)

        # Set the server-side fields
        validated_data['reporter'] = request.user
        validated_data['content_type'] = content_type
        validated_data['object_id'] = obj_id

        return Report.objects.create(**validated_data)




class GenericRelatedObjectSerializer(serializers.Serializer):
    type = serializers.CharField(read_only=True, source='_meta.model_name') 
    id = serializers.IntegerField(read_only=True, source='pk')
    display_text = serializers.CharField(read_only=True, source='__str__')
    
    # --- THIS IS THE FIX ---
    # We add object_id to link back to parent posts from comments/replies.
    object_id = serializers.SerializerMethodField()

    def get_object_id(self, obj):
        """
        Return the 'object_id' if the object has it (like a Comment), 
        otherwise return the object's own ID as a fallback.
        """
        if hasattr(obj, 'object_id'):
            return obj.object_id
        # For top-level objects like StatusPost, its object_id is its own pk.
        return obj.pk
    # --- END OF FIX ---

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

    class SimpleGroupSerializer(serializers.ModelSerializer):
        class Meta:
            model = Group
            fields = ['id', 'name']
    
    author = UserSerializer(read_only=True)
    is_liked_by_user = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    content_type_id = serializers.SerializerMethodField()
    object_id = serializers.SerializerMethodField()
    post_type = serializers.SerializerMethodField()   
    comment_count = serializers.SerializerMethodField()
    group = SimpleGroupSerializer(read_only=True, allow_null=True)
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        source='group',
        write_only=True,
        required=False,
        allow_null=True
    )

    # --- Fields for Media ---
    media = PostMediaSerializer(many=True, read_only=True)
    images = serializers.ListField(child=serializers.FileField(use_url=False), write_only=True, required=False)
    videos = serializers.ListField(child=serializers.FileField(use_url=False), write_only=True, required=False)
    media_to_delete = serializers.CharField(write_only=True, required=False, allow_blank=True)

    # --- NEW: Fields for Polls ---
    poll = PollSerializer(read_only=True, allow_null=True)
    poll_data = serializers.CharField(write_only=True, required=False, allow_blank=True)

    is_saved = serializers.SerializerMethodField()


    
    def validate_media_to_delete(self, value):
        """
        Custom validator to parse a JSON string of IDs from FormData
        into a Python list of integers.
        """
        if not value:
            return []
        try:
            ids = json.loads(value)
            if not isinstance(ids, list):
                raise serializers.ValidationError("media_to_delete must be a JSON-formatted array.")
            return [int(id_val) for id_val in ids]
        except (json.JSONDecodeError, ValueError, TypeError):
            raise serializers.ValidationError("Invalid format. media_to_delete must be a JSON-formatted array of integers.")
    

    class Meta:
        model = StatusPost
        fields = [
            'id', 'author', 'content', 'created_at', 'updated_at', 'group', 'group_id',
            'like_count', 'is_liked_by_user', 'content_type_id', 'object_id', 
            'post_type', 'comment_count',
            # Media fields
            'media',
            'images',
            'videos',
            'media_to_delete',
            # Poll fields
            'poll',
            'poll_data',
            'is_saved'
        ]
        read_only_fields = [
            'id', 'author', 'created_at', 'updated_at', 'like_count',
            'is_liked_by_user', 'content_type_id', 'object_id', 'post_type',
            'comment_count', 'media', 'poll', 'group', 'is_saved' # Added 'poll' here
        ]

     # --- ADD THE NEW METHOD HERE ---
    # def validate_images(self, files):
    #    """
    #    Custom validation to check for unsupported image types like AVIF.
    #   """
    #    for f in files:
    #        # Check the filename extension
    #        if f.name.lower().endswith('.avif'):
    #            raise serializers.ValidationError(
    #                f"Unsupported image format: '{f.name}'. Please use JPG, PNG, or WEBP."
    #            )
    #        # You can add more checks here if needed
    #    return files
    # --- END OF NEW METHOD ---

    # In community/serializers.py -> StatusPostSerializer
# Replace your entire validate_poll_data method with this one.

    # In community/serializers.py -> StatusPostSerializer
# Replace your entire validate_poll_data method with this one.

    def validate_poll_data(self, value):
        if not value:
            return None
        try:
            data = json.loads(value)
            if not isinstance(data, dict):
                raise serializers.ValidationError("Poll data must be a JSON object.")
            if 'question' not in data or not str(data['question']).strip():
                raise serializers.ValidationError("Poll question cannot be empty.")

            # --- THIS IS THE NEW, SMARTER VALIDATION LOGIC ---
            # It now handles BOTH 'create' and 'update' scenarios.

            is_update_payload = 'options_to_update' in data or 'options_to_add' in data or 'options_to_delete' in data
            
            if is_update_payload:
                # This is an UPDATE. We don't need to validate as strictly.
                # We just check that the keys exist and are lists if provided.
                if 'options_to_update' in data and not isinstance(data['options_to_update'], list):
                    raise serializers.ValidationError("options_to_update must be a list.")
                if 'options_to_add' in data and not isinstance(data['options_to_add'], list):
                    raise serializers.ValidationError("options_to_add must be a list.")
                if 'options_to_delete' in data and not isinstance(data['options_to_delete'], list):
                    raise serializers.ValidationError("options_to_delete must be a list.")
            else:
                # This is a CREATE. It must have the simple 'options' key.
                if 'options' not in data or not isinstance(data['options'], list):
                    raise serializers.ValidationError("Poll options must be a list.")
                if len(data['options']) < 2:
                    raise serializers.ValidationError("A poll must have at least two options.")
                if any(not str(opt).strip() for opt in data['options']):
                    raise serializers.ValidationError("Poll options cannot be empty.")
            # --- END OF NEW LOGIC ---

            # Return the parsed data, structure intact
            return data
        except json.JSONDecodeError:
            raise serializers.ValidationError("Invalid JSON format for poll data.")

    def validate(self, data):
        # This is the original validation logic from your file, now with poll support
        is_update = self.instance is not None
        
        # Determine current and incoming values
        # --- THIS IS THE FIX ---
        # Get the content from the incoming data, or fall back to the existing instance's content.
        # Crucially, if that is also None, fall back to an empty string '' BEFORE trying to strip().
        content = (data.get('content', self.instance.content if is_update else None) or '').strip()
        # --- END OF FIX ---

        new_images = data.get('images', [])
        new_videos = data.get('videos', [])
        poll_data = data.get('poll_data')

        if is_update:
            # --- THIS IS THE FIX ---
            # We add a check for poll_data, just like in the 'create' validation
            media_to_delete_ids = self.validate_media_to_delete(data.get('media_to_delete'))
            surviving_media_count = self.instance.media.exclude(id__in=media_to_delete_ids).count()
            final_media_count = surviving_media_count + len(new_images) + len(new_videos)
            
            # The new, corrected rule:
            if not content and final_media_count == 0 and not poll_data:
                raise serializers.ValidationError("A post cannot be empty. It must have text content, media, or a poll.")
            # --- END OF FIX ---
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
        # --- Standard Media Handling (Unchanged) ---
        images_data = validated_data.pop('images', [])
        videos_data = validated_data.pop('videos', [])
        media_to_delete_ids = validated_data.pop('media_to_delete', [])
        
        # --- New, Advanced Poll Handling ---
        poll_data = validated_data.pop('poll_data', None)
        
        # Update the main post instance with any text content
        instance = super().update(instance, validated_data)

        # Handle media deletions and additions (Unchanged)
        if media_to_delete_ids:
            instance.media.filter(id__in=media_to_delete_ids).delete()
        
        media_to_create = []
        for image_file in images_data:
            media_to_create.append(PostMedia(post=instance, media_type='image', file=image_file))
        for video_file in videos_data:
            media_to_create.append(PostMedia(post=instance, media_type='video', file=video_file))
        if media_to_create:
            PostMedia.objects.bulk_create(media_to_create)

        # --- THIS IS THE NEW, ADVANCED POLL LOGIC ---
        if poll_data and hasattr(instance, 'poll'):
            poll = instance.poll
            
            # 1. Update the Poll Question
            poll.question = poll_data.get('question', poll.question)
            poll.save()
            
            # 2. Delete Options
            # The frontend will send a list of IDs for options to be deleted.
            options_to_delete_ids = poll_data.get('options_to_delete', [])
            if options_to_delete_ids:
                # We also delete the associated votes to keep the database clean.
                PollOption.objects.filter(id__in=options_to_delete_ids, poll=poll).delete()
            
            # 3. Update Existing Options
            # The frontend will send a list of option objects that have an 'id'.
            options_to_update = poll_data.get('options_to_update', [])
            for option_data in options_to_update:
                option_id = option_data.get('id')
                option_text = option_data.get('text')
                if option_id and option_text is not None:
                    PollOption.objects.filter(id=option_id, poll=poll).update(text=option_text)
            
            # 4. Add New Options
            # The frontend will send a list of option objects that DO NOT have an 'id'.
            options_to_add = poll_data.get('options_to_add', [])
            if options_to_add:
                new_poll_options = [
                    PollOption(poll=poll, text=option_data.get('text'))
                    for option_data in options_to_add if option_data.get('text')
                ]
                if new_poll_options:
                    PollOption.objects.bulk_create(new_poll_options)
        # --- END OF NEW POLL LOGIC ---
            
        instance.save()
        return self.Meta.model.objects.get(pk=instance.pk)
    
    
    def get_is_saved(self, obj):
        """
        Checks if the post is saved by the requesting user.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        # Uses the 'saved_by' related_name from the UserProfile model
        return obj.saved_by.filter(user=request.user).exists()
    

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

# In community/serializers.py


class GroupSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    member_count = serializers.IntegerField(source='members.count', read_only=True)
    is_member = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'creator', 'member_count', 'is_member', 'created_at', 'privacy_level']
        
        # --- THIS IS THE FIX ---
        # We remove 'privacy_level' from this list to make it writable.
        read_only_fields = ['creator', 'member_count', 'created_at']
        # --- END OF FIX ---

    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.members.filter(pk=request.user.pk).exists()
        return False

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