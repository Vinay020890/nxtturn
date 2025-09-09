# C:\Users\Vinay\Project\Loopline\tests\community\test_registration_api.py
import pytest
from rest_framework import status
from django.contrib.auth import get_user_model

from tests.conftest import user_factory, api_client_factory, api_client

User = get_user_model()
pytestmark = pytest.mark.django_db

def test_user_registration_success(api_client): # <-- MISSING TEST RESTORED
    """
    Ensures a new user can be registered successfully via the API
    with the correct password1 and password2 fields.
    """
    # Define the registration data
    registration_data = {
        'username': 'newtestuser',
        'email': 'newtestuser@example.com',
        'password1': 'StrongPassword123',
        'password2': 'StrongPassword123'
    }

    # Make the POST request to the registration endpoint
    url = '/api/auth/registration/'
    response = api_client.post(url, registration_data)

    # Assert that the request was successful (HTTP 201 Created)
    assert response.status_code == status.HTTP_201_CREATED, \
        f"Expected status 201, but got {response.status_code}. Response: {response.data}"

    # Assert that the user was actually created in the database
    assert User.objects.filter(username='newtestuser').exists()

def test_user_registration_fails_with_mismatched_passwords(api_client):
    """
    Ensures registration fails if password1 and password2 do not match.
    """
    # Arrange
    registration_data = {
        'username': 'anotheruser',
        'email': 'another@example.com',
        'password1': 'StrongPassword123',
        'password2': 'DIFFERENTPassword123'
    }

    # Act
    url = '/api/auth/registration/'
    response = api_client.post(url, registration_data)

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'non_field_errors' in response.data
    assert "The two password fields didn't match." in response.data['non_field_errors'][0]
    assert not User.objects.filter(username='anotheruser').exists()

def test_user_registration_fails_with_existing_username(api_client, user_factory):
    """
    Ensures registration fails if the username is already taken.
    """
    # Arrange
    existing_user = user_factory(username_prefix="existinguser")
    registration_data = {
        'username': existing_user.username,
        'email': 'newemail@example.com',
        'password1': 'StrongPassword123',
        'password2': 'StrongPassword123'
    }

    # Act
    url = '/api/auth/registration/'
    response = api_client.post(url, registration_data)

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'username' in response.data
    assert 'A user with that username already exists.' in response.data['username'][0]