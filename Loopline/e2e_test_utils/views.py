# C:\Users\Vinay\Project\Loopline\e2e_test_utils\views.py
# REVISED VERSION

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
from community.models import (
    Follow,
    Group,
    StatusPost,
    Poll,
    PollOption,
    UserProfile,
    Skill,
    SkillCategory,
    Education,
    Experience,
    Comment,
    Like,
)
from allauth.account.models import EmailAddress

User = get_user_model()


def create_verified_user(user):
    """Gets or creates a verified EmailAddress record for a user."""
    EmailAddress.objects.get_or_create(
        user=user, defaults={"email": user.email, "primary": True, "verified": True}
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
                    if "username_prefix" in data:
                        prefix = data.get("username_prefix")
                        timestamp = int(time.time())
                        username = f"{prefix}_{timestamp}"
                        email = f"{username}@cypresstest.com"
                        password = "Airtel@123"
                        user = User.objects.create_user(
                            username=username, email=email, password=password
                        )

                        create_verified_user(user)

                        token, _ = Token.objects.get_or_create(user=user)
                        return Response(
                            {
                                "username": user.username,
                                "token": token.key,
                            },
                            status=status.HTTP_201_CREATED,
                        )

                    elif "username" in data:
                        username = data.get("username")
                        password = data.get("password", "password123")
                        email = data.get("email", f"{username}@cypresstest.com")
                        user, created = User.objects.get_or_create(
                            username=username, defaults={"email": email}
                        )
                        if created:
                            user.set_password(password)
                            user.save()

                        create_verified_user(user)

                        if data.get("with_picture", False):
                            dummy_image = SimpleUploadedFile(
                                name="test_avatar.gif",
                                content=b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b",
                                content_type="image/gif",
                            )
                            profile, _ = UserProfile.objects.get_or_create(user=user)
                            profile.picture.save(
                                "test_avatar.gif", dummy_image, save=True
                            )
                        return Response(
                            {"message": f"User '{username}' handled."},
                            status=status.HTTP_201_CREATED,
                        )

                    else:
                        return Response(
                            {
                                "error": "Action 'create_user' requires either 'username' or 'username_prefix' in data."
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                # ====================================================================
                # === START: NEW LOGIC BLOCK ADDED HERE ==============================
                # ====================================================================
                elif action == "create_unverified_user":
                    username = data.get("username")
                    password = data.get("password")
                    email = data.get("email")

                    if not all([username, password, email]):
                        return Response(
                            {
                                "error": "Action 'create_unverified_user' requires 'username', 'password', and 'email' in data."
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    # Create the user but DO NOT call create_verified_user.
                    # This relies on django-allauth's default behavior of creating an
                    # unverified EmailAddress object upon user creation.
                    user = User.objects.create_user(
                        username=username, email=email, password=password
                    )

                    return Response(
                        {"message": f"Unverified user '{username}' created."},
                        status=status.HTTP_201_CREATED,
                    )
                # ====================================================================
                # === END: NEW LOGIC BLOCK ===========================================
                # ====================================================================

                elif action == "create_two_users":
                    user_a_data = data.get("userA", {})
                    user_b_data = data.get("userB", {})

                    # --- Create User A ---
                    user_a, _ = User.objects.get_or_create(
                        username=user_a_data.get("username"),
                        defaults={
                            "email": f'{user_a_data.get("username")}@cypresstest.com'
                        },
                    )
                    user_a.set_password(user_a_data.get("password"))
                    user_a.save()
                    create_verified_user(user_a)  # Use your helper function

                    # --- Create User B ---
                    user_b, _ = User.objects.get_or_create(
                        username=user_b_data.get("username"),
                        defaults={
                            "email": f'{user_b_data.get("username")}@cypresstest.com'
                        },
                    )
                    user_b.set_password(user_b_data.get("password"))
                    user_b.save()
                    create_verified_user(user_b)  # Use your helper function

                    return Response(
                        {
                            "message": "Two users created successfully.",
                            "user_a_id": user_a.id,
                            "user_b_id": user_b.id,
                        },
                        status=status.HTTP_201_CREATED,
                    )

                # --- ADD THIS ENTIRE 'elif' BLOCK ---
                elif action == "create_user_and_post":
                    user_data = data.get("user", {})
                    post_data = data.get("post", {})

                    username = user_data.get("username")
                    password = user_data.get("password", "password123")
                    email = user_data.get("email", f"{username}@cypresstest.com")

                    user, created = User.objects.get_or_create(
                        username=username, defaults={"email": email}
                    )
                    if created:
                        user.set_password(password)
                        user.save()

                    create_verified_user(user)

                    if user_data.get("with_picture", False):
                        dummy_image = SimpleUploadedFile(
                            name="test_avatar.gif",
                            content=b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b",
                            content_type="image/gif",
                        )
                        profile, _ = UserProfile.objects.get_or_create(user=user)
                        profile.picture.save("test_avatar.gif", dummy_image, save=True)

                    # Create the post authored by this user
                    StatusPost.objects.create(
                        author=user,
                        content=post_data.get("content", "Default test post content."),
                    )

                    return Response(
                        {"message": f"User '{username}' and a post were created."},
                        status=status.HTTP_201_CREATED,
                    )
                # --- END OF THE NEW BLOCK ---

                elif action == "create_user_with_posts":
                    username = data.get("username")
                    num_posts = data.get("num_posts", 10)
                    password = "Airtel@123"

                    if not username:
                        return Response(
                            {"error": "Username is required"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={"email": f"{username}@cypresstest.com"},
                    )
                    user.set_password(password)
                    user.save()

                    create_verified_user(user)

                    UserProfile.objects.update_or_create(
                        user=user,
                        defaults={
                            "bio": "This is a default bio for the scroll tester."
                        },
                    )

                    StatusPost.objects.filter(author=user).delete()

                    for i in range(num_posts):
                        StatusPost.objects.create(
                            author=user,
                            content=f"This is test post number {i+1} for user {username}.",
                        )

                    token, _ = Token.objects.get_or_create(user=user)
                    return Response(
                        {
                            "username": user.username,
                            "token": token.key,
                        },
                        status=status.HTTP_201_CREATED,
                    )

                elif action == "create_group":
                    prefix = data.get("creator_username_prefix")
                    username = data.get("creator_username")
                    if not prefix and not username:
                        return Response(
                            {
                                "error": "creator_username_prefix or creator_username is required"
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    if prefix:
                        creator = User.objects.filter(
                            username__startswith=prefix
                        ).latest("date_joined")
                    else:
                        creator = User.objects.get(username=username)
                    timestamp = int(time.time())
                    group_name = data.get("name", "Default Test Group")
                    final_group_name = f"{group_name}-{timestamp}"
                    is_private_flag = data.get("is_private", False)
                    privacy_level_value = "private" if is_private_flag else "public"
                    group = Group.objects.create(
                        name=final_group_name,
                        creator=creator,
                        privacy_level=privacy_level_value,
                    )
                    group.members.add(creator)
                    return Response(
                        {"name": group.name, "slug": group.slug},
                        status=status.HTTP_201_CREATED,
                    )

                elif action == "create_post":
                    author = get_object_or_404(User, username=data.get("username"))
                    post = StatusPost.objects.create(
                        author=author, content=data.get("content")
                    )
                    return Response(
                        {"message": "Post created.", "post_id": post.id},
                        status=status.HTTP_201_CREATED,
                    )

                elif action == "create_post_with_poll":
                    author = get_object_or_404(User, username=data.get("username"))
                    post_content = data.get("poll_question", "Default Poll Question")
                    post = StatusPost.objects.create(
                        author=author, content=post_content
                    )
                    poll = Poll.objects.create(
                        post=post, question=data["poll_question"]
                    )
                    for option_text in data["poll_options"]:
                        PollOption.objects.create(poll=poll, text=option_text)
                    return Response(
                        {"message": "Post with poll created."},
                        status=status.HTTP_201_CREATED,
                    )

                elif action == "create_follow":
                    follower = get_object_or_404(User, username=data.get("follower"))
                    following = get_object_or_404(User, username=data.get("following"))
                    Follow.objects.get_or_create(follower=follower, following=following)
                    return Response(
                        {"message": "Follow relationship created."},
                        status=status.HTTP_201_CREATED,
                    )

                elif action == "get_last_email":
                    from django.core import mail

                    if mail.outbox:
                        last_email = mail.outbox[-1]  # Get the most recent email
                        return Response(
                            {
                                "status": "success",
                                "data": {
                                    "subject": last_email.subject,
                                    "body": last_email.body,
                                    "to": last_email.to[0] if last_email.to else None,
                                },
                            },
                            status=status.HTTP_200_OK,
                        )
                    else:
                        return Response(
                            {"error": "No emails found in outbox"},
                            status=status.HTTP_404_NOT_FOUND,
                        )

                elif action == "cleanup":
                    # --- 1. Identify users by the specific Cypress domain ONLY ---
                    # We also exclude superusers as a final "emergency brake"
                    users_to_delete = User.objects.filter(
                        email__endswith="@cypresstest.com"
                    ).exclude(is_superuser=True)

                    # --- 2. Targeted cleanup of data belonging ONLY to these users ---
                    # This ensures "Frontend Magic" is gone for Cypress users,
                    # but if YOU created "Frontend Magic" on your real account, it stays!

                    SkillCategory.objects.filter(
                        user_profile__user__in=users_to_delete
                    ).delete()
                    Skill.objects.filter(
                        category__user_profile__user__in=users_to_delete
                    ).delete()
                    Education.objects.filter(
                        user_profile__user__in=users_to_delete
                    ).delete()
                    Experience.objects.filter(
                        user_profile__user__in=users_to_delete
                    ).delete()

                    Comment.objects.filter(author__in=users_to_delete).delete()
                    StatusPost.objects.filter(author__in=users_to_delete).delete()

                    # Groups created by these specific test users
                    groups_deleted_count, _ = Group.objects.filter(
                        creator__in=users_to_delete
                    ).delete()

                    # --- 3. Finally, delete the test users themselves ---
                    users_deleted_count, _ = users_to_delete.delete()

                    return Response(
                        {
                            "status": "success",
                            "message": "Domain-locked cleanup complete. Only @cypresstest.com users removed.",
                            "users_deleted": users_deleted_count,
                            "groups_deleted": groups_deleted_count,
                        },
                        status=status.HTTP_200_OK,
                    )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
