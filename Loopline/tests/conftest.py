# C:\Users\Vinay\Project\Loopline\tests\conftest.py

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from community.models import Group, GroupJoinRequest
from channels.layers import get_channel_layer

User = get_user_model()

# --- CORRECTED user_factory FIXTURE ---
@pytest.fixture
def user_factory(db):
    """
    A factory fixture to create unique, valid users for tests.
    Ensures that an email is always created, satisfying allauth's requirements.
    """
    def create_user(
        username=None,
        email=None,
        password='password123',
        **kwargs
    ):
        # Generate a unique username if not provided
        if not username:
            # Using a simple counter for username generation
            if not hasattr(create_user, "counter"):
                create_user.counter = 0
            create_user.counter += 1
            username = f'user_{create_user.counter}'

        # Generate a unique email based on the username if not provided
        if not email:
            email = f'{username}@test.com'
        
        # This part now correctly includes the email
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            **kwargs
        )
        return user
    
    # Reset counter for each test run to ensure isolation.
    create_user.counter = 0
    return create_user


# --- CORRECTED api_client_factory FIXTURE for Token Authentication ---
@pytest.fixture
def api_client_factory(db):
    """
    A factory fixture to create and optionally authenticate an APIClient
    using the project's Token Authentication method.
    """
    def create_client(user=None):
        client = APIClient()
        if user:
            # Create a token for the user to simulate a logged-in state
            token, _ = Token.objects.get_or_create(user=user)
            # Set the authorization header for all subsequent requests with this client
            client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        return client
        
    return create_client

# --- Unchanged Fixtures (Copied from your version) ---

@pytest.fixture
def api_client(api_client_factory):
    """Provides a default, unauthenticated API client."""
    return api_client_factory()
    
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
    creator = user_factory(username='creator')
    requester = user_factory(username='requester')
    
    private_group = Group.objects.create(
        creator=creator, 
        name="Exclusive Test Group", 
        privacy_level='private'
    )
    # The creator is automatically a member, so we don't need to add them.
    
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