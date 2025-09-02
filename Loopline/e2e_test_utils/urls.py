# Loopline/e2e_test_utils/urls.py

from django.urls import path
from .views import CreateTestUserView, CreateTestFollowView

urlpatterns = [
    path('create-user/', CreateTestUserView.as_view(), name='create-test-user'),
    path('create-follow/', CreateTestFollowView.as_view(), name='create-test-follow'),
]