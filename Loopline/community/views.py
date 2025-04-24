from django.db.models import Q, Count
# from django.contrib.auth.models import User
from django.contrib.auth import get_user_model 
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, views, serializers
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
# from rest_framework.views import APIView
from django.contrib.contenttypes.models import ContentType
from .models import UserProfile, Follow, StatusPost, ForumCategory, Group, ForumPost, Comment, Like, Conversation, Message # Ensure all models are imported
from .serializers import UserSerializer, UserProfileSerializer, UserProfileUpdateSerializer, StatusPostSerializer, ForumCategorySerializer, ForumPostSerializer, ForumPostCreateUpdateSerializer, GroupSerializer, LikeSerializer, CommentSerializer, FeedItemSerializer, ConversationSerializer, MessageSerializer, MessageCreateSerializer # Ensure all serializers are imported
from .permissions import IsOwnerOrReadOnly
from rest_framework.pagination import PageNumberPagination


User = get_user_model()

# Create your views here.

class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    """
    API view to retrieve or update a user's profile.
    Uses the username from the URL to look up the user.
    """
    queryset = UserProfile.objects.select_related('user').all()
    lookup_field = 'user__username'
    lookup_url_kwarg = 'username'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserProfileUpdateSerializer
        return UserProfileSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return [AllowAny()]


class FollowToggleView(views.APIView):
    """
    API view to allow an authenticated user to follow (POST)
    or unfollow (DELETE) another user.
    Uses the URL: /api/users/{username}/follow/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, username, format=None):
        user_to_follow = get_object_or_404(User, username=username)
        follower = request.user
        if follower == user_to_follow:
            return Response({"detail": "You cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)
        if Follow.objects.filter(follower=follower, following=user_to_follow).exists():
            return Response({"detail": "You are already following this user."}, status=status.HTTP_400_BAD_REQUEST)
        Follow.objects.create(follower=follower, following=user_to_follow)
        return Response({"detail": f"You are now following {username}."}, status=status.HTTP_201_CREATED)

    def delete(self, request, username, format=None):
        user_to_unfollow = get_object_or_404(User, username=username)
        follower = request.user
        if follower == user_to_unfollow:
            return Response({"detail": "You cannot unfollow yourself."}, status=status.HTTP_400_BAD_REQUEST)

        follow_instance = Follow.objects.filter(follower=follower, following=user_to_unfollow).first()
        if not follow_instance:
            return Response({"detail": "You are not following this user."}, status=status.HTTP_400_BAD_REQUEST)

        follow_instance.delete()
        # Return standard 204 No Content for successful DELETE
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowingListView(generics.ListAPIView):
    """
    API view to list users that a specific user is following.
    Uses URL like /api/users/{username}/following/
    """
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        target_username = self.kwargs['username']
        target_user = get_object_or_404(User, username=target_username)
        following_ids = Follow.objects.filter(follower=target_user).values_list('following_id', flat=True)
        return User.objects.filter(id__in=following_ids)


class FollowersListView(generics.ListAPIView):
    """
    API view to list users who are following a specific user.
    Uses URL like /api/users/{username}/followers/
    """
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        target_username = self.kwargs['username']
        target_user = get_object_or_404(User, username=target_username)
        follower_ids = Follow.objects.filter(following=target_user).values_list('follower_id', flat=True)
        return User.objects.filter(id__in=follower_ids)


class StatusPostListCreateView(generics.ListCreateAPIView):
    """
    API view to list status posts (GET) or create a new one (POST).
    - GET (list): Filters posts by the username specified in the URL if present.
    - POST (create): Creates a post for the currently authenticated user.
    """
    serializer_class = StatusPostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = StatusPost.objects.select_related('author__userprofile').all()
        username = self.kwargs.get('username') # Get username from URL if present (e.g., from user-post-list URL)
        if username:
            queryset = queryset.filter(author__username=username)
        # If no username (e.g., accessing /api/posts/ directly via GET), this returns ALL posts. Refine later.
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


# --- Add this view for single StatusPost operations ---

class StatusPostRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view to retrieve (GET), update (PUT/PATCH), or delete (DELETE)
    a single StatusPost instance by its primary key (ID).
    Ensures only the author can update or delete their post.
    Example URL: /api/posts/5/ (where 5 is the StatusPost ID)
    """
    queryset = StatusPost.objects.select_related('author__userprofile').all()
    serializer_class = StatusPostSerializer
    # Apply permissions: Must be authenticated, and must be owner for update/delete
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = 'pk' # Explicitly state we are looking up by primary key (default, but good practice)

    # We rely on the IsOwnerOrReadOnly permission to check 'author' field
    # Generic view handles GET, PUT, PATCH, DELETE logic based on pk.

# --- End of StatusPostRetrieveUpdateDestroyView ---


class ForumCategoryListView(generics.ListAPIView):
    """
    API view to list all forum categories.
    Uses URL like /api/forums/
    """
    queryset = ForumCategory.objects.all()
    serializer_class = ForumCategorySerializer
    permission_classes = [AllowAny]


# Modify this existing view

class ForumPostListCreateView(generics.ListCreateAPIView):
    """
    API view to list posts within a specific category OR group (GET)
    or create a new post within that category OR group (POST).
    Uses URL like /api/forums/{category_id}/posts/ OR /api/groups/{group_id}/posts/
    """
    # Keep using ForumPostSerializer by default for GET list
    serializer_class = ForumPostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        # Still use the simpler serializer for POST requests
        if self.request.method == 'POST':
            return ForumPostCreateUpdateSerializer
        return ForumPostSerializer

    def get_queryset(self):
        """
        Filter posts by EITHER category_id OR group_id from the URL.
        """
        queryset = ForumPost.objects.select_related('author__userprofile', 'category', 'group').all()
        category_id = self.kwargs.get('category_id')
        group_id = self.kwargs.get('group_id') # Get group_id as well

        if category_id:
            queryset = queryset.filter(category_id=category_id)
        elif group_id: # Add condition for group_id
            queryset = queryset.filter(group_id=group_id)
        else:
            # If neither is specified on GET, return nothing (or maybe all posts later?)
             return ForumPost.objects.none()
        return queryset

    def perform_create(self, serializer):
        """
        Set author and EITHER category OR group based on the URL used.
        """
        category_id = self.kwargs.get('category_id')
        group_id = self.kwargs.get('group_id') # Get group_id as well
        category = None
        group = None

        if category_id:
            category = get_object_or_404(ForumCategory, pk=category_id)
        elif group_id: # Add condition for group_id
            group = get_object_or_404(Group, pk=group_id)
        else:
            # This case shouldn't happen if URL patterns are set up correctly for POST
            # (i.e., POST should only go to /forums/.../posts/ or /groups/.../posts/)
            # You could raise a validation error here if needed.
            pass

        # Pass author, and EITHER category or group (the other will be None)
        serializer.save(author=self.request.user, category=category, group=group)


# --- Add this view for single ForumPost operations ---

class ForumPostRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view to retrieve (GET), update (PUT/PATCH), or delete (DELETE)
    a single ForumPost instance by its primary key (ID).
    Ensures only the author can update or delete their post.
    Example URL: /api/forumposts/5/ (where 5 is the ForumPost ID)
    """
    # Optimize query by prefetching related author/profile, category, group
    queryset = ForumPost.objects.select_related(
        'author__userprofile', 'category', 'group'
    ).all()
    serializer_class = ForumPostSerializer # Use the main serializer for GET, PUT, PATCH
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = 'pk'

    # We rely on the IsOwnerOrReadOnly permission to check the 'author' field.
    # Generic view handles GET, PUT, PATCH, DELETE logic based on pk.

    # Optional: If you want to use a different serializer for Update (PUT/PATCH)
    # you can override get_serializer_class like this:
    # def get_serializer_class(self):
    #     if self.request.method in ['PUT', 'PATCH']:
    #         # Choose the appropriate serializer for updates
    #         return ForumPostCreateUpdateSerializer # Or keep ForumPostSerializer
    #     return ForumPostSerializer # Default for GET

# --- End of ForumPostRetrieveUpdateDestroyView ---

# Add this view for Groups

class GroupListView(generics.ListAPIView):
    """
    API view to list all Groups.
    (Later, might filter for public groups only if privacy is added)
    Uses URL like /api/groups/
    """
    # For now, list all groups. Add filtering later if needed.
    queryset = Group.objects.prefetch_related('creator', 'members').all() # Optimize queries
    serializer_class = GroupSerializer
    permission_classes = [AllowAny] # Anyone can list groups for now


# --- Add this view for single Group retrieval ---

class GroupRetrieveAPIView(generics.RetrieveAPIView):
    """
    API view to retrieve (GET) the details of a single Group instance
    by its primary key (ID).
    Example URL: /api/groups/1/ (where 1 is the Group ID)
    """
    # Optimize query by prefetching members and creator details
    queryset = Group.objects.prefetch_related('members', 'creator__userprofile').all()
    serializer_class = GroupSerializer
    permission_classes = [AllowAny] # Anyone can view group details for now
    lookup_field = 'pk' # Use the primary key from the URL

# --- End of GroupRetrieveAPIView ---


# Add this view for Group Membership

class GroupMembershipView(views.APIView):
    """
    API view to allow an authenticated user to join (POST)
    or leave (DELETE) a specific group.
    Uses URL like /api/groups/{group_id}/membership/
    """
    permission_classes = [IsAuthenticated] # Must be logged in to join/leave

    def post(self, request, group_id, format=None):
        """Handles joining a group."""
        group = get_object_or_404(Group, pk=group_id)
        user = request.user

        # Check if user is already a member
        if group.members.filter(pk=user.pk).exists():
            return Response(
                {"detail": "You are already a member of this group."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Add the user to the group's members
        group.members.add(user)
        return Response(
            {"detail": f"You have joined the group '{group.name}'."},
            status=status.HTTP_200_OK # Or 201 Created, 200 is fine too
        )

    def delete(self, request, group_id, format=None):
        """Handles leaving a group."""
        group = get_object_or_404(Group, pk=group_id)
        user = request.user

        # Check if user is actually a member
        if not group.members.filter(pk=user.pk).exists():
            return Response(
                {"detail": "You are not a member of this group."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Remove the user from the group's members
        group.members.remove(user)
        return Response(
            {"detail": f"You have left the group '{group.name}'."},
            status=status.HTTP_204_NO_CONTENT
        )
    

# --- Add this new View ---

class LikeToggleAPIView(views.APIView):
    """
    API view to allow users to like (POST) or unlike (DELETE)
    a specific StatusPost or ForumPost.
    Expects 'content_type' (e.g., 'statuspost' or 'forumpost') and 'object_id'
    as URL parameters.
    """
    permission_classes = [IsAuthenticated] # Only logged-in users can like/unlike
    serializer_class = LikeSerializer # Use the serializer we created

    def get_target_object(self, content_type_str, object_id):
        """Helper method to find the actual post object being liked/unliked."""
        if content_type_str == 'statuspost':
            model = StatusPost
        elif content_type_str == 'forumpost':
            model = ForumPost
        # Add more 'elif' blocks here if you add other likeable models later
        else:
            return None # Invalid content type string

        try:
            # Find the specific post instance by its ID
            return model.objects.get(pk=object_id)
        except model.DoesNotExist:
            return None # Object not found

    def post(self, request, content_type, object_id, format=None):
        """Handle Liking a post (Create a Like instance)."""
        target_object = self.get_target_object(content_type, object_id)
        if not target_object:
            return Response({"error": "Invalid content type or object not found."}, status=status.HTTP_404_NOT_FOUND)

        # Prepare data for creating the Like
        like_data = {'user': request.user}
        if isinstance(target_object, StatusPost):
            like_data['status_post'] = target_object
        elif isinstance(target_object, ForumPost):
            like_data['forum_post'] = target_object
        else:
            # Should not happen if get_target_object worked, but good practice
            return Response({"error": "Unsupported object type for liking."}, status=status.HTTP_400_BAD_REQUEST)

        # Try to create the Like. Use get_or_create to handle existing likes gracefully.
        # The model's unique constraint will prevent duplicates anyway, but get_or_create is cleaner.
        like, created = Like.objects.get_or_create(
            user=request.user,
            status_post=like_data.get('status_post'),
            forum_post=like_data.get('forum_post')
            # Defaults are handled by get_or_create/model constraints
        )

        if created:
            serializer = self.serializer_class(like)
            return Response(serializer.data, status=status.HTTP_201_CREATED) # Successfully created
        else:
            # If get_or_create found an existing like, maybe return it or just confirm existence
            serializer = self.serializer_class(like)
            return Response(serializer.data, status=status.HTTP_200_OK) # Like already exists


    def delete(self, request, content_type, object_id, format=None):
        """Handle Unliking a post (Delete the Like instance)."""
        target_object = self.get_target_object(content_type, object_id)
        if not target_object:
            # Don't need to check target existence strictly for delete,
            # as maybe the post was deleted, but we still want to remove the like record.
            # However, we do need to know the type to construct the filter.
            if content_type == 'statuspost':
                filter_kwargs = {'status_post_id': object_id}
            elif content_type == 'forumpost':
                filter_kwargs = {'forum_post_id': object_id}
            else:
                return Response({"error": "Invalid content type."}, status=status.HTTP_400_BAD_REQUEST)

        else: # Target object exists, construct filter based on its type
            if isinstance(target_object, StatusPost):
                filter_kwargs = {'status_post': target_object}
            elif isinstance(target_object, ForumPost):
                filter_kwargs = {'forum_post': target_object}
            else:
                return Response({"error": "Unsupported object type."}, status=status.HTTP_400_BAD_REQUEST)

        # Find the specific like by the current user for the target object
        try:
            like_instance = Like.objects.get(user=request.user, **filter_kwargs)
            like_instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT) # Successfully deleted
        except Like.DoesNotExist:
            # The user hadn't liked this object, or already unliked it.
            return Response({"error": "Like not found."}, status=status.HTTP_404_NOT_FOUND)
        

# --- Add this new View for Comments ---

class CommentListCreateAPIView(generics.ListCreateAPIView):
    """
    API view to list comments for a specific object (GET)
    or create a new comment for that object (POST).
    Uses Generic Relations via URL parameters 'content_type' and 'object_id'.
    Example URL: /api/comments/statuspost/1/
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly] # Allow reading comments, require auth for posting

    def get_queryset(self):
        """
        Filter comments based on the parent object's content type and ID
        provided in the URL.
        """
        # Get the parent object's type and ID from URL kwargs
        content_type_str = self.kwargs.get('content_type')
        object_id = self.kwargs.get('object_id')

        if not content_type_str or not object_id:
            # This shouldn't happen if URL patterns are correct, but good practice
            return Comment.objects.none() # Return empty queryset if params missing

        try:
            # Find the ContentType object corresponding to the string name
            # Ensure your model names are lowercase in the URL (e.g., 'statuspost')
            content_type = ContentType.objects.get(model=content_type_str.lower())
        except ContentType.DoesNotExist:
            # Invalid model name provided in URL
            return Comment.objects.none() # Return empty queryset

        # Filter comments belonging to the specific parent object
        queryset = Comment.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).select_related('author__userprofile') # Optimize by fetching author details

        return queryset

    def perform_create(self, serializer):
        """
        Set the author and link the comment to the correct parent object
        before saving the new comment.
        """
        # Get parent object details from URL
        content_type_str = self.kwargs.get('content_type')
        object_id = self.kwargs.get('object_id')

        try:
            # Find the ContentType object
            content_type = ContentType.objects.get(model=content_type_str.lower())
        except ContentType.DoesNotExist:
            # Handle error - though validation should ideally catch this earlier
            # For now, let serializer validation handle it or raise an error here
            # This scenario is less likely if URL routing is correct.
            # Consider adding validation in the view or serializer if needed.
             raise serializers.ValidationError("Invalid content_type specified in URL.")


        # We don't strictly need to fetch the parent object itself here,
        # just need its content_type and object_id to save the comment.
        # The serializer expects 'author', 'content', 'content_type', 'object_id'
        # Author is set from the request, content from request data.
        # We need to provide the resolved content_type object and object_id.

        # Save the comment, associating it with the logged-in user and the parent object
        serializer.save(
            author=self.request.user,
            content_type=content_type, # The actual ContentType instance
            object_id=object_id       # The ID from the URL
        )


# --- Add this view for single comment operations ---

class CommentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view to retrieve (GET), update (PUT/PATCH), or delete (DELETE)
    a single comment instance by its primary key (ID).
    Ensures only the author can update or delete their comment.
    Example URL: /api/comments/123/  (where 123 is the comment ID)
    """
    queryset = Comment.objects.all() # Base queryset - view handles filtering by pk
    serializer_class = CommentSerializer
    # Apply permissions: Must be authenticated, and must be owner for update/delete
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    # No need to override methods like get_object, perform_update, perform_destroy
    # unless you need custom logic beyond what the generic view and permissions provide.
    # The lookup is handled by generics.RetrieveUpdateDestroyAPIView using 'pk' from URL.
    # The permission class handles ownership checks for unsafe methods (PUT, PATCH, DELETE).

# --- End of CommentRetrieveUpdateDestroyAPIView ---

# --- End of CommentListCreateAPIView ---

# --- Add this new View for the Feed ---

# Use 'views.APIView' if you imported 'views', otherwise use 'APIView' if imported directly


# --- Replace the OLD FeedListView with THIS one ---

# In community/views.py
from rest_framework.pagination import PageNumberPagination # Make sure this import is added at the top

# Use 'views.APIView' or 'APIView' based on your import convention
class FeedListView(views.APIView):
    """
    API view to retrieve the personalized feed for the logged-in user.
    Combines StatusPosts from followed users and ForumPosts from joined groups.
    Sorted by creation date (newest first). NOW WITH PAGINATION.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination # Define the pagination class to use

    def get(self, request, format=None):
        """Handles GET requests to fetch the user's feed."""
        user = request.user
        # Remove the manual limit = 20 here, pagination handles limits
        # limit = 20

        # 1. Get IDs of users the current user follows
        following_user_ids = Follow.objects.filter(follower=user).values_list('following_id', flat=True)

        # 2. Get IDs of groups the current user is a member of
        joined_group_ids = user.joined_groups.values_list('id', flat=True)

        # 3. Fetch recent StatusPosts from followed users
        # Remove the [:limit] slice for now, fetch all relevant ones first
        # NEW LINE:
        status_posts = StatusPost.objects.filter(
        Q(author_id__in=list(following_user_ids)) | Q(author=user) # Posts from followed OR self
        ).select_related('author__userprofile').order_by('-created_at')
        status_posts_list = list(status_posts)


  

    # 4. Fetch recent ForumPosts from joined groups
    # ... rest of the code ...

        # 4. Fetch recent ForumPosts from joined groups
        # Remove the [:limit] slice for now
        group_posts = ForumPost.objects.filter(
            group_id__in=list(joined_group_ids)
        ).select_related('author__userprofile', 'group', 'category').order_by('-created_at')
        group_posts_list = list(group_posts)

        # 5. Combine the lists
        combined_feed_items = status_posts_list + group_posts_list

        # 6. Sort the combined list by 'created_at' date, newest first
        sorted_feed_items = sorted(
            combined_feed_items,
            key=lambda item: item.created_at,
            reverse=True
        )

        # --- ADD PAGINATION LOGIC ---
        # Instantiate the paginator defined in the class or settings
        paginator = self.pagination_class()
        # Paginate the sorted list based on request parameters (e.g., ?page=2)
        paginated_list = paginator.paginate_queryset(sorted_feed_items, request, view=self)
        # --- END PAGINATION LOGIC ---

        # 7. Serialize the PAGINATED list
        # Pass the paginated subset of items to the serializer
        serializer = FeedItemSerializer(paginated_list, many=True)

        # 8. Return the PAGINATED response
        # The paginator provides a method to get the response structure
        # which includes 'count', 'next', 'previous', 'results' keys.
        return paginator.get_paginated_response(serializer.data)
        # --- End of changes ---

# --- End of UPDATED FeedListView ---

# --- Add these views for Private Messaging ---

class ConversationListView(generics.ListAPIView):
    """
    API view to list all conversations the current user participates in.
    Sorted by the last message time (updated_at descending).
    Example URL: /api/conversations/
    """
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated] # Must be logged in to see conversations

    def get_queryset(self):
        """
        Return a queryset of conversations involving the current user.
        """
        user = self.request.user
        # Filter conversations where the user is one of the participants
        # Order by 'updated_at' descending (defined in Conversation.Meta)
        # Prefetch participants and their profiles for efficiency
        return user.conversations.prefetch_related('participants__userprofile').all()

# --- End of ConversationListView ---

class MessageListView(generics.ListAPIView):
    """
    API view to list all messages within a specific conversation.
    Ensures the requesting user is a participant of the conversation.
    Example URL: /api/conversations/5/messages/ (where 5 is the Conversation ID)
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return messages for the specified conversation, ensuring the user
        is a participant.
        """
        user = self.request.user
        # Get conversation ID from URL kwargs
        conversation_id = self.kwargs.get('conversation_id')

        # Get the specific conversation, ensuring the current user is a participant
        conversation = get_object_or_404(
            Conversation.objects.prefetch_related('participants'), # Prefetch for check
            pk=conversation_id,
            participants=user # Filter: user must be in participants
        )

        # If the user is a participant (get_object_or_404 didn't fail),
        # return the messages for that conversation.
        # Ordered by 'timestamp' ascending (defined in Message.Meta)
        # Select related sender details for efficiency
        return conversation.messages.select_related('sender__userprofile').all()

    # We will add POST logic here later to create messages within this conversation.

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



# --- Add this view for Sending Messages ---

# Use views.APIView since you import 'views' from rest_framework
class SendMessageView(views.APIView):
    """
    API view to send a private message to another user.
    If a conversation exists between the sender and recipient, adds the message.
    If not, creates a new conversation first.
    Expects 'recipient_username' and 'content' in request data.
    Example URL: POST /api/messages/send/
    """
    permission_classes = [IsAuthenticated]
    # We use the input serializer manually inside post() for validation

    def post(self, request, format=None):
        # Validate input data using the specific input serializer
        input_serializer = MessageCreateSerializer(data=request.data, context={'request': request})
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = input_serializer.validated_data
        recipient_username = validated_data['recipient_username']
        content = validated_data['content']
        sender = request.user

        try:
            # User variable is defined globally via get_user_model()
            recipient = User.objects.get(username=recipient_username)
        except User.DoesNotExist:
            # This case *should* be caught by serializer validation,
            # but this provides an extra layer of safety.
            return Response({"error": "Recipient not found."}, status=status.HTTP_404_NOT_FOUND)

        # Prevent sending messages to oneself
        if sender == recipient:
             return Response({"error": "You cannot send messages to yourself."}, status=status.HTTP_400_BAD_REQUEST)

        # Find or create the conversation between sender and recipient
        # This looks for conversations that have *at least* these two participants.
        # We need to ensure it finds one with *exactly* these two for 1-on-1 chat.
        # Let's refine the query slightly for exact 2-person conversations.

        # Query using annotation to count participants first
        from django.db.models import Count # Add this import if needed near top of file
        conversation = Conversation.objects.annotate(
            num_participants=Count('participants')
        ).filter(
            participants=sender
        ).filter(
            participants=recipient
        ).filter(
            num_participants=2 # Ensure it's exactly a 2-person chat
        ).first()


        if not conversation:
             # Create a new conversation if none exists with exactly these two
             conversation = Conversation.objects.create()
             conversation.participants.add(sender, recipient)

        # Create the message within the conversation
        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            content=content
        )

        # Important: Update conversation's updated_at timestamp by saving it
        conversation.save()

        # Serialize the newly created message to return it using the main MessageSerializer
        output_serializer = MessageSerializer(message)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

# --- End of SendMessageView ---

# --- End of new View ---
    
