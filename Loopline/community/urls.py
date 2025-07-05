# community/urls.py
from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    # --- User Profile, Follows, and Search ---
    path('profiles/<str:username>/', views.UserProfileDetailView.as_view(), name='user-profile-detail'),
    path('users/<str:username>/posts/', views.UserPostListView.as_view(), name='user-post-list'),
    path('users/<str:username>/follow/', views.FollowToggleView.as_view(), name='follow-toggle'),
    path('users/<str:username>/following/', views.FollowingListView.as_view(), name='following-list'),
    path('users/<str:username>/followers/', views.FollowersListView.as_view(), name='followers-list'),
    path('search/users/', views.UserSearchAPIView.as_view(), name='user-search'), # <-- ADDED THIS LINE

    # --- Status Posts ---
    path('posts/', views.StatusPostListCreateView.as_view(), name='statuspost-list-create'),
    path('posts/<int:pk>/', views.StatusPostRetrieveUpdateDestroyView.as_view(), name='statuspost-detail'),

    # --- Liking ---
    path('content/<int:content_type_id>/<int:object_id>/like/', views.LikeToggleAPIView.as_view(), name='like-toggle'),

    # --- ADD THIS NEW REPORTING URL ---
    path('content/<int:ct_id>/<int:obj_id>/report/', views.ReportCreateAPIView.as_view(), name='content-report'),
    # --- END OF NEW URL ---

    # --- Forums ---
    path('forums/', views.ForumCategoryListView.as_view(), name='forum-category-list'),
    path('forums/<int:category_id>/posts/', views.ForumPostListCreateView.as_view(), name='forum-post-list-create-by-category'),
    path('forumposts/<int:pk>/', views.ForumPostRetrieveUpdateDestroyView.as_view(), name='forumpost-detail'),

    # --- Groups ---
    path('groups/', views.GroupListView.as_view(), name='group-list'),
    path('groups/<int:pk>/', views.GroupRetrieveAPIView.as_view(), name='group-detail'),
    path('groups/<int:group_id>/membership/', views.GroupMembershipView.as_view(), name='group-membership'),
    path('groups/<int:group_id>/posts/', views.ForumPostListCreateView.as_view(), name='group-post-list-create-by-group'),

    # --- Comments ---
    path('comments/<str:content_type>/<int:object_id>/', views.CommentListCreateAPIView.as_view(), name='comment-list-create'),
    path('comments/<int:pk>/', views.CommentRetrieveUpdateDestroyAPIView.as_view(), name='comment-detail'),

    # --- Feed ---
    path('feed/', views.FeedListView.as_view(), name='user-feed'),
    
    # --- Notifications ---
    path('notifications/', views.NotificationListAPIView.as_view(), name='notification-list'),
    path('notifications/unread-count/', views.UnreadNotificationCountAPIView.as_view(), name='notification-unread-count'),
    path('notifications/mark-as-read/', views.MarkNotificationsAsReadAPIView.as_view(), name='notifications-mark-as-read'),
    path('notifications/mark-all-as-read/', views.MarkAllNotificationsAsReadAPIView.as_view(), name='notifications-mark-all-as-read'),
   
    # --- Private Messaging ---
    path('conversations/', views.ConversationListView.as_view(), name='conversation-list'),
    path('conversations/<int:conversation_id>/messages/', views.MessageListView.as_view(), name='message-list'),
    path('messages/send/', views.SendMessageView.as_view(), name='send-message'),

     # NEW: URL for casting a vote on a poll
    path('polls/<int:poll_id>/options/<int:option_id>/vote/', views.PollVoteAPIView.as_view(), name='poll-vote'),
]