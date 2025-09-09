# C:\Users\Vinay\Project\Loopline\community\conftest.py

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from community.models import Group, GroupJoinRequest
from channels.layers import get_channel_layer

User = get_user_model()

# In tests/conftest.py

@pytest.fixture
def user_factory():
    """
    A factory fixture to create unique users for tests.
    Can create a user with a specific username or a prefixed one.
    
    Usage:
    user_factory() -> user_1
    user_factory(username_prefix='test') -> test_2
    user_factory(username='specific_user') -> specific_user
    """
    def create_user(username_prefix='user', **kwargs):
        # --- THIS IS THE NEW LOGIC ---
        # Check if a specific username was passed in kwargs.
        username = kwargs.get('username')
        
        if not username:
            # If no specific username, use the original prefix logic.
            if not hasattr(create_user, "counter"):
                create_user.counter = 0
            create_user.counter += 1
            username = f"{username_prefix}_{create_user.counter}"
        # --- END OF NEW LOGIC ---
        
        # This part remains the same.
        return User.objects.create_user(username=username, password='password123')
    
    # Reset counter for each test run to ensure isolation.
    create_user.counter = 0
    return create_user


@pytest.fixture
def api_client_factory():
    """
    A factory fixture to create and optionally authenticate an APIClient.
    """
    # This is also a 'factory as a function'.
    def create_client(user=None):
        client = APIClient()
        if user:
            client.force_authenticate(user=user)
        return client
        
    return create_client

@pytest.fixture
def join_request_scenario(user_factory):
    """
    Sets up a complete scenario with a private group and a pending join request.
    
    Returns a dictionary containing:
    - 'creator': The User who owns the group.
    - 'requester': The User who wants to join.
    - 'group': The private Group object.
    - 'request': The pending GroupJoinRequest object.
    """
    creator = user_factory(username_prefix='creator')
    requester = user_factory(username_prefix='requester')
    
    private_group = Group.objects.create(
        creator=creator, 
        name="Exclusive Test Group", 
        privacy_level='private'
    )
    
    join_request = GroupJoinRequest.objects.create(
        user=requester, 
        group=private_group, 
        status='pending'
    )
    
    return {
        'creator': creator,
        'requester': requester,
        'group': private_group,
        'request': join_request
    }

@pytest.fixture
def channel_layer():
    """
    Provides access to the Channels layer for testing.
    This simply returns the default channel layer.
    """
    return get_channel_layer()

@pytest.fixture
def api_client():
    """
    Provides a non-authenticated API client.
    """
    return APIClient()
