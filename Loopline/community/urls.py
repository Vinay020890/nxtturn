# community/urls.py
from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(
    r'connections/requests', 
    views.ConnectionRequestViewSet, 
    basename='connection-request'
)

app_name = 'community'

urlpatterns = [
    # --- User Profile, Follows, and Search ---
    path('profiles/<str:username>/', views.UserProfileDetailView.as_view(), name='user-profile-detail'),
    path('users/<str:username>/posts/', views.UserPostListView.as_view(), name='user-post-list'),
    path('users/<str:username>/follow/', views.FollowToggleView.as_view(), name='follow-toggle'),
    path('users/<str:username>/following/', views.FollowingListView.as_view(), name='following-list'),
    path('users/<str:username>/followers/', views.FollowersListView.as_view(), name='followers-list'),
    path('users/<str:username>/relationship/', views.UserRelationshipView.as_view(), name='user-relationship'),
    path('search/users/', views.UserSearchAPIView.as_view(), name='user-search'), 
    path('search/content/', views.ContentSearchAPIView.as_view(), name='content-search'),

    # --- Status Posts ---
    path('posts/', views.StatusPostListCreateView.as_view(), name='statuspost-list-create'),
    path('posts/<int:pk>/', views.StatusPostRetrieveUpdateDestroyView.as_view(), name='statuspost-detail'),

    # --- Liking ---
    path('content/<int:content_type_id>/<int:object_id>/like/', views.LikeToggleAPIView.as_view(), name='like-toggle'),

    # --- ADD THIS NEW REPORTING URL ---
    path('content/<int:ct_id>/<int:obj_id>/report/', views.ReportCreateAPIView.as_view(), name='content-report'),
    # path('reports/create/', views.ReportCreateAPIView.as_view(), name='report-create'),
    # --- END OF NEW URL ---

    

    # --- Groups ---
    path('groups/', views.GroupListView.as_view(), name='group-list'),
    path('groups/<slug:slug>/', views.GroupRetrieveAPIView.as_view(), name='group-detail'),
    path('groups/<slug:slug>/transfer-ownership/', views.GroupTransferOwnershipView.as_view(), name='group-transfer-ownership'),
    path('groups/<slug:slug>/membership/', views.GroupMembershipView.as_view(), name='group-membership'),
    path('groups/<slug:slug>/status-posts/', views.GroupPostListView.as_view(), name='group-statuspost-list'),

    # === NEW: URLs for managing private group join requests ===
    path('groups/<slug:slug>/requests/', views.GroupJoinRequestListView.as_view(), name='group-join-requests-list'),
    path('groups/<slug:slug>/requests/<int:request_id>/', views.GroupJoinRequestManageView.as_view(), name='group-request-manage'),
    path('groups/<slug:slug>/blocks/', views.GroupBlockListView.as_view(), name='group-block-list'),
    path('groups/<slug:slug>/blocks/<int:user_id>/', views.GroupBlockManageView.as_view(), name='group-block-manage'),
    # =========================================================

    # --- Comments ---
    path('comments/<str:content_type>/<int:object_id>/', views.CommentListCreateAPIView.as_view(), name='comment-list-create'),
    path('comments/<int:pk>/', views.CommentRetrieveUpdateDestroyAPIView.as_view(), name='comment-detail'),

    # --- Feed ---
    path('feed/', views.FeedListView.as_view(), name='user-feed'),
    
    # --- Notifications ---
    path('notifications/', views.NotificationListAPIView.as_view(), name='notification-list'),
    path('notifications/unread-count/', views.UnreadNotificationCountAPIView.as_view(), name='notification-unread-count'),
    
    # --- THIS IS THE NEW URL FOR A SINGLE NOTIFICATION ---
    path('notifications/<int:pk>/mark-as-read/', views.MarkNotificationAsReadAPIView.as_view(), name='notification-mark-as-read'),
    # ---------------------------------------------------

    path('notifications/mark-as-read/', views.MarkMultipleNotificationsAsReadAPIView.as_view(), name='notifications-mark-as-read'), # This handles bulk marking
    path('notifications/mark-all-as-read/', views.MarkAllNotificationsAsReadAPIView.as_view(), name='notifications-mark-all-as-read'),
   
    # --- Private Messaging ---
    path('conversations/', views.ConversationListView.as_view(), name='conversation-list'),
    path('conversations/<int:conversation_id>/messages/', views.MessageListView.as_view(), name='message-list'),
    path('messages/send/', views.SendMessageView.as_view(), name='send-message'),

     # NEW: URL for casting a vote on a poll
     path('polls/<int:poll_id>/options/<int:option_id>/vote/', views.PollVoteAPIView.as_view(), name='poll-vote'),
    

     # === NEW: URLS FOR SAVED POSTS ===
    # ================================================
    path('posts/<int:pk>/save/', views.SavedPostToggleView.as_view(), name='post-save-toggle'),
    path('posts/saved/', views.SavedPostListView.as_view(), name='saved-post-list'),

    path('health-check/', views.health_check_view, name='health-check'),
]

urlpatterns += router.urls