# C:\Users\Vinay\Project\Loopline\tests\community\test_profile_api.py
# --- THIS IS THE COMPLETE, UPDATED FILE CONTENT ---

import pytest
from rest_framework import status
from django.urls import reverse
from community.models import UserProfile, Follow, ConnectionRequest, SocialLink
from tests.conftest import user_factory, api_client_factory, api_client

pytestmark = pytest.mark.django_db

# ===================================================================
# --- REFACTORED TESTS for UserProfileDetailView and its new Serializer ---
# ===================================================================


def test_unauthenticated_user_can_view_profile(api_client, user_factory):
    profile_user = user_factory(username="testprofile")
    url = reverse(
        "community:userprofile-detail", kwargs={"username": profile_user.username}
    )
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["user"]["username"] == "testprofile"
    # For unauthenticated users, the relationship status should be None.
    assert response.data["relationship_status"] is None


def test_profile_returns_correct_relationship_status_no_relationship(
    api_client_factory, user_factory
):
    profile_user = user_factory()
    viewer_user = user_factory()
    client = api_client_factory(user=viewer_user)
    url = reverse(
        "community:userprofile-detail", kwargs={"username": profile_user.username}
    )
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    expected_status = {
        "connection_status": "not_connected",
        "is_followed_by_request_user": False,
    }
    assert response.data["relationship_status"] == expected_status


def test_profile_returns_correct_relationship_status_viewer_follows(
    api_client_factory, user_factory
):
    profile_user = user_factory()
    viewer_user = user_factory()
    Follow.objects.create(follower=viewer_user, following=profile_user)
    client = api_client_factory(user=viewer_user)
    url = reverse(
        "community:userprofile-detail", kwargs={"username": profile_user.username}
    )
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    expected_status = {
        "connection_status": "not_connected",
        "is_followed_by_request_user": True,
    }
    assert response.data["relationship_status"] == expected_status


def test_profile_returns_correct_relationship_status_request_sent(
    api_client_factory, user_factory
):
    profile_user = user_factory()
    viewer_user = user_factory()
    ConnectionRequest.objects.create(
        sender=viewer_user, receiver=profile_user, status="pending"
    )
    client = api_client_factory(user=viewer_user)
    url = reverse(
        "community:userprofile-detail", kwargs={"username": profile_user.username}
    )
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    expected_status = {
        "connection_status": "request_sent",
        "is_followed_by_request_user": False,
    }
    assert response.data["relationship_status"] == expected_status


def test_profile_returns_correct_relationship_status_request_received(
    api_client_factory, user_factory
):
    profile_user = user_factory()
    viewer_user = user_factory()
    ConnectionRequest.objects.create(
        sender=profile_user, receiver=viewer_user, status="pending"
    )
    client = api_client_factory(user=viewer_user)
    url = reverse(
        "community:userprofile-detail", kwargs={"username": profile_user.username}
    )
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    expected_status = {
        "connection_status": "request_received",
        "is_followed_by_request_user": False,
    }
    assert response.data["relationship_status"] == expected_status


def test_profile_returns_correct_relationship_status_connected(
    api_client_factory, user_factory
):
    profile_user = user_factory()
    viewer_user = user_factory()
    Follow.objects.create(follower=viewer_user, following=profile_user)
    Follow.objects.create(follower=profile_user, following=viewer_user)
    client = api_client_factory(user=viewer_user)
    url = reverse(
        "community:userprofile-detail", kwargs={"username": profile_user.username}
    )
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    expected_status = {
        "connection_status": "connected",
        "is_followed_by_request_user": True,
    }
    assert response.data["relationship_status"] == expected_status


# ===================================================================
# --- Tests for User Profile Updates (PATCH Requests) - UPDATED ---
# ===================================================================


def test_user_can_update_own_profile(api_client_factory, user_factory):
    """
    Tests that a user can update their own profile with the new
    structured location data.
    """
    user = user_factory(username="editor")
    client = api_client_factory(user=user)
    url = reverse("community:userprofile-detail", kwargs={"username": user.username})

    # MODIFIED: The payload now uses the new field names
    payload = {
        "bio": "This is my new bio.",
        "location_city": "New York",
        "location_administrative_area": "NY",
        "location_country": "USA",
        "current_work_style": "remote",
        "is_open_to_relocation": True,
    }

    response = client.patch(url, data=payload, format="json")

    # ASSERT: Check the response status and data
    assert response.status_code == status.HTTP_200_OK
    assert response.data["bio"] == "This is my new bio."
    assert response.data["location_city"] == "New York"
    assert response.data["current_work_style"] == "remote"
    assert response.data["is_open_to_relocation"] is True

    # ASSERT: Check the database state (most important)
    user.profile.refresh_from_db()
    assert user.profile.bio == "This is my new bio."
    assert user.profile.location_city == "New York"
    assert user.profile.location_administrative_area == "NY"
    assert user.profile.location_country == "USA"
    assert user.profile.current_work_style == "remote"
    assert user.profile.is_open_to_relocation is True


# Find and replace the test_user_can_update_social_links function with this one.


def test_user_can_update_social_links(api_client_factory, user_factory):
    """
    Tests the full create, update, and delete lifecycle for SocialLink objects
    via a single PATCH request to the user's profile.
    """
    user = user_factory(username="linker")
    profile = user.profile
    client = api_client_factory(user=user)

    # ARRANGE: Create some initial links in the database
    link_to_update = SocialLink.objects.create(
        profile=profile, link_type="linkedin", url="https://linkedin.com/old"
    )
    link_to_delete = SocialLink.objects.create(
        profile=profile, link_type="twitter", url="https://twitter.com/old"
    )

    url = reverse("community:userprofile-detail", kwargs={"username": user.username})

    payload = {
        "social_links": [
            # The frontend sends what it considers an "update" to the LinkedIn link
            {"link_type": "linkedin", "url": "https://linkedin.com/new-and-updated"},
            # And a "creation" of a GitHub link
            {"link_type": "github", "url": "https://github.com/new"},
        ]
    }

    # ACT: Make the API call
    response = client.patch(url, data=payload, format="json")

    # ASSERT: Check the response
    assert response.status_code == status.HTTP_200_OK

    # ASSERT: Check the database state
    profile.refresh_from_db()

    # There should now be exactly 2 links associated with the profile
    assert profile.social_links.count() == 2

    # The link_to_delete (twitter) should no longer exist by its old ID
    assert not SocialLink.objects.filter(id=link_to_delete.id).exists()

    # The original link_to_update (linkedin) should also be gone, as it was re-created
    assert not SocialLink.objects.filter(id=link_to_update.id).exists()

    # We should now find a NEW LinkedIn link with the updated URL
    assert profile.social_links.filter(
        link_type="linkedin", url="https://linkedin.com/new-and-updated"
    ).exists()

    # And the new GitHub link should exist
    assert profile.social_links.filter(
        link_type="github", url="https://github.com/new"
    ).exists()


def test_user_cannot_update_another_users_profile(api_client_factory, user_factory):
    profile_owner = user_factory(username="owner")
    attacker = user_factory(username="attacker")
    client = api_client_factory(user=attacker)
    url = reverse(
        "community:userprofile-detail", kwargs={"username": profile_owner.username}
    )
    payload = {"bio": "Trying to hack this profile."}
    response = client.patch(url, data=payload, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_unauthenticated_user_cannot_update_profile(api_client, user_factory):
    user = user_factory(username="testuser")
    url = reverse("community:userprofile-detail", kwargs={"username": user.username})
    payload = {"bio": "Anonymous update attempt."}
    response = api_client.patch(url, data=payload, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ===================================================================
# --- Tests for Follow/Unfollow Actions (Basic functionality) ---
# --- These can remain as simple checks for the endpoint itself ---
# ===================================================================


def test_user_can_follow_another_user(user_factory, api_client_factory):
    user_a = user_factory()
    user_b = user_factory()
    client = api_client_factory(user=user_a)
    url = reverse("community:follow-toggle", kwargs={"username": user_b.username})
    response = client.post(url)
    # The new status code for a simple follow is 201 CREATED
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"status": "following"}
    assert Follow.objects.filter(follower=user_a, following=user_b).exists()


def test_user_can_unfollow_another_user(user_factory, api_client_factory):
    user_a = user_factory()
    user_b = user_factory()
    Follow.objects.create(follower=user_a, following=user_b)
    client = api_client_factory(user=user_a)
    url = reverse("community:follow-toggle", kwargs={"username": user_b.username})
    response = client.delete(url)
    # The new status for a simple unfollow is 200 OK
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "unfollowed"}
    assert not Follow.objects.filter(follower=user_a, following=user_b).exists()
