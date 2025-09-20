# C:\Users\Vinay\Project\Loopline\e2e_test_utils\views.py

import time
from rest_framework.authtoken.models import Token
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from community.models import Follow, Group, StatusPost, Poll, PollOption, UserProfile
from allauth.account.models import EmailAddress # <-- 1. ADD THIS IMPORT

User = get_user_model()

def create_verified_user(user):
    """Gets or creates a verified EmailAddress record for a user."""
    EmailAddress.objects.get_or_create(
        user=user,
        defaults={
            'email': user.email,
            'primary': True,
            'verified': True
        }
    )

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
                    if 'username_prefix' in data:
                        prefix = data.get("username_prefix")
                        timestamp = int(time.time())
                        username = f"{prefix}_{timestamp}"
                        email = f"{username}@example.com"
                        password = "Airtel@123"
                        user = User.objects.create_user(username=username, email=email, password=password)
                        
                        # <-- 2. ADD VERIFICATION LOGIC
                        create_verified_user(user)

                        token, _ = Token.objects.get_or_create(user=user)
                        return Response({
                            "username": user.username,
                            "token": token.key,
                        }, status=status.HTTP_201_CREATED)
                    
                    elif 'username' in data:
                        username = data.get("username")
                        password = data.get("password", "password123")
                        email = data.get("email", f"{username}@example.com")
                        user, created = User.objects.get_or_create(
                            username=username, 
                            defaults={'email': email}
                        )
                        if created:
                            user.set_password(password)
                            user.save()
                        
                        # <-- 3. ADD VERIFICATION LOGIC
                        create_verified_user(user)

                        if data.get("with_picture", False):
                            dummy_image = SimpleUploadedFile(name='test_avatar.gif', content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b', content_type='image/gif')
                            profile, _ = UserProfile.objects.get_or_create(user=user)
                            profile.picture.save('test_avatar.gif', dummy_image, save=True)
                        return Response({"message": f"User '{username}' handled."}, status=status.HTTP_201_CREATED)
                    
                    else:
                        return Response({"error": "Action 'create_user' requires either 'username' or 'username_prefix' in data."}, status=status.HTTP_400_BAD_REQUEST)

                elif action == "create_user_with_posts":
                    username = data.get("username")
                    num_posts = data.get("num_posts", 10)
                    password = "Airtel@123"

                    if not username:
                        return Response({"error": "Username is required"}, status=status.HTTP_400_BAD_REQUEST)

                    user, created = User.objects.get_or_create(username=username, defaults={'email': f"{username}@example.com"})
                    user.set_password(password)
                    user.save()

                    # <-- 4. ADD VERIFICATION LOGIC
                    create_verified_user(user)

                    UserProfile.objects.update_or_create(
                        user=user,
                        defaults={'bio': 'This is a default bio for the scroll tester.'}
                    )
                    
                    StatusPost.objects.filter(author=user).delete()
                    
                    for i in range(num_posts):
                        StatusPost.objects.create(
                            author=user,
                            content=f"This is test post number {i+1} for user {username}."
                        )
                    
                    token, _ = Token.objects.get_or_create(user=user)
                    return Response({
                        "username": user.username,
                        "token": token.key,
                    }, status=status.HTTP_201_CREATED)
                
                # ... The rest of the file (create_group, create_post, cleanup etc.) remains unchanged ...
                
                elif action == "create_group":
                    prefix = data.get("creator_username_prefix")
                    username = data.get("creator_username")
                    if not prefix and not username:
                        return Response({"error": "creator_username_prefix or creator_username is required"}, status=status.HTTP_400_BAD_REQUEST)
                    if prefix:
                        creator = User.objects.filter(username__startswith=prefix).latest('date_joined')
                    else:
                        creator = User.objects.get(username=username)
                    timestamp = int(time.time())
                    group_name = data.get("name", "Default Test Group")
                    final_group_name = f"{group_name}-{timestamp}"
                    is_private_flag = data.get("is_private", False)
                    privacy_level_value = 'private' if is_private_flag else 'public'
                    group = Group.objects.create(
                        name=final_group_name,
                        creator=creator,
                        privacy_level=privacy_level_value
                    )
                    group.members.add(creator)
                    return Response({ "name": group.name, "slug": group.slug }, status=status.HTTP_201_CREATED)

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

                elif action == 'cleanup':
                    test_user_prefixes = ['scroll_tester', 'creator_', 'requester_', 'member_', 'user_', 'auth_test_', 'multitab_', 'pollTester', 'interaction_', 'profileEditor', 'pictureRemover', 'pictureUploader', 'user_with_posts_', 'reactive_', 'main_', 'joiner_', 'viewer_', 'follower_', 'denied_', 'blocked_']
                    user_query = Q()
                    for prefix in test_user_prefixes:
                        user_query |= Q(username__startswith=prefix)
                    user_query |= Q(username__in=['userA', 'userB', 'userC'])
                    _, users_deleted_details = User.objects.filter(user_query).delete()
                    _, groups_deleted_details = Group.objects.filter(slug__regex=r'-\d{10,}$').delete()
                    return Response({
                        'status': 'success',
                        'message': 'Test data cleanup complete.',
                        'users_deleted': users_deleted_details.get('auth.User', 0),
                        'groups_deleted': groups_deleted_details.get('community.Group', 0),
                    }, status=status.HTTP_200_OK)
            
            return Response({"error": "Invalid action specified."}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)