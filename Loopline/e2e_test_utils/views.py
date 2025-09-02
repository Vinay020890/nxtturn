# Loopline/e2e_test_utils/views.py

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

# We need to import the Follow model from the community app
from community.models import Follow

User = get_user_model()

class CreateTestUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        if not settings.DEBUG:
            return Response(status=status.HTTP_404_NOT_FOUND)
        # ... (rest of the view code is identical) ...
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({"error": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)
        user, created = User.objects.get_or_create(username=username, defaults={'password': 'dummy-for-creation'})
        user.set_password(password)
        user.save()
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response({"username": user.username, "created": created}, status=status_code)

class CreateTestFollowView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        if not settings.DEBUG:
            return Response(status=status.HTTP_404_NOT_FOUND)
        # ... (rest of the view code is identical) ...
        follower_username = request.data.get('follower')
        following_username = request.data.get('following')
        if not follower_username or not following_username:
            return Response({"error": "Both 'follower' and 'following' usernames are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            follower = User.objects.get(username=follower_username)
            following = User.objects.get(username=following_username)
        except User.DoesNotExist:
            return Response({"error": "One of the specified users does not exist."}, status=status.HTTP_404_NOT_FOUND)
        follow, created = Follow.objects.get_or_create(follower=follower, following=following)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response({"detail": f"User '{follower_username}' now follows '{following_username}'."}, status=status_code)