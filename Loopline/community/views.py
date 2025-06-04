# community/views.py

# --- Django Imports ---
from django.apps import apps # Keep if used elsewhere (e.g., old Like view)
from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.http import Http404 # Import Http404

# --- DRF Imports ---
from rest_framework import generics, status, views, serializers
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView # Import APIView directly
from rest_framework.pagination import PageNumberPagination # Use DRF's built-in pagination

# --- Local Imports ---
from .models import (
    UserProfile, Follow, StatusPost, ForumCategory, Group, ForumPost,
    Comment, Like, Conversation, Message, Notification 
)
from .serializers import (
    UserSerializer, UserProfileSerializer, UserProfileUpdateSerializer,
    StatusPostSerializer, ForumCategorySerializer, ForumPostSerializer,
    ForumPostCreateUpdateSerializer, GroupSerializer, LikeSerializer,
    CommentSerializer, FeedItemSerializer, ConversationSerializer,
    MessageSerializer, MessageCreateSerializer, NotificationSerializer 
)
from .permissions import IsOwnerOrReadOnly


User = get_user_model()

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10  # Or your preferred default
    page_size_query_param = 'page_size'
    max_page_size = 50

# ==================================
# User Profile & Follower Views
# ==================================

class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update a user's profile (GET, PUT, PATCH).
    Lookup by username.
    """
    queryset = UserProfile.objects.select_related('user').all()
    lookup_field = 'user__username'
    lookup_url_kwarg = 'username'
    # serializer_class assignment handled by get_serializer_class

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserProfileUpdateSerializer # Handles updates
        return UserProfileSerializer # Handles retrieval (GET)

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            # Only authenticated owner can update
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        # Anyone can view profiles
        return [AllowAny()]
    
    def get_serializer_context(self):
        """
        Ensures the request object is available in the serializer context.
        """
        context = super().get_serializer_context() # Get default context
        context['request'] = self.request          # Add request object
        return context

    def update(self, request, *args, **kwargs):
    # This handles full updates (PUT requests)
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        # Use UserProfileUpdateSerializer for validating the incoming data
        serializer = UserProfileUpdateSerializer(instance, data=request.data, partial=partial, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        
        # IMPORTANT: Use UserProfileSerializer for the response to ensure full data
        response_serializer = UserProfileSerializer(instance, context=self.get_serializer_context())
        return Response(response_serializer.data)

    def partial_update(self, request, *args, **kwargs):
        # This handles partial updates (PATCH requests - like just uploading a picture)
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        # Use UserProfileUpdateSerializer for validating the incoming data
        serializer = UserProfileUpdateSerializer(instance, data=request.data, partial=partial, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        # IMPORTANT: Use UserProfileSerializer for the response to ensure full data
        response_serializer = UserProfileSerializer(instance, context=self.get_serializer_context())
        return Response(response_serializer.data)

# --- ADD THIS NEW VIEW for User's Posts ---
class UserPostListView(generics.ListAPIView):
    """
    List posts created by a specific user (GET).
    Lookup by username. Uses standard pagination.
    """
    serializer_class = StatusPostSerializer
    permission_classes = [AllowAny] # Anyone can view any user's posts
    pagination_class = PageNumberPagination # Use DRF's standard pagination

    def get_queryset(self):
        """ Filter posts by the username provided in the URL. """
        username = self.kwargs.get('username')
        # Ensure user exists before filtering posts
        user = get_object_or_404(User, username=username)
        # Filter posts by the found user's ID for efficiency
        return StatusPost.objects.filter(
            author=user
        ).select_related('author__userprofile').prefetch_related('likes').order_by('-created_at') # Use author__userprofile

    def get_serializer_context(self):
        """ Pass request context to serializer (for is_liked_by_user). """
        return {'request': self.request}
# --- End of UserPostListView ---


class FollowToggleView(APIView): # Use APIView directly
    """
    Follow (POST) or unfollow (DELETE) another user.
    URL: /api/users/{username}/follow/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, username, format=None):
        user_to_follow = get_object_or_404(User, username=username)
        follower = request.user
        if follower == user_to_follow:
            return Response({"detail": "You cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)
        # Use get_or_create for atomicity (though less likely needed here than likes)
        follow_instance, created = Follow.objects.get_or_create(follower=follower, following=user_to_follow)
        if not created:
            return Response({"detail": "You are already following this user."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": f"You are now following {username}."}, status=status.HTTP_201_CREATED)

    def delete(self, request, username, format=None):
        user_to_unfollow = get_object_or_404(User, username=username)
        follower = request.user
        if follower == user_to_unfollow:
             # Not strictly necessary as filter won't find it, but good check
            return Response({"detail": "You cannot unfollow yourself."}, status=status.HTTP_400_BAD_REQUEST)
        # Use filter().delete() for simplicity and efficiency
        deleted_count, _ = Follow.objects.filter(follower=follower, following=user_to_unfollow).delete()
        if deleted_count == 0:
            return Response({"detail": "You were not following this user."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowingListView(generics.ListAPIView):
    """ List users that a specific user is following (GET). """
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    pagination_class = PageNumberPagination # Add pagination

    def get_queryset(self):
        target_username = self.kwargs['username']
        target_user = get_object_or_404(User, username=target_username)
        # Directly query Users followed by target_user
        return User.objects.filter(followers__follower=target_user) # Use related name 'followers'


class FollowersListView(generics.ListAPIView):
    """ List users who are following a specific user (GET). """
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    pagination_class = PageNumberPagination # Add pagination

    def get_queryset(self):
        target_username = self.kwargs['username']
        target_user = get_object_or_404(User, username=target_username)
         # Directly query Users following target_user
        return User.objects.filter(following__following=target_user) # Use related name 'following'


# ==================================
# Status Post Views
# ==================================

class StatusPostListCreateView(generics.ListCreateAPIView):
    """
    List *all* status posts (GET) or create a new one (POST).
    Use UserPostListView for user-specific posts.
    """
    # Use select_related/prefetch_related here too
    queryset = StatusPost.objects.select_related('author__profile').prefetch_related('likes').order_by('-created_at')
    serializer_class = StatusPostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly] # Read all, create if authenticated
    pagination_class = PageNumberPagination # Add pagination

    # No longer need get_queryset filtering by username here, as UserPostListView handles that.
    # def get_queryset(self): ...

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_context(self):
        """ Pass request context to serializer (for is_liked_by_user). """
        return {'request': self.request}


class StatusPostRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """ Retrieve, update, or delete a single StatusPost (GET, PUT, PATCH, DELETE). """
    queryset = StatusPost.objects.select_related('author__profile').prefetch_related('likes').all()
    serializer_class = StatusPostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly] # Read if public/auth, write if owner
    lookup_field = 'pk'

    def get_serializer_context(self):
        """ Pass request context to serializer (for is_liked_by_user). """
        return {'request': self.request}

# ==================================
# Like View (Corrected Version)
# ==================================

# --- REPLACE the old LikeToggleAPIView with this one ---
class LikeToggleAPIView(APIView): # Use APIView directly
    """
    Toggle a like on a compatible object (e.g., StatusPost, ForumPost).
    Uses POST for both liking and unliking.
    URL: /api/content/<int:content_type_id>/<int:object_id>/like/
    Returns {"liked": bool, "like_count": int}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        content_type_id = kwargs.get('content_type_id')
        object_id = kwargs.get('object_id')
        user = request.user

        # Validate ContentType ID and get the corresponding model
        try:
            content_type = ContentType.objects.get_for_id(content_type_id)
            model_class = content_type.model_class()
            # Optional: Check if model_class is one you allow liking
            # if model_class not in [StatusPost, ForumPost]:
            #     return Response({"error": "Liking not supported for this content type"}, status=status.HTTP_400_BAD_REQUEST)
        except ContentType.DoesNotExist:
            return Response({"error": "Invalid content type ID"}, status=status.HTTP_404_NOT_FOUND)

        # Get the target object instance
        target_object = get_object_or_404(model_class, pk=object_id)

        # Use get_or_create to handle like/unlike atomically
        like, created = Like.objects.get_or_create(
            user=user,
            content_type=content_type,
            object_id=object_id # Use object_id directly
        )

        liked = False
        if created:
            # Like was just created
            liked = True
        else:
            # Like already existed, so delete it (unlike)
            like.delete()
            liked = False

        # Get the updated like count from the target object's 'likes' relation
        # Assumes target_object has a GenericRelation named 'likes'
        like_count = target_object.likes.count()

        # Return the current status and count
        return Response({
            "liked": liked,
            "like_count": like_count
        }, status=status.HTTP_200_OK)
# --- End of CORRECTED LikeToggleAPIView ---


# ==================================
# Forum Views
# ==================================

class ForumCategoryListView(generics.ListAPIView):
    """ List all forum categories (GET). """
    queryset = ForumCategory.objects.all()
    serializer_class = ForumCategorySerializer
    permission_classes = [AllowAny]
    # pagination_class = PageNumberPagination # Optional: Paginate categories?


class ForumPostListCreateView(generics.ListCreateAPIView):
    """ List posts in a category/group (GET) or create one (POST). """
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = PageNumberPagination # Add pagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ForumPostCreateUpdateSerializer
        return ForumPostSerializer # Use for GET list

    def get_queryset(self):
        queryset = ForumPost.objects.select_related(
            'author__profile', 'category', 'group'
        ).prefetch_related('likes').order_by('-created_at') # Add prefetch_related

        category_id = self.kwargs.get('category_id')
        group_id = self.kwargs.get('group_id')

        if category_id:
            # Ensure category exists before filtering
            get_object_or_404(ForumCategory, pk=category_id)
            queryset = queryset.filter(category_id=category_id)
        elif group_id:
             # Ensure group exists before filtering
            get_object_or_404(Group, pk=group_id)
            queryset = queryset.filter(group_id=group_id)
        else:
            # If neither specified, perhaps raise error or return none?
            # Depending on URL setup, this might indicate an issue.
            # For now, return empty if no context provided.
            return ForumPost.objects.none()
        return queryset

    def perform_create(self, serializer):
        category_id = self.kwargs.get('category_id')
        group_id = self.kwargs.get('group_id')
        category = None
        group = None

        if category_id:
            category = get_object_or_404(ForumCategory, pk=category_id)
        elif group_id:
            group = get_object_or_404(Group, pk=group_id)
        else:
            # Should not happen with correct URL patterns for POST
             raise serializers.ValidationError("Missing category or group context for post creation.")

        serializer.save(author=self.request.user, category=category, group=group)

    def get_serializer_context(self):
        """ Pass request context to serializer (for is_liked_by_user). """
        return {'request': self.request}


class ForumPostRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """ Retrieve, update, or delete a single ForumPost (GET, PUT, PATCH, DELETE). """
    queryset = ForumPost.objects.select_related(
        'author__profile', 'category', 'group'
    ).prefetch_related('likes').all() # Add prefetch_related
    serializer_class = ForumPostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    lookup_field = 'pk'

    def get_serializer_context(self):
        """ Pass request context to serializer (for is_liked_by_user). """
        return {'request': self.request}

# ==================================
# Group Views
# ==================================

class GroupListView(generics.ListAPIView):
    """ List all Groups (GET). """
    queryset = Group.objects.prefetch_related('creator__profile', 'members').all() # Optimize members
    serializer_class = GroupSerializer
    permission_classes = [AllowAny]
    pagination_class = PageNumberPagination # Add pagination


class GroupRetrieveAPIView(generics.RetrieveAPIView):
    """ Retrieve details of a single Group (GET). """
    queryset = Group.objects.prefetch_related('members__profile', 'creator__profile').all() # Optimize further
    serializer_class = GroupSerializer
    permission_classes = [AllowAny]
    lookup_field = 'pk'


class GroupMembershipView(APIView): # Use APIView directly
    """ Join (POST) or leave (DELETE) a group. """
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id, format=None):
        group = get_object_or_404(Group, pk=group_id)
        user = request.user
        if group.members.filter(pk=user.pk).exists():
            return Response({"detail": "You are already a member."}, status=status.HTTP_400_BAD_REQUEST)
        group.members.add(user)
        return Response({"detail": f"Joined group '{group.name}'."}, status=status.HTTP_200_OK)

    def delete(self, request, group_id, format=None):
        group = get_object_or_404(Group, pk=group_id)
        user = request.user
        if not group.members.filter(pk=user.pk).exists():
            return Response({"detail": "You are not a member."}, status=status.HTTP_400_BAD_REQUEST)
        group.members.remove(user)
        # 204 No Content preferred for successful DELETE with no body
        return Response(status=status.HTTP_204_NO_CONTENT)


# ==================================
# Comment Views
# ==================================

class CommentListCreateAPIView(generics.ListCreateAPIView):
    """ List comments for an object (GET) or create one (POST). """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = None  # <-- EXPLICITLY SET TO NONE

    def get_queryset(self):
        content_type_str = self.kwargs.get('content_type')
        object_id = self.kwargs.get('object_id')

        if not content_type_str or not object_id:
             raise Http404("Missing content type or object ID in URL.")

        try:
            content_type = ContentType.objects.get(model=content_type_str.lower())
            # Optional: Check if model is commentable
            # model_class = content_type.model_class()
            # if model_class not in [StatusPost, ForumPost]: ...
        except ContentType.DoesNotExist:
             raise Http404("Invalid content type specified.")

        # Check if parent object actually exists (good practice)
        parent_model = content_type.model_class()
        get_object_or_404(parent_model, pk=object_id) # Raises 404 if parent doesn't exist

        queryset = Comment.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).select_related('author__userprofile').order_by('created_at') # Order comments chronologically

         # --- ADD DEBUG PRINT HERE ---
        print(f"DEBUG: QuerySet for comments ({content_type_str}/{object_id}): {queryset}")
        # You can also try printing the actual list to force evaluation:
        # try:
        #     print(f"DEBUG: QuerySet as list: {list(queryset)}")
        # except Exception as e:
        #     print(f"DEBUG: Error converting queryset to list: {e}")
        # --- END DEBUG PRINT ---
        
        return queryset

    def perform_create(self, serializer):
        content_type_str = self.kwargs.get('content_type')
        object_id = self.kwargs.get('object_id')

         
        try:
            content_type = ContentType.objects.get(model=content_type_str.lower())
            # Check parent existence again before saving (optional but safer)
            parent_model = content_type.model_class()
            get_object_or_404(parent_model, pk=object_id)
        except ContentType.DoesNotExist:
             raise serializers.ValidationError("Invalid content_type specified in URL.")
        except parent_model.DoesNotExist:
              raise serializers.ValidationError("Parent object does not exist.")
        
        

        serializer.save(
            author=self.request.user,
            content_type=content_type,
            object_id=object_id
        )


class CommentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """ Retrieve, update, or delete a single comment (GET, PUT, PATCH, DELETE). """
    queryset = Comment.objects.select_related('author__userprofile').all() # Optimize author fetch
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    lookup_field = 'pk'


# ==================================
# Feed View
# ==================================

class FeedListView(APIView): # Use APIView directly
    """
    Personalized feed combining StatusPosts (followed users + self)
    and ForumPosts (joined groups). Paginated. (GET)
    """
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination # Use DRF's standard pagination

    def get(self, request, format=None):
        user = request.user

        # Get IDs of users the current user follows (including self for simplicity later)
        following_user_ids = list(Follow.objects.filter(follower=user).values_list('following_id', flat=True))
        # Ensure user's own posts are included
        user_ids_for_status_posts = following_user_ids + [user.id]

        # Get IDs of groups the current user is a member of
        joined_group_ids = list(user.joined_groups.values_list('id', flat=True)) # Access via related_name

        # Fetch relevant StatusPosts
        status_posts = StatusPost.objects.filter(
            author_id__in=user_ids_for_status_posts
        ).select_related('author__userprofile').prefetch_related('likes') # Include likes prefetch

        # Fetch relevant ForumPosts
        group_posts = ForumPost.objects.filter(
            group_id__in=joined_group_ids
        ).select_related('author__userprofile', 'group', 'category').prefetch_related('likes') # Include likes prefetch

        # Combine the querysets efficiently using union (requires compatible fields/annotations)
        # Or, fetch separately and sort in Python if union is complex
        # Python sorting approach:
        status_posts_list = list(status_posts)
        group_posts_list = list(group_posts)
        combined_feed_items = status_posts_list + group_posts_list

        # Sort the combined list by 'created_at' date, newest first
        # Ensure both models have 'created_at'
        sorted_feed_items = sorted(
            combined_feed_items,
            key=lambda item: item.created_at,
            reverse=True
        )

        # Paginate the sorted list
        paginator = self.pagination_class()
        paginated_list = paginator.paginate_queryset(sorted_feed_items, request, view=self)

        # Serialize the paginated list using the dedicated FeedItemSerializer
        # Ensure FeedItemSerializer handles both StatusPost and ForumPost objects
        serializer = FeedItemSerializer(paginated_list, many=True, context={'request': request}) # Pass context

        # Return the paginated response
        return paginator.get_paginated_response(serializer.data)


# ==================================
# Private Messaging Views
# ==================================

class ConversationListView(generics.ListAPIView):
    """ List conversations the current user participates in (GET). """
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination # Add pagination

    def get_queryset(self):
        user = self.request.user
        # Order by 'updated_at' (should be on Conversation model)
        return user.conversations.prefetch_related('participants__profile').order_by('-updated_at')


class MessageListView(generics.ListAPIView):
    """ List messages within a specific conversation (GET). """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination # Add pagination (maybe reverse order?)

    def get_queryset(self):
        user = self.request.user
        conversation_id = self.kwargs.get('conversation_id')
        # Ensure user is part of the conversation
        conversation = get_object_or_404(
            Conversation.objects.prefetch_related('participants'),
            pk=conversation_id,
            participants=user
        )
        # Order messages chronologically (oldest first - typical for chat)
        # Add prefetch_related for sender profile
        return conversation.messages.select_related('sender__profile').order_by('timestamp')

    # POST method could be added here or in Conversation detail view to create message
    # For now, SendMessageView handles creation


class SendMessageView(APIView): # Use APIView directly
    """ Send a private message to another user (POST). """
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        # Use the MessageCreateSerializer for input validation
        input_serializer = MessageCreateSerializer(data=request.data, context={'request': request})
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = input_serializer.validated_data
        recipient_username = validated_data['recipient_username']
        content = validated_data['content']
        sender = request.user

        try:
            recipient = User.objects.get(username=recipient_username)
        except User.DoesNotExist:
             # Should be caught by serializer, but good backup check
             raise Http404("Recipient user not found.")

        if sender == recipient:
             return Response({"error": "You cannot send messages to yourself."}, status=status.HTTP_400_BAD_REQUEST)

        # Find or create the 1-on-1 conversation
        conversation = Conversation.objects.annotate(
            num_participants=Count('participants')
        ).filter(
            participants=sender, num_participants=2 # Filter conversations with sender and exactly 2 people
        ).filter(
             participants=recipient # Check if the recipient is the other person
        ).first()

        if not conversation:
             conversation = Conversation.objects.create()
             conversation.participants.add(sender, recipient)

        # Create the message
        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            content=content
        )

        # Trigger conversation update (e.g., update updated_at timestamp)
        conversation.save()

        # Return the created message data
        output_serializer = MessageSerializer(message, context={'request': request}) # Pass context
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
# ==================================
# Notification Views    

# ---- ADD THE NEW NotificationListAPIView HERE ----
class NotificationListAPIView(ListAPIView):
    """
    API view to list notifications for the authenticated user.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination # Or use global default if preferred

    def get_queryset(self):
        user = self.request.user
        return Notification.objects.filter(recipient=user).order_by('-timestamp')

    # Optional get_serializer_context method if needed
    # def get_serializer_context(self):
    #     return {'request': self.request}
# ---- END OF NotificationListAPIView ----

# You can add more notification-related views later below this,
# for example, views to mark notifications as read.

class UnreadNotificationCountAPIView(APIView):
    """
    API view to get the count of unread notifications for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        unread_count = Notification.objects.filter(recipient=user, is_read=False).count()
        return Response({'unread_count': unread_count})
    
    
class MarkNotificationsAsReadAPIView(APIView):
    """
    API view to mark a list of notifications as read for the authenticated user.
    Expects a POST request with a JSON body like: {"notification_ids": [1, 2, 3]}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user = request.user
        notification_ids = request.data.get('notification_ids', [])

        if not isinstance(notification_ids, list):
            return Response(
                {"detail": "Invalid data format. 'notification_ids' must be a list."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not notification_ids: # If empty list is sent
            return Response(
                {"detail": "No notification IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Filter for notifications that belong to the user and are in the provided list
        notifications_to_update = Notification.objects.filter(
            recipient=user, 
            id__in=notification_ids,
            is_read=False # Only update those that are currently unread
        )
        
        updated_count = notifications_to_update.update(is_read=True)

        return Response(
            {"detail": f"{updated_count} notification(s) marked as read."},
            status=status.HTTP_200_OK
        )
        

# In Loopline/community/views.py
# ... (after MarkNotificationsAsReadAPIView or with other notification views)

class MarkAllNotificationsAsReadAPIView(APIView):
    """
    API view to mark all unread notifications for the authenticated user as read.
    Accepts a POST request.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user = request.user
        
        # Find all unread notifications for the user
        unread_notifications = Notification.objects.filter(recipient=user, is_read=False)
        
        if not unread_notifications.exists():
            return Response(
                {"detail": "No unread notifications to mark as read."},
                status=status.HTTP_200_OK # Or HTTP_204_NO_CONTENT if you prefer
            )

        updated_count = unread_notifications.update(is_read=True)

        return Response(
            {"detail": f"{updated_count} notification(s) marked as read."},
            status=status.HTTP_200_OK
        )