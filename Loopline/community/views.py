# community/views.py

from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.db.models import Q, Count, Value, CharField, Case, When
from django.db import transaction
from django.utils import timezone # Import timezone for admin actions (if not already there)

from rest_framework import generics, status, views, serializers, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from .models import (
    UserProfile, Follow, StatusPost, ForumCategory, Group, ForumPost,
    Comment, Like, Conversation, Message, Notification, Poll, PollOption, PollVote, Report
)
from .serializers import (
    UserSerializer, UserProfileSerializer, UserProfileUpdateSerializer,
    StatusPostSerializer, ForumCategorySerializer, ForumPostSerializer,
    GroupSerializer, CommentSerializer, FeedItemSerializer, ConversationSerializer,
    MessageSerializer, MessageCreateSerializer, NotificationSerializer, ReportSerializer
)
from .permissions import IsOwnerOrReadOnly, IsGroupMember





User = get_user_model()

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

# ==================================
# User Profile & Follower Views
# ==================================
class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    queryset = UserProfile.objects.select_related('user').all()
    lookup_field = 'user__username'
    lookup_url_kwarg = 'username'
    def get_serializer_class(self):
        return UserProfileUpdateSerializer if self.request.method in ['PUT', 'PATCH'] else UserProfileSerializer
    def get_permissions(self):
        return [IsAuthenticated(), IsOwnerOrReadOnly()] if self.request.method in ['PUT', 'PATCH'] else [AllowAny()]
    def get_serializer_context(self):
        return {**super().get_serializer_context(), 'request': self.request}
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_serializer = UserProfileSerializer(instance, context=self.get_serializer_context())
        return Response(response_serializer.data)

class UserPostListView(generics.ListAPIView):
    serializer_class = StatusPostSerializer
    permission_classes = [AllowAny]
    pagination_class = PageNumberPagination
    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return StatusPost.objects.filter(author=user).select_related('author__userprofile').prefetch_related('likes', 'media', 'poll__options', 'poll__votes').order_by('-created_at')
    def get_serializer_context(self):
        return {'request': self.request}

class FollowToggleView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, username, format=None):
        user_to_follow = get_object_or_404(User, username=username)
        if request.user == user_to_follow:
            return Response({"detail": "You cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)
        _, created = Follow.objects.get_or_create(follower=request.user, following=user_to_follow)
        if not created: return Response({"detail": "You are already following this user."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": f"You are now following {username}."}, status=status.HTTP_201_CREATED)
    def delete(self, request, username, format=None):
        user_to_unfollow = get_object_or_404(User, username=username)
        deleted_count, _ = Follow.objects.filter(follower=request.user, following=user_to_unfollow).delete()
        if deleted_count == 0: return Response({"detail": "You were not following this user."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

class FollowingListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    pagination_class = PageNumberPagination
    def get_queryset(self):
        target_user = get_object_or_404(User, username=self.kwargs['username'])
        return User.objects.filter(followers__follower=target_user)

class FollowersListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    pagination_class = PageNumberPagination
    def get_queryset(self):
        target_user = get_object_or_404(User, username=self.kwargs['username'])
        return User.objects.filter(following__following=target_user)

# ==================================
# Search Views
# ==================================
class UserSearchAPIView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    def get_queryset(self):
        query = self.request.query_params.get('q', None)
        if not query or not query.strip():
            return User.objects.none()

        search_filter = (
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
        
        # Annotate results with a priority score.
        # Users whose username STARTS WITH the query get a higher priority (1).
        # Others who just contain it get a lower priority (2).
        queryset = User.objects.filter(search_filter).annotate(
            priority=Case(
                When(username__istartswith=query, then=1),
                default=2
            )
        ).distinct()

        # Order by our new priority field first, then alphabetically by username.
        return queryset.order_by('priority', 'username')
    


class ContentSearchAPIView(generics.ListAPIView):
    """
    API endpoint for searching StatusPost content.
    Accepts a search query parameter 'q'.
    """
    serializer_class = StatusPostSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination # Use our existing pagination

    def get_queryset(self):
        """
        Filter posts based on the 'q' query parameter.
        """
        query = self.request.query_params.get('q', None)

        if not query or not query.strip():
            # If no query is provided, return no results.
            return StatusPost.objects.none()

        # Perform a case-insensitive search on the content of the posts.
        # This is a good starting point for content search.
        queryset = StatusPost.objects.filter(
            content__icontains=query
        ).select_related(
            'author__userprofile'
        ).prefetch_related(
            'media', 'likes', 'poll__options', 'poll__votes'
        ).order_by('-created_at') # Order by most recent first

        return queryset

    def get_serializer_context(self):
        # Pass request context to the serializer for calculating `is_liked_by_user`
        return {'request': self.request}

# ==================================
# Status Post Views
# ==================================
# In C:\Users\Vinay\Project\Loopline\community\views.py

# --- REPLACEMENT StatusPostListCreateView ---
class StatusPostListCreateView(generics.ListCreateAPIView):
    queryset = StatusPost.objects.select_related('author__userprofile', 'group__creator').prefetch_related('likes', 'media', 'poll__options', 'poll__votes').order_by('-created_at')
    serializer_class = StatusPostSerializer
    pagination_class = PageNumberPagination

    def get_permissions(self):
        """
        This method now correctly checks for 'group_id' from the frontend
        to apply the IsGroupMember permission.
        """
        if self.request.method == 'POST':
            # The frontend sends the group's ID under the key 'group_id'.
            if 'group_id' in self.request.data and self.request.data['group_id']:
                return [IsAuthenticated(), IsGroupMember()]
            else:
                return [IsAuthenticated()]
        return [AllowAny()] 

    def perform_create(self, serializer):
        """
        This method is called by DRF after the serializer is validated.
        Our serializer setup correctly takes 'group_id' from the request
        and puts the corresponding Group object into validated_data['group'].
        We then explicitly save it with the post.
        """
        group = serializer.validated_data.get('group', None)
        serializer.save(author=self.request.user, group=group)
    
    def get_serializer_context(self):
        return {'request': self.request}

class StatusPostRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = StatusPost.objects.select_related('author__userprofile').prefetch_related('likes', 'media', 'poll__options', 'poll__votes').all()
    serializer_class = StatusPostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    lookup_field = 'pk'
    def get_serializer_context(self):
        return {'request': self.request}

# ==================================
# Like View
# ==================================
class LikeToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        content_type = get_object_or_404(ContentType, pk=kwargs.get('content_type_id'))
        target_object = get_object_or_404(content_type.model_class(), pk=kwargs.get('object_id'))
        like, created = Like.objects.get_or_create(user=request.user, content_type=content_type, object_id=target_object.id)
        if not created:
            like.delete()
        return Response({"liked": created, "like_count": target_object.likes.count()}, status=status.HTTP_200_OK)
    
# === PASTE THIS NEW VIEW AND SECTION INTO community/views.py ===

# ==================================
# Moderation Views
# ==================================
class ReportCreateAPIView(generics.CreateAPIView):
    """
    API endpoint for creating a new report on a piece of content.
    The URL pattern must provide the content_type_id (ct_id) and object_id (obj_id).
    
    Example URL: /api/community/content/<ct_id>/<obj_id>/report/
    """
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        """
        Pass the request and view context to the serializer.
        This is crucial for our custom validation logic.
        """
        context = super().get_serializer_context()
        context['view'] = self
        return context
    
class PollVoteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, poll_id, option_id, format=None):
        poll = get_object_or_404(Poll, pk=poll_id)
        option = get_object_or_404(PollOption, pk=option_id, poll=poll)
        
        # Atomically create or update the vote
        with transaction.atomic():
            vote, created = PollVote.objects.update_or_create(
                user=request.user,
                poll=poll,
                defaults={'option': option}
            )
        
        # We need to return the entire updated Post object so the frontend can refresh the state.
        # This is better than just returning a success message.
        post_instance = poll.post
        context = {'request': request}
        
        # Re-serialize the parent post with the new vote data
        serializer = StatusPostSerializer(instance=post_instance, context=context)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request, poll_id, option_id, format=None):
        """
        Handles vote retraction. The option_id from the URL is not needed
        to identify the vote, but it's part of the URL structure.
        """
        poll = get_object_or_404(Poll, pk=poll_id)
        
        # Find and delete the vote for this user on this poll.
        # This is safe and won't crash if the vote doesn't exist.
        PollVote.objects.filter(user=request.user, poll=poll).delete()
        
        # Just like in post, return the full updated post object
        # so the frontend can sync its state.
        post_instance = poll.post
        context = {'request': request}
        serializer = StatusPostSerializer(instance=post_instance, context=context)
        return Response(serializer.data, status=status.HTTP_200_OK)

# ==================================
# Forum Views  <-- RESTORED
# ==================================
class ForumCategoryListView(generics.ListAPIView):
    queryset = ForumCategory.objects.all()
    serializer_class = ForumCategorySerializer
    permission_classes = [AllowAny]

class ForumPostListCreateView(generics.ListCreateAPIView):
    serializer_class = ForumPostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = PageNumberPagination
    def get_queryset(self):
        queryset = ForumPost.objects.select_related('author', 'category', 'group').prefetch_related('likes').order_by('-created_at')
        category_id = self.kwargs.get('category_id')
        group_id = self.kwargs.get('group_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        elif group_id:
            queryset = queryset.filter(group_id=group_id)
        else:
            return ForumPost.objects.none()
        return queryset
    def perform_create(self, serializer):
        category_id = self.kwargs.get('category_id')
        group_id = self.kwargs.get('group_id')
        category = get_object_or_404(ForumCategory, pk=category_id) if category_id else None
        group = get_object_or_404(Group, pk=group_id) if group_id else None
        if not category and not group:
             raise serializers.ValidationError("Missing category or group context.")
        serializer.save(author=self.request.user, category=category, group=group)
    def get_serializer_context(self):
        return {'request': self.request}

class ForumPostRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ForumPost.objects.select_related('author__userprofile', 'category', 'group').prefetch_related('likes').all()
    serializer_class = ForumPostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    lookup_field = 'pk'
    def get_serializer_context(self):
        return {'request': self.request}

# ==================================
# Group Views  <-- RESTORED
# ==================================
class GroupListView(generics.ListCreateAPIView):
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        # This queryset with select_related is crucial for performance and for our fix.
        return Group.objects.select_related('creator__userprofile').prefetch_related('members').all()

    def perform_create(self, serializer):
        # This part is correct: save the group and add the creator as a member.
        group = serializer.save(creator=self.request.user)
        group.members.add(self.request.user)

    def create(self, request, *args, **kwargs):
        """
        THIS IS THE FIX.
        We override the default 'create' behavior to ensure the response
        payload is serialized with the full GroupSerializer, not the limited
        one used for validating input.
        """
        # Step 1: Validate incoming data (uses the appropriate serializer based on get_serializer_class).
        # For a POST, this will be your internal GroupCreateSerializer if you keep it,
        # or just GroupSerializer if you simplify. We'll use the default DRF behavior.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Step 2: Use perform_create to save the object and add the member.
        self.perform_create(serializer)

        # Step 3: Re-fetch the newly created instance from the database using our optimized queryset.
        # This guarantees that the 'creator' and 'creator.userprofile' are loaded.
        new_group_instance = self.get_queryset().get(pk=serializer.instance.pk)
        
        # Step 4: Serialize the *full* instance for the response using the main GroupSerializer.
        # We explicitly use GroupSerializer here to ensure it has all fields.
        response_serializer = GroupSerializer(new_group_instance, context=self.get_serializer_context())
        
        # Step 5: Return the standard 201 CREATED response with the rich data.
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class GroupRetrieveAPIView(generics.RetrieveAPIView):
    queryset = Group.objects.prefetch_related('members__userprofile', 'creator__userprofile').all()
    serializer_class = GroupSerializer
    permission_classes = [AllowAny]
    lookup_field = 'pk'

class GroupMembershipView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, group_id, format=None):
        group = get_object_or_404(Group, pk=group_id)
        if group.members.filter(pk=request.user.pk).exists():
            return Response({"detail": "You are already a member."}, status=status.HTTP_400_BAD_REQUEST)
        group.members.add(request.user)
        return Response({"detail": f"Joined group '{group.name}'."}, status=status.HTTP_200_OK)
    def delete(self, request, group_id, format=None):
        group = get_object_or_404(Group, pk=group_id)
        if not group.members.filter(pk=request.user.pk).exists():
            return Response({"detail": "You are not a member."}, status=status.HTTP_400_BAD_REQUEST)
        group.members.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
    

# === PASTE THIS NEW VIEW INTO community/views.py ===
# (e.g., in the "Group Views" section)

# In C:\Users\Vinay\Project\Loopline\community\views.py

# --- REPLACEMENT GroupPostListView ---
# In C:\Users\Vinay\Project\Loopline\community\views.py

class GroupPostListView(generics.ListAPIView):
    """
    API endpoint for listing all StatusPosts that belong to a specific group.
    """
    serializer_class = StatusPostSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """
        This queryset is correct. It filters by group and pre-fetches related data.
        """
        group_id = self.kwargs.get('group_id')
        return StatusPost.objects.filter(
            group__id=group_id
        ).select_related(
            'author__userprofile', 
            'group'
        ).prefetch_related(
            'media', 'likes', 'poll__options', 'poll__votes'
        ).order_by('-created_at')

    # --- THIS IS THE FIX ---
    # We add a custom 'list' method to explicitly control and apply pagination.
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            # If a page exists, serialize that page's data.
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Fallback if pagination is somehow disabled or not applicable.
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    # --- END OF FIX ---

    def get_serializer_context(self):
        return {'request': self.request}

# ==================================
# Comment Views
# ==================================
# This is the NEW code
class CommentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = None
    
    def get_queryset(self):
        content_type = get_object_or_404(ContentType, model=self.kwargs.get('content_type').lower())
        parent_object = get_object_or_404(content_type.model_class(), pk=self.kwargs.get('object_id'))
        return Comment.objects.filter(content_type=content_type, object_id=parent_object.id).select_related('author__userprofile').order_by('created_at')

    def get_serializer_context(self):
        """Pass the request and view context to the serializer."""
        context = super().get_serializer_context()
        context['request'] = self.request
        context['view'] = self
        return context

    def perform_create(self, serializer):
        # All logic will now be handled in the serializer's .create() method.
        # This simplification is key for the next steps.
        serializer.save()

class CommentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.select_related('author__userprofile').all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    lookup_field = 'pk'

# ==================================
# Feed View
# ==================================
# In community/views.py

# ==================================
# Feed View (High-Performance Version)
# ==================================
class FeedListView(generics.ListAPIView):
    # Change 1: Use StatusPostSerializer directly. We've proven it works and
    # provides all the necessary data, including the nested group object.
    serializer_class = StatusPostSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        user = self.request.user
        following_user_ids = list(user.following.values_list('following_id', flat=True))
        user_ids_for_feed = following_user_ids + [user.id]

        # Change 2: The queryset now pre-fetches everything needed.
        # This makes the view simpler and more efficient.
        return StatusPost.objects.filter(
            author_id__in=user_ids_for_feed
        ).select_related(
            'author__userprofile', 
            'group'  # The crucial part for our context display
        ).prefetch_related(
            'media', 'likes', 'poll__options', 'poll__votes'
        ).order_by('-created_at')

    def get_serializer_context(self):
        # This is still needed for 'is_liked_by_user'
        return {'request': self.request}

# ==================================
# Private Messaging Views
# ==================================
class ConversationListView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    def get_queryset(self):
        return self.request.user.conversations.prefetch_related('participants__userprofile').order_by('-updated_at')

class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    def get_queryset(self):
        conversation = get_object_or_404(Conversation, pk=self.kwargs.get('conversation_id'), participants=self.request.user)
        return conversation.messages.select_related('sender__userprofile').order_by('timestamp')

class SendMessageView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        input_serializer = MessageCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        recipient = get_object_or_404(User, username=input_serializer.validated_data['recipient_username'])
        if request.user == recipient:
             return Response({"error": "You cannot send messages to yourself."}, status=status.HTTP_400_BAD_REQUEST)
        conversation = Conversation.objects.filter(participants=request.user).filter(participants=recipient).annotate(p_count=Count('participants')).filter(p_count=2).first()
        if not conversation:
             conversation = Conversation.objects.create()
             conversation.participants.add(request.user, recipient)
        message = Message.objects.create(conversation=conversation, sender=request.user, content=input_serializer.validated_data['content'])
        conversation.save()
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)

# ==================================
# Notification Views    
# ==================================
class NotificationListAPIView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    def get_queryset(self):
        return self.request.user.notifications_received.all().order_by('-timestamp')

class UnreadNotificationCountAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        return Response({'unread_count': request.user.notifications_received.filter(is_read=False).count()})

class MarkNotificationsAsReadAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        ids = request.data.get('notification_ids', [])
        updated_count = request.user.notifications_received.filter(id__in=ids, is_read=False).update(is_read=True)
        return Response({"detail": f"{updated_count} notification(s) marked as read."})

class MarkAllNotificationsAsReadAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        updated_count = request.user.notifications_received.filter(is_read=False).update(is_read=True)
        return Response({"detail": f"{updated_count} notification(s) marked as read."})