# C:\Users\Vinay\Project\Loopline\tests\community\test_profile_api.py

import pytest
from rest_framework import status
from django.urls import reverse
from community.models import UserProfile, Follow
from tests.conftest import user_factory, api_client_factory, api_client 

pytestmark = pytest.mark.django_db

# --- Test User Profile Retrieval (GET Requests) ---

def test_unauthenticated_user_can_view_profile(api_client, user_factory):
    profile_user = user_factory(username="testprofile")
    url = f"/api/profiles/{profile_user.username}/"
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['user']['username'] == "testprofile"
    assert 'bio' in response.data

def test_authenticated_user_can_view_profile(api_client_factory, user_factory):
    profile_user = user_factory(username="testprofile")
    viewer_user = user_factory(username="viewer")
    client = api_client_factory(user=viewer_user)
    url = f"/api/profiles/{profile_user.username}/"
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['user']['username'] == "testprofile"
    assert response.data['is_followed_by_request_user'] is False

def test_followed_status_is_correct_for_viewer(api_client_factory, user_factory):
    profile_user = user_factory(username="testprofile")
    viewer_user = user_factory(username="viewer")
    Follow.objects.create(follower=viewer_user, following=profile_user)
    client = api_client_factory(user=viewer_user)
    url = f"/api/profiles/{profile_user.username}/"
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['is_followed_by_request_user'] is True

# --- Test User Profile Updates (PATCH Requests) ---

def test_user_can_update_own_profile(api_client_factory, user_factory):
    user = user_factory(username="editor")
    client = api_client_factory(user=user)
    url = f"/api/profiles/{user.username}/"
    payload = {
        "bio": "This is my new bio.",
        "location_city": "New York",
        "skills": ["Django", "React"]
    }
    response = client.patch(url, data=payload, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['bio'] == "This is my new bio."
    user.profile.refresh_from_db()
    assert user.profile.bio == "This is my new bio."

def test_user_cannot_update_another_users_profile(api_client_factory, user_factory):
    profile_owner = user_factory(username="owner")
    attacker = user_factory(username="attacker")
    client = api_client_factory(user=attacker)
    url = f"/api/profiles/{profile_owner.username}/"
    payload = {"bio": "Trying to hack this profile."}
    response = client.patch(url, data=payload, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_unauthenticated_user_cannot_update_profile(api_client, user_factory):
    user = user_factory(username="testuser")
    url = f"/api/profiles/{user.username}/"
    payload = {"bio": "Anonymous update attempt."}
    response = api_client.patch(url, data=payload, format='json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# --- Test Follow/Unfollow Actions ---

def test_user_can_follow_another_user(user_factory, api_client_factory):
    """
    Tests that a user can successfully follow another user via the toggle endpoint.
    """
    user_a = user_factory()
    user_b = user_factory()
    
    client = api_client_factory(user=user_a)
    url = reverse('community:follow-toggle', kwargs={'username': user_b.username})
    response = client.post(url)

    assert response.status_code == status.HTTP_201_CREATED
    assert Follow.objects.filter(follower=user_a, following=user_b).exists()

def test_user_can_unfollow_another_user(user_factory, api_client_factory):
    """
    Regression test to ensure the DELETE method on FollowToggleView works correctly.
    """
    # Arrange: user_a follows user_b
    user_a = user_factory()
    user_b = user_factory()
    Follow.objects.create(follower=user_a, following=user_b)
    assert Follow.objects.count() == 1

    # Act: user_a sends a DELETE request to unfollow user_b
    client = api_client_factory(user=user_a)
    url = reverse('community:follow-toggle', kwargs={'username': user_b.username})
    response = client.delete(url)

    # Assert
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Follow.objects.count() == 0