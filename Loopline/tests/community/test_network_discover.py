import pytest
from django.urls import reverse
from rest_framework import status
from community.models import (
    Follow,
    Education,
    Skill,
    SkillCategory,
    ConnectionRequest,
    RecommendationImpression,
)
from django.contrib.auth import get_user_model
from datetime import date, timedelta

User = get_user_model()

# Mark all tests to use the database
pytestmark = pytest.mark.django_db


class TestNetworkDiscoverAPI:
    """
    Test suite for the Advanced Network Discovery Algorithm.
    Endpoint: /api/community/network/discover/
    """

    def test_discovery_global_exclusions(self, api_client_factory, user_factory):
        """
        SAFETY TEST:
        Ensures users we follow or have pending requests with are banned from ALL categories globally.
        """
        me = user_factory(username="me")
        me.profile.location_city = "Pune"
        me.profile.save()

        # User 1: A perfect match (same city), but we already follow them
        following = user_factory(username="following")
        following.profile.location_city = "Pune"
        following.profile.save()
        Follow.objects.create(follower=me, following=following)

        # User 2: A perfect match (same city), but we sent a request
        requested = user_factory(username="requested")
        requested.profile.location_city = "Pune"
        requested.profile.save()
        ConnectionRequest.objects.create(
            sender=me, receiver=requested, status="pending"
        )

        client = api_client_factory(user=me)
        url = reverse("community:network-discover")
        response = client.get(url)
        data = response.data

        # Collect all suggestions into a single flat list
        all_names = [
            user["username"] for category in data.values() for user in category
        ]

        # ASSERTIONS: They must NOT appear in the recommendations
        assert "following" not in all_names
        assert "requested" not in all_names
        assert "me" not in all_names

    def test_weighted_deduplication(self, api_client_factory, user_factory):
        """
        WEIGHTING TEST:
        A 'Super Match' must appear ONLY in their highest-weighted category.
        Priority: Mutuals > Alumni > Location
        """
        me = user_factory(username="me")
        me.profile.location_city = "Bangalore"
        me.profile.save()
        Education.objects.create(user_profile=me.profile, institution="IIM")

        # Setup a mutual friend to act as the bridge
        friend = user_factory(username="friend")
        Follow.objects.create(follower=me, following=friend)
        Follow.objects.create(follower=friend, following=me)

        # User A: Matches Alumni (Medium) and Location (Low)
        super_alumni = user_factory(username="super_alumni")
        super_alumni.profile.location_city = "Bangalore"
        super_alumni.profile.save()
        Education.objects.create(user_profile=super_alumni.profile, institution="IIM")

        # User B: Matches Mutuals (High), Alumni (Med), and Location (Low)
        mega_match = user_factory(username="mega_match")
        mega_match.profile.location_city = "Bangalore"
        mega_match.profile.save()
        Education.objects.create(user_profile=mega_match.profile, institution="IIM")
        # Make them a mutual connection
        Follow.objects.create(follower=friend, following=mega_match)
        Follow.objects.create(follower=mega_match, following=friend)

        client = api_client_factory(user=me)
        url = reverse("community:network-discover")
        response = client.get(url)
        data = response.data

        mutuals = [u["username"] for u in data["mutual_connections"]]
        alumni = [u["username"] for u in data["alumni"]]
        location = [u["username"] for u in data["local_professionals"]]

        # Assert User B (mega_match) is ONLY in the highest priority list (Mutuals)
        assert "mega_match" in mutuals
        assert "mega_match" not in alumni
        assert "mega_match" not in location

        # Assert User A (super_alumni) is ONLY in their highest priority list (Alumni)
        assert "super_alumni" in alumni
        assert "super_alumni" not in location

    def test_fatigue_exclusion(self, api_client_factory, user_factory):
        """
        FATIGUE TEST:
        Ensures a user is excluded from suggestions after being shown 5 times.
        """
        me = user_factory(username="me")
        me.profile.location_city = "Delhi"
        me.profile.save()

        # Create a user who is a perfect match
        stale_user = user_factory(username="stale_user")
        stale_user.profile.location_city = "Delhi"
        stale_user.profile.save()

        # Manually create the impression record to simulate 5 previous views
        RecommendationImpression.objects.create(
            user=me,
            suggested_user=stale_user,
            impression_count=5,
            last_shown_date=date.today() - timedelta(days=1),  # Shown yesterday
        )

        client = api_client_factory(user=me)
        url = reverse("community:network-discover")
        response = client.get(url)
        data = response.data

        all_names = [
            user["username"] for category in data.values() for user in category
        ]

        # Assert the fatigued user is completely hidden
        assert "stale_user" not in all_names
