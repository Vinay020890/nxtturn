from django.urls import path
from . import views # Import views from the current directory

app_name = 'community' # Optional: Namespace for URLs

urlpatterns = [
    # URL pattern for retrieving/updating a specific user profile by username
    path('profiles/<str:username>/', views.UserProfileDetailView.as_view(), name='profile-detail'),

     # In community/urls.py's urlpatterns list:
# Change this line:
# path('users/<str:username>/follow/', views.FollowUserView.as_view(), name='follow-user'),
# TO this:
   path('users/<str:username>/follow/', views.FollowToggleView.as_view(), name='follow-toggle'), # Use the new view

   # Add URL pattern for listing users someone is following
    path('users/<str:username>/following/', views.FollowingListView.as_view(), name='following-list'), # Add this line

      # Add URL pattern for listing users who follow someone
    path('users/<str:username>/followers/', views.FollowersListView.as_view(), name='followers-list'), # Add this line

     # Add URL pattern for LISTING posts for a specific user
    path('users/<str:username>/posts/', views.StatusPostListCreateView.as_view(), name='user-post-list'), # Add this line

    # Add URL pattern for CREATING a new status post
    path('posts/', views.StatusPostListCreateView.as_view(), name='post-create'), # Add this line

     # --- Forum URLs ---
    path('forums/', views.ForumCategoryListView.as_view(), name='forum-category-list'), # Add this line: List all categories
    path('forums/<int:category_id>/posts/', views.ForumPostListCreateView.as_view(), name='forum-post-list-create'), # Add this line: List/Create posts in a category
    # --- ADD THIS LINE for single Forum Posts ---
    path('forumposts/<int:pk>/', views.ForumPostRetrieveUpdateDestroyView.as_view(), name='forumpost-detail'),

       # --- Group URLs ---
    path('groups/', views.GroupListView.as_view(), name='group-list'), # Add this line: List all groups

     # Add URL pattern for joining/leaving a group
    path('groups/<int:group_id>/membership/', views.GroupMembershipView.as_view(), name='group-membership'),

      # --- ADD THIS LINE for single Group retrieval ---
    path('groups/<int:pk>/', views.GroupRetrieveAPIView.as_view(), name='group-detail'),

    # Add URL pattern for listing/creating posts within a group
    path('groups/<int:group_id>/posts/', views.ForumPostListCreateView.as_view(), name='group-post-list-create'),

    path('<str:content_type>/<int:object_id>/like/', views.LikeToggleAPIView.as_view(), name='like-toggle'),

        # List comments for a specific object or Create a new comment for it
    path('comments/<str:content_type>/<int:object_id>/', views.CommentListCreateAPIView.as_view(), name='comment-list-create'),
    # Example URL: /api/comments/statuspost/1/ (GET to list, POST to create)

    # Retrieve, Update, or Delete a specific comment by its ID
    path('comments/<int:pk>/', views.CommentRetrieveUpdateDestroyAPIView.as_view(), name='comment-detail'),
    # Example URL: /api/comments/5/ (GET, PUT, PATCH, DELETE)

     # --- Feed URL ---
    path('feed/', views.FeedListView.as_view(), name='user-feed'), 

     # --- ADD THIS LINE for single Status Posts ---
    path('posts/<int:pk>/', views.StatusPostRetrieveUpdateDestroyView.as_view(), name='statuspost-detail'),

      # --- Private Messaging URLs ---
    # List user's conversations
    path('conversations/', views.ConversationListView.as_view(), name='conversation-list'),
    # List messages within a specific conversation
    path('conversations/<int:conversation_id>/messages/', views.MessageListView.as_view(), name='message-list'),

     # --- ADD THIS LINE for sending a message ---
    path('messages/send/', views.SendMessageView.as_view(), name='message-send'), # Send a message (finds/creates convo)





    # Add other community app URLs here later (e.g., for posts, follows, etc.)
]