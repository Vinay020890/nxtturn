# community/views.py

from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.db.models import Q, Count, Value, CharField, Case, When
from django.db import transaction
from django.utils import timezone

from rest_framework import generics, status, views, serializers, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination, CursorPagination # NEW: Import CursorPagination

from .models import (
    UserProfile, Follow, StatusPost, ForumCategory, Group, ForumPost,
    Comment, Like, Conversation, Message, Notification, Poll, PollOption, PollVote, Report
)
from .serializers import (
    UserSerializer, UserProfileSerializer, UserProfileUpdateSerializer,
    StatusPostSerializer, ForumCategorySerializer, ForumPostSerializer,
    GroupSerializer, CommentSerializer, ConversationSerializer, # Removed FeedItemSerializer as it's not directly used in views
    MessageSerializer, MessageCreateSerializer, NotificationSerializer, ReportSerializer
)
from .permissions import IsOwnerOrReadOnly, IsGroupMember, IsCreatorOrReadOnly

User = get_user_model()

# ==================================
# Custom Pagination Classes
# ==================================

# Standard PageNumberPagination for less dynamic lists (e.g., search results, saved posts)
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

# NEW: CursorPagination for dynamic feeds (Main Feed, Group Feeds)
class PostCursorPagination(CursorPagination):
    page_size = 10
    ordering = '-created_at' # Crucial for cursor pagination: Must match queryset ordering
    page_size_query_param = 'page_size' # Allow client to specify page size

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
    pagination_class = PageNumberPagination # KEEP: Offset pagination is fine for a user's own post list
    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return StatusPost.objects.filter(author=user).select_related('author__profile').prefetch_related('likes', 'media', 'poll__options', 'poll__votes').order_by('-created_at')
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
    pagination_class = StandardResultsSetPagination # KEEP: Offset pagination for search results
    def get_queryset(self):
        query = self.request.query_params.get('q', None)
        if not query or not query.strip():
            return User.objects.none()

        search_filter = (
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
        
        queryset = User.objects.filter(search_filter).annotate(
            priority=Case(
                When(username__istartswith=query, then=1),
                default=2
            )
        ).distinct()

        return queryset.order_by('priority', 'username')

class ContentSearchAPIView(generics.ListAPIView):
    serializer_class = StatusPostSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination # KEEP: Offset pagination for search results

    def get_queryset(self):
        query = self.request.query_params.get('q', None)
        if not query or not query.strip():
            return StatusPost.objects.none()

        queryset = StatusPost.objects.filter(
            content__icontains=query
        ).select_related(
            'author__profile'
        ).prefetch_related(
            'media', 'likes', 'poll__options', 'poll__votes'
        ).order_by('-created_at')

        return queryset

    def get_serializer_context(self):
        return {'request': self.request}

# ==================================
# Status Post Views
# ==================================
class StatusPostListCreateView(generics.ListCreateAPIView):
    queryset = StatusPost.objects.select_related('author__profile', 'group__creator').prefetch_related('likes', 'media', 'poll__options', 'poll__votes').order_by('-created_at')
    serializer_class = StatusPostSerializer
    pagination_class = PageNumberPagination # KEEP: This view handles both list (paginated) and create (not paginated)

    def get_permissions(self):
        if self.request.method == 'POST':
            if 'group_id' in self.request.data and self.request.data['group_id']:
                return [IsAuthenticated(), IsGroupMember()]
            else:
                return [IsAuthenticated()]
        return [AllowAny()] 

    def perform_create(self, serializer):
        group = serializer.validated_data.get('group', None)
        serializer.save(author=self.request.user, group=group)
    
    def get_serializer_context(self):
        return {'request': self.request}

class StatusPostRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = StatusPost.objects.select_related('author__profile').prefetch_related('likes', 'media', 'poll__options', 'poll__votes').all()
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
    
# ==================================
# Moderation Views
# ==================================
class ReportCreateAPIView(generics.CreateAPIView):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['view'] = self
        return context
    
class PollVoteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, poll_id, option_id, format=None):
        poll = get_object_or_404(Poll, pk=poll_id)
        option = get_object_or_404(PollOption, pk=option_id, poll=poll)
        
        with transaction.atomic():
            PollVote.objects.update_or_create(
                user=request.user,
                poll=poll,
                defaults={'option': option}
            )
        
        post_instance = poll.post
        context = {'request': request}
        serializer = StatusPostSerializer(instance=post_instance, context=context)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request, poll_id, option_id, format=None):
        poll = get_object_or_404(Poll, pk=poll_id)
        PollVote.objects.filter(user=request.user, poll=poll).delete()
        post_instance = poll.post
        context = {'request': request}
        serializer = StatusPostSerializer(instance=post_instance, context=context)
        return Response(serializer.data, status=status.HTTP_200_OK)

# ==================================
# Forum Views
# ==================================
class ForumCategoryListView(generics.ListAPIView):
    queryset = ForumCategory.objects.all()
    serializer_class = ForumCategorySerializer
    permission_classes = [AllowAny]

class ForumPostListCreateView(generics.ListCreateAPIView):
    serializer_class = ForumPostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = PageNumberPagination # KEEP: Offset pagination for forum posts
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
    queryset = ForumPost.objects.select_related('author__profile', 'category', 'group').prefetch_related('likes').all()
    serializer_class = ForumPostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    lookup_field = 'pk'
    def get_serializer_context(self):
        return {'request': self.request}

# ==================================
# Group Views
# ==================================
class GroupListView(generics.ListCreateAPIView):
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination # KEEP: Offset pagination for group discovery

    def get_queryset(self):
        return Group.objects.select_related('creator__profile').prefetch_related('members').all()
    
    def get_serializer_context(self):
        """
        Ensure the request object is passed to the serializer context.
        This is crucial for fields like 'is_member' and 'is_creator'.
        """
        return {'request': self.request}

    def perform_create(self, serializer):
        group = serializer.save(creator=self.request.user)
        group.members.add(self.request.user)

    

class GroupRetrieveAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.prefetch_related('members__profile', 'creator__profile').all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsCreatorOrReadOnly]
    lookup_field = 'slug'

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
        user = request.user

        # --- THIS IS THE NEW SAFETY CHECK ---
        if group.creator == user:
            return Response(
                {"detail": "As the group creator, you must transfer ownership before leaving."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # --- END OF SAFETY CHECK ---

        if not group.members.filter(pk=user.pk).exists():
            return Response({"detail": "You are not a member."}, status=status.HTTP_400_BAD_REQUEST)
        
        group.members.remove(user)
        return Response(status=status.HTTP_204_NO_CONTENT)

class GroupPostListView(generics.ListAPIView):
    serializer_class = StatusPostSerializer
    permission_classes = [AllowAny]
    pagination_class = PostCursorPagination # NEW: Use cursor pagination here

    def get_queryset(self):
        group_id = self.kwargs.get('group_id')
        return StatusPost.objects.filter(
            group__id=group_id
        ).select_related(
            'author__profile', 
            'group'
        ).prefetch_related(
            'media', 'likes', 'poll__options', 'poll__votes'
        ).order_by('-created_at') # IMPORTANT: Must match cursor pagination ordering

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_serializer_context(self):
        return {'request': self.request}

# ==================================
# Comment Views
# ==================================
class CommentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = None # KEEP: No pagination for comments (show all)
    
    def get_queryset(self):
        content_type = get_object_or_404(ContentType, model=self.kwargs.get('content_type').lower())
        parent_object = get_object_or_404(content_type.model_class(), pk=self.kwargs.get('object_id'))
        return Comment.objects.filter(content_type=content_type, object_id=parent_object.id).select_related('author__profile').order_by('created_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['view'] = self
        return context

    def perform_create(self, serializer):
        serializer.save()

class CommentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.select_related('author__profile').all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    lookup_field = 'pk'

# ==================================
# Feed View
# ==================================
class FeedListView(generics.ListAPIView):
    serializer_class = StatusPostSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PostCursorPagination # NEW: Use cursor pagination here

    def get_queryset(self):
        user = self.request.user
        following_user_ids = list(user.following.values_list('following_id', flat=True))
        user_ids_for_feed = following_user_ids + [user.id]

        return StatusPost.objects.filter(
            author_id__in=user_ids_for_feed
        ).select_related(
            'author__profile', 
            'group'
        ).prefetch_related(
            'media', 'likes', 'poll__options', 'poll__votes'
        ).order_by('-created_at') # IMPORTANT: Must match cursor pagination ordering

    def get_serializer_context(self):
        return {'request': self.request}
    
# ==================================
# Saved Posts Views
# ==================================
class SavedPostToggleView(APIView):
    """
    Toggles saving or unsaving a post for the currently authenticated user.
    Expects a POST request to /api/community/posts/<pk>/save/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, format=None):
        post = get_object_or_404(StatusPost, pk=pk)
        profile = request.user.profile
        
        if post in profile.saved_posts.all():
            profile.saved_posts.remove(post)
        else:
            profile.saved_posts.add(post)

        serializer = StatusPostSerializer(post, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class SavedPostListView(generics.ListAPIView):
    """
    Returns a paginated list of posts saved by the currently authenticated user.
    """
    serializer_class = StatusPostSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination # KEEP: Offset pagination for saved posts

    def get_queryset(self):
        user = self.request.user
        return user.profile.saved_posts.select_related(
            'author__profile', 
            'group'
        ).prefetch_related(
            'media', 'likes', 'poll__options', 'poll__votes'
        ).order_by('-created_at') # Order by most recently saved first, or by post creation date

# ==================================
# Private Messaging Views
# ==================================
class ConversationListView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination # KEEP: Offset pagination for conversations
    def get_queryset(self):
        return self.request.user.conversations.prefetch_related('participants__profile').order_by('-updated_at')

class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination # KEEP: Offset pagination for messages within conversation
    def get_queryset(self):
        conversation = get_object_or_404(Conversation, pk=self.kwargs.get('conversation_id'), participants=self.request.user)
        return conversation.messages.select_related('sender__profile').order_by('timestamp')

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
    pagination_class = StandardResultsSetPagination # KEEP: Offset pagination for notifications
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