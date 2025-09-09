# C:\Users\Vinay\Project\Loopline\e2e_test_utils\views.py

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from community.models import Follow, StatusPost, Poll, PollOption, UserProfile

User = get_user_model()

# This view is deprecated in favor of TestSetupAPIView but kept for reference
class CreateTestUserView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        if not settings.DEBUG:
            return Response(status=status.HTTP_404_NOT_FOUND)
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({"error": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)
        user, created = User.objects.get_or_create(username=username, defaults={'password': 'dummy-for-creation'})
        user.set_password(password)
        user.save()
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response({"username": user.username, "created": created}, status=status_code)

# This view is deprecated in favor of TestSetupAPIView but kept for reference
class CreateTestFollowView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        if not settings.DEBUG:
            return Response(status=status.HTTP_404_NOT_FOUND)
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


# This is our main view for E2E test setup
class TestSetupAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        if not settings.DEBUG:
            return Response(status=status.HTTP_404_NOT_FOUND)

        action = request.data.get("action")
        data = request.data.get("data", {})

        try:
            with transaction.atomic():
                if action == "create_user":
                    username = data.get("username")
                    password = data.get("password", "password123")
                    user, created = User.objects.get_or_create(username=username)
                    if created:
                        user.set_password(password)
                        user.save()
                    
                    if data.get("with_picture", False):
                        dummy_image = SimpleUploadedFile(
                            name='test_avatar.gif',
                            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
                            content_type='image/gif'
                        )
                        profile, _ = UserProfile.objects.get_or_create(user=user)
                        profile.picture.save('test_avatar.gif', dummy_image, save=True)

                    return Response({"message": f"User '{username}' handled."}, status=status.HTTP_201_CREATED)

                elif action == "create_post":
                    author = get_object_or_404(User, username=data.get("username"))
                    post = StatusPost.objects.create(author=author, content=data.get("content"))
                    return Response({"message": "Post created.", "post_id": post.id}, status=status.HTTP_201_CREATED)

                elif action == "create_post_with_poll":
                    author = get_object_or_404(User, username=data.get("username"))
                    post_content = data.get("poll_question", "Default Poll Question")
                    post = StatusPost.objects.create(author=author, content=post_content)
                    poll = Poll.objects.create(post=post, question=data["poll_question"])
                    for option_text in data["poll_options"]:
                        PollOption.objects.create(poll=poll, text=option_text)
                    return Response({"message": "Post with poll created."}, status=status.HTTP_201_CREATED)

                elif action == "create_follow":
                    follower = get_object_or_404(User, username=data.get("follower"))
                    following = get_object_or_404(User, username=data.get("following"))
                    Follow.objects.get_or_create(follower=follower, following=following)
                    return Response({"message": "Follow relationship created."}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"error": "Invalid action specified."}, status=status.HTTP_400_BAD_REQUEST)