# C:\Users\Vinay\Project\Loopline\tests\community\test_feed_api.py

import pytest
from rest_framework import status
from community.models import StatusPost, Follow, Group

# We will need the user_factory and api_client_factory fixtures
from tests.conftest import user_factory, api_client_factory

# Mark all tests in this file to use the database
pytestmark = pytest.mark.django_db


# --- NEW FIXTURE for setting up a common feed scenario ---

@pytest.fixture
def feed_scenario(user_factory):
    """
    Creates a common social graph for feed testing:
    - user_a: The main user whose feed we are testing.
    - user_b: A user that user_a follows.
    - user_c: A user that user_a does NOT follow.
    
    Also creates a private group owned by user_b that user_a is NOT a member of.
    """
    user_a = user_factory(username='user_a')
    user_b = user_factory(username='user_b')
    user_c = user_factory(username='user_c')

    Follow.objects.create(follower=user_a, following=user_b)
    
    private_group = Group.objects.create(creator=user_b, name="User B's Private Group", privacy_level='private')
    private_group.members.add(user_b)

    # Create posts for each scenario
    post_a = StatusPost.objects.create(author=user_a, content="This is User A's own post.")
    post_b_public = StatusPost.objects.create(author=user_b, content="This is User B's public post.")
    post_b_private = StatusPost.objects.create(author=user_b, content="This is User B's PRIVATE post.", group=private_group)
    post_c = StatusPost.objects.create(author=user_c, content="This is User C's post, an unfollowed user.")
    
    return {
        'user_a': user_a,
        'user_b': user_b,
        'user_c': user_c,
        'post_a': post_a,
        'post_b_public': post_b_public,
        'post_b_private': post_b_private,
        'post_c': post_c,
    }


# --- THE ORIGINAL 5 TESTS (Verified to work with the new fixture) ---

def test_unauthenticated_user_cannot_access_feed(api_client_factory):
    """Verifies that the feed endpoint requires authentication."""
    client = api_client_factory()
    response = client.get('/api/feed/')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_feed_contains_own_posts(feed_scenario, api_client_factory):
    """Verifies that a user's feed includes their own posts."""
    user = feed_scenario['user_a']
    client = api_client_factory(user=user)
    
    response = client.get('/api/feed/')
    assert response.status_code == status.HTTP_200_OK
    
    feed_contents = [post['content'] for post in response.json()['results']]
    
    assert feed_scenario['post_a'].content in feed_contents


def test_feed_contains_followed_user_posts(feed_scenario, api_client_factory):
    """Verifies that a user's feed includes posts from users they follow."""
    user = feed_scenario['user_a']
    client = api_client_factory(user=user)
    
    response = client.get('/api/feed/')
    assert response.status_code == status.HTTP_200_OK
    
    feed_contents = [post['content'] for post in response.json()['results']]
    
    # Use the public post for this assertion
    assert feed_scenario['post_b_public'].content in feed_contents


def test_feed_excludes_unfollowed_user_posts(feed_scenario, api_client_factory):
    """Verifies that a user's feed does NOT include posts from users they don't follow."""
    user = feed_scenario['user_a']
    client = api_client_factory(user=user)
    
    response = client.get('/api/feed/')
    assert response.status_code == status.HTTP_200_OK
    
    feed_contents = [post['content'] for post in response.json()['results']]
    
    assert feed_scenario['post_c'].content not in feed_contents


def test_feed_is_correctly_ordered_by_newest_first(user_factory, api_client_factory):
    """Verifies that the feed is ordered by creation date, descending."""
    user = user_factory()
    client = api_client_factory(user=user)
    
    oldest_post = StatusPost.objects.create(author=user, content="Oldest post.")
    newest_post = StatusPost.objects.create(author=user, content="Newest post.")
    
    response = client.get('/api/feed/')
    assert response.status_code == status.HTTP_200_OK
    
    results = response.json()['results']
    
    assert len(results) == 2
    assert results[0]['id'] == newest_post.id
    assert results[1]['id'] == oldest_post.id


# --- NEW EDGE CASE AND NEGATIVE SCENARIO TESTS ---

def test_feed_for_new_user_is_empty(user_factory, api_client_factory):
    """Verifies a user with no posts and no followers gets a clean, empty feed."""
    new_user = user_factory()
    client = api_client_factory(user=new_user)
    
    response = client.get('/api/feed/')
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['results'] == []


def test_feed_excludes_posts_from_private_groups_user_is_not_in(feed_scenario, api_client_factory):
    """
    CRITICAL: Verifies the feed does NOT leak posts from private groups
    the user is not a member of, even if they follow the author.
    """
    user = feed_scenario['user_a']
    client = api_client_factory(user=user)
    
    response = client.get('/api/feed/')
    assert response.status_code == status.HTTP_200_OK
    
    feed_contents = [post['content'] for post in response.json()['results']]
    
    # We expect to see the public post from user_b
    assert feed_scenario['post_b_public'].content in feed_contents
    
    # We must NOT see the private post from user_b
    assert feed_scenario['post_b_private'].content not in feed_contents