import pytest
from django.urls import reverse
from rest_framework import status
from community.models import Follow

# Mark all tests in this file as requiring database access
pytestmark = pytest.mark.django_db


class TestContactTabAPI:
    """
    Test suite for the Contact & Privacy logic.
    Verifies that the server correctly hides/shows data based on the 4 visibility tiers.
    """

    # --- OWNER TESTS (Existing) ---
    def test_unauthenticated_user_cannot_access_contact_endpoint(self, api_client):
        url = reverse("community:profile-contact")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_can_retrieve_their_own_contact_details(
        self, api_client_factory, user_factory
    ):
        user = user_factory()
        profile = user.profile
        profile.phone_number = "1234567890"
        profile.phone_visibility = "self"
        profile.save()

        client = api_client_factory(user=user)
        url = reverse("community:profile-contact")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["phone_number"] == "1234567890"
        assert response.data["email"] == user.email

    # --- PRIVACY TIER TESTS (New & Hardened) ---

    def test_visibility_everyone_public(self, api_client, user_factory):
        """Tier 1: 'public' should be visible to anyone."""
        owner = user_factory()
        owner.profile.phone_number = "999"
        owner.profile.phone_visibility = "public"
        owner.profile.save()

        # Anonymous visitor
        url = reverse(
            "community:userprofile-detail", kwargs={"username": owner.username}
        )
        response = api_client.get(url)
        assert response.data["phone_number"] == "999"

    def test_visibility_followers_only(self, api_client_factory, user_factory):
        """Tier 2: 'followers' should only be visible if the requester follows the owner."""
        owner = user_factory()
        follower = user_factory()
        stranger = user_factory()

        owner.profile.phone_number = "888"
        owner.profile.phone_visibility = "followers"
        owner.profile.save()

        Follow.objects.create(follower=follower, following=owner)

        url = reverse(
            "community:userprofile-detail", kwargs={"username": owner.username}
        )

        # 1. Follower should see it
        client_follower = api_client_factory(user=follower)
        assert client_follower.get(url).data["phone_number"] == "888"

        # 2. Stranger should NOT see it
        client_stranger = api_client_factory(user=stranger)
        assert client_stranger.get(url).data["phone_number"] is None

    def test_visibility_connections_only(self, api_client_factory, user_factory):
        """Tier 3: 'connections' should only be visible if there is a mutual follow."""
        owner = user_factory()
        follower_only = user_factory()
        mutual_friend = user_factory()

        owner.profile.phone_number = "777"
        owner.profile.phone_visibility = "connections"
        owner.profile.save()

        # Simple Follow (one-way)
        Follow.objects.create(follower=follower_only, following=owner)

        # Mutual Follow (two-way)
        Follow.objects.create(follower=mutual_friend, following=owner)
        Follow.objects.create(follower=owner, following=mutual_friend)

        url = reverse(
            "community:userprofile-detail", kwargs={"username": owner.username}
        )

        # 1. One-way follower should NOT see it
        client_fan = api_client_factory(user=follower_only)
        assert client_fan.get(url).data["phone_number"] is None

        # 2. Mutual friend should see it
        client_friend = api_client_factory(user=mutual_friend)
        assert client_friend.get(url).data["phone_number"] == "777"

    def test_visibility_self_only(self, api_client_factory, user_factory):
        """Tier 4: 'self' should be hidden from everyone except the owner."""
        owner = user_factory()
        mutual_friend = user_factory()

        owner.profile.phone_number = "555"
        owner.profile.phone_visibility = "self"
        owner.profile.save()

        # Even a mutual connection...
        Follow.objects.create(follower=mutual_friend, following=owner)
        Follow.objects.create(follower=owner, following=mutual_friend)

        url = reverse(
            "community:userprofile-detail", kwargs={"username": owner.username}
        )

        # 1. Mutual friend should NOT see it
        client_friend = api_client_factory(user=mutual_friend)
        assert client_friend.get(url).data["phone_number"] is None

        # 2. Owner should still see it
        client_owner = api_client_factory(user=owner)
        assert client_owner.get(url).data["phone_number"] == "555"
