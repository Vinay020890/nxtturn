# community/urls.py
from django.urls import path
from . import views # Import views from the current directory

app_name = 'community' # Namespace for URLs

urlpatterns = [
    # --- User Profile, Follows ---
    path('profiles/<str:username>/', views.UserProfileDetailView.as_view(), name='user-profile-detail'),
    # --- List posts by a specific user ---
    path('users/<str:username>/posts/', views.UserPostListView.as_view(), name='user-post-list'),
    # --- Follow/Unfollow ---
    path('users/<str:username>/follow/', views.FollowToggleView.as_view(), name='follow-toggle'),
    path('users/<str:username>/following/', views.FollowingListView.as_view(), name='following-list'),
    path('users/<str:username>/followers/', views.FollowersListView.as_view(), name='followers-list'),

    # --- Status Posts ---
    # Use '/posts/' for listing ALL posts and creating new ones
    path('posts/', views.StatusPostListCreateView.as_view(), name='statuspost-list-create'),
    # Use '/posts/<pk>/' for individual post actions
    path('posts/<int:pk>/', views.StatusPostRetrieveUpdateDestroyView.as_view(), name='statuspost-detail'),

    # --- Liking ---
    # --- CORRECT URL for Like Toggle (Matches corrected view) ---
    path('content/<int:content_type_id>/<int:object_id>/like/', views.LikeToggleAPIView.as_view(), name='like-toggle'),

    # --- Forums ---
    path('forums/', views.ForumCategoryListView.as_view(), name='forum-category-list'),
    # Posts within a category
    path('forums/<int:category_id>/posts/', views.ForumPostListCreateView.as_view(), name='forum-post-list-create-by-category'),
    # Individual forum posts (assuming you want a direct link)
    path('forumposts/<int:pk>/', views.ForumPostRetrieveUpdateDestroyView.as_view(), name='forumpost-detail'),

    # --- Groups ---
    path('groups/', views.GroupListView.as_view(), name='group-list'),
    path('groups/<int:pk>/', views.GroupRetrieveAPIView.as_view(), name='group-detail'),
    path('groups/<int:group_id>/membership/', views.GroupMembershipView.as_view(), name='group-membership'),
    # Posts within a group
    path('groups/<int:group_id>/posts/', views.ForumPostListCreateView.as_view(), name='group-post-list-create-by-group'), # Reuse view

    # --- Comments ---
    # List/Create comments for a specific content type and object ID
    path('comments/<str:content_type>/<int:object_id>/', views.CommentListCreateAPIView.as_view(), name='comment-list-create'),
    # Retrieve/Update/Delete a specific comment by its ID
    path('comments/<int:pk>/', views.CommentRetrieveUpdateDestroyAPIView.as_view(), name='comment-detail'),

    # --- Feed ---
    path('feed/', views.FeedListView.as_view(), name='user-feed'),
    
    # --- Notifications ---
    # List all notifications for the authenticated user
    path('notifications/', views.NotificationListAPIView.as_view(), name='notification-list'),
    path('notifications/unread-count/', views.UnreadNotificationCountAPIView.as_view(), name='notification-unread-count'),
    path('notifications/mark-as-read/', views.MarkNotificationsAsReadAPIView.as_view(), name='notifications-mark-as-read'),
    path('notifications/mark-all-as-read/', views.MarkAllNotificationsAsReadAPIView.as_view(), name='notifications-mark-all-as-read'),
   
    # --- Private Messaging ---
    path('conversations/', views.ConversationListView.as_view(), name='conversation-list'),
    path('conversations/<int:conversation_id>/messages/', views.MessageListView.as_view(), name='message-list'),
    path('messages/send/', views.SendMessageView.as_view(), name='send-message'), # Changed name slightly

]