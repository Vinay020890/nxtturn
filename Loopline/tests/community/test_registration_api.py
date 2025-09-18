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

# [Add this function to the end of your test_registration_api.py file]

def test_registration_fails_with_duplicate_email(api_client):
    """
    Ensures registration fails if the email address is already in use,
    even with a different username.
    """
    # Arrange: Define the API endpoint
    url = '/api/auth/registration/'

    # Arrange: Register the first user successfully
    user1_data = {
        "username": "user1_unique",
        "email": "duplicate_test@example.com",
        "password1": "StrongPassword123",
        "password2": "StrongPassword123"
    }
    response1 = api_client.post(url, user1_data)
    assert response1.status_code == status.HTTP_201_CREATED, \
        "The first user should have registered successfully to set up the test."

    # Arrange: Prepare data for a second user with the same email
    user2_data = {
        "username": "user2_also_unique",
        "email": "duplicate_test@example.com",  # Using the same email
        "password1": "StrongPassword123",
        "password2": "StrongPassword123"
    }

    # Act: Attempt to register the second user
    response2 = api_client.post(url, user2_data)

    # Assert: The request should fail with a 400 Bad Request
    assert response2.status_code == status.HTTP_400_BAD_REQUEST, \
        "Expected registration to fail with a 400 status, but it returned 201."
    
    # Assert: The response should contain a specific error message for the email field
    assert 'email' in response2.data
    assert 'This field must be unique.' in response2.data['email'][0]