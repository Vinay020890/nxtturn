# C:\Users\Vinay\Project\Loopline\tests\conftest.py

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from community.models import Group, GroupJoinRequest
from channels.layers import get_channel_layer

User = get_user_model()

# --- THE DEFINITIVE, CORRECTED user_factory FIXTURE ---
@pytest.fixture
def user_factory(db):
    """
    A robust factory that can create users in multiple ways:
    - user_factory() -> creates user_1, user_2, etc.
    - user_factory(username='specific_user') -> creates a user with that exact name.
    - user_factory(username_prefix='test') -> creates test_1, test_2, etc.
    
    It ALWAYS creates a valid user with an email.
    """
    def create_user(
        username=None,
        password='password123',
        username_prefix='user',
        **kwargs
    ):
        # Determine the final username based on priority
        if not username:
            if not hasattr(create_user, "counter"):
                create_user.counter = 0
            create_user.counter += 1
            username = f"{username_prefix}_{create_user.counter}"
        
        # Always generate an email to satisfy allauth's requirements
        email = kwargs.pop('email', f'{username}@test.com')
        
        # Create the user with the final username, email, and any other kwargs
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            **kwargs
        )
        return user
    
    create_user.counter = 0
    return create_user

# --- This fixture is already correct, no changes needed ---
@pytest.fixture
def api_client_factory(db):
    def create_client(user=None):
        client = APIClient()
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        return client
    return create_client

# --- All other fixtures are also correct, no changes needed ---

@pytest.fixture
def api_client(api_client_factory):
    return api_client_factory()
    
@pytest.fixture
def join_request_scenario(user_factory):
    creator = user_factory(username='creator')
    requester = user_factory(username='requester')
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
    return get_channel_layer()