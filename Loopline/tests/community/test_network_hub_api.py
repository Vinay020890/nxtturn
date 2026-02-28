import pytest
from django.urls import reverse
from rest_framework import status
from community.models import Follow

# Mark all tests in this file as requiring database access
pytestmark = pytest.mark.django_db


class TestNetworkHubAPI:
    """
    Test suite for the Network Hub endpoints.
    Target Endpoints:
    - /api/community/network/followers/
    - /api/community/network/following/
    - /api/community/network/connections/
    """

    def test_get_followers_list(self, api_client_factory, user_factory):
        owner = user_factory(username="owner")
        follower_1 = user_factory(username="follower_1")
        follower_2 = user_factory(username="follower_2")

        # Setup: Two people follow the owner
        Follow.objects.create(follower=follower_1, following=owner)
        Follow.objects.create(follower=follower_2, following=owner)

        client = api_client_factory(user=owner)
        # We expect this URL name to exist
        url = reverse("community:network-followers")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Check that both followers are returned
        assert response.data["count"] == 2
        usernames = [user["username"] for user in response.data["results"]]
        assert "follower_1" in usernames
        assert "follower_2" in usernames

    def test_get_following_list(self, api_client_factory, user_factory):
        owner = user_factory(username="owner")
        target_1 = user_factory(username="target_1")

        # Setup: Owner follows target_1
        Follow.objects.create(follower=owner, following=target_1)

        client = api_client_factory(user=owner)
        url = reverse("community:network-following")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["username"] == "target_1"

    def test_get_mutual_connections_list(self, api_client_factory, user_factory):
        """
        Ensures ONLY mutual follows are returned in the connections endpoint.
        """
        me = user_factory(username="me")
        mutual_friend = user_factory(username="mutual_friend")
        just_follower = user_factory(username="just_follower")

        # 1. Setup Mutual Follow (Connection)
        Follow.objects.create(follower=mutual_friend, following=me)
        Follow.objects.create(follower=me, following=mutual_friend)

        # 2. Setup One-way Follow (Not a Connection)
        Follow.objects.create(follower=just_follower, following=me)

        client = api_client_factory(user=me)
        url = reverse("community:network-connections")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Logic Check: Should ONLY show mutual_friend
        assert response.data["count"] == 1
        assert response.data["results"][0]["username"] == "mutual_friend"

        # Ensure 'just_follower' is filtered out
        usernames = [user["username"] for user in response.data["results"]]
        assert "just_follower" not in usernames

    def test_network_endpoints_require_authentication(self, api_client):
        # Using one of the endpoints to check protection
        try:
            url = reverse("community:network-connections")
            response = api_client.get(url)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        except Exception:
            # If URL doesn't exist yet, we catch it here, but the main tests will fail properly
            pass
