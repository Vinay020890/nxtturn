# C:\Users\Vinay\Project\Loopline\tests\community\test_profile_api.py

import pytest
from rest_framework import status
from community.models import UserProfile, Follow
from tests.conftest import user_factory, api_client_factory, api_client 

pytestmark = pytest.mark.django_db

# --- Test User Profile Retrieval (GET Requests) ---

def test_unauthenticated_user_can_view_profile(api_client, user_factory):
    """
    Verifies that ANYONE, even an unauthenticated guest, can successfully
    retrieve and view a user's profile.
    """
    profile_user = user_factory(username="testprofile")
    # --- CORRECTED URL ---
    url = f"/api/profiles/{profile_user.username}/"
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['user']['username'] == "testprofile"
    assert 'bio' in response.data

def test_authenticated_user_can_view_profile(api_client_factory, user_factory):
    """
    Verifies that an authenticated user can view another user's profile and
    that the 'is_followed_by_request_user' field is correctly set to False.
    """
    profile_user = user_factory(username="testprofile")
    viewer_user = user_factory(username="viewer")
    client = api_client_factory(user=viewer_user)
    # --- CORRECTED URL ---
    url = f"/api/profiles/{profile_user.username}/"
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['user']['username'] == "testprofile"
    assert response.data['is_followed_by_request_user'] is False

def test_followed_status_is_correct_for_viewer(api_client_factory, user_factory):
    """
    Verifies that 'is_followed_by_request_user' is True when the viewing
    user is following the profile user.
    """
    profile_user = user_factory(username="testprofile")
    viewer_user = user_factory(username="viewer")
    Follow.objects.create(follower=viewer_user, following=profile_user)
    client = api_client_factory(user=viewer_user)
    # --- CORRECTED URL ---
    url = f"/api/profiles/{profile_user.username}/"
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['is_followed_by_request_user'] is True

# --- Test User Profile Updates (PATCH Requests) ---

def test_user_can_update_own_profile(api_client_factory, user_factory):
    """
    Verifies that an authenticated user can successfully send a PATCH request
    to update their own profile information.
    """
    user = user_factory(username="editor")
    client = api_client_factory(user=user)
    # --- CORRECTED URL ---
    url = f"/api/profiles/{user.username}/"
    payload = {
        "bio": "This is my new bio.",
        "location_city": "New York",
        "skills": ["Django", "React"]
    }
    response = client.patch(url, data=payload, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['bio'] == "This is my new bio."
    assert response.data['location_city'] == "New York"
    assert response.data['skills'] == ["Django", "React"]
    user.profile.refresh_from_db()
    assert user.profile.bio == "This is my new bio."

def test_user_cannot_update_another_users_profile(api_client_factory, user_factory):
    """
    CRITICAL: Verifies that a user gets a 403 Forbidden error when
    attempting to update a profile that does not belong to them.
    """
    profile_owner = user_factory(username="owner")
    attacker = user_factory(username="attacker")
    client = api_client_factory(user=attacker)
    # --- CORRECTED URL ---
    url = f"/api/profiles/{profile_owner.username}/"
    payload = {"bio": "Trying to hack this profile."}
    response = client.patch(url, data=payload, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_unauthenticated_user_cannot_update_profile(api_client, user_factory):
    """
    Verifies that an unauthenticated guest gets a 401 Unauthorized error
    when attempting to update any profile.
    """
    user = user_factory(username="testuser")
    # --- CORRECTED URL ---
    url = f"/api/profiles/{user.username}/"
    payload = {"bio": "Anonymous update attempt."}
    response = api_client.patch(url, data=payload, format='json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED