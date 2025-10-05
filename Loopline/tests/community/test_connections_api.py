# C:\Users\Vinay\Project\Loopline\tests\community\test_connections_api.py

import pytest
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from community.models import ConnectionRequest, Follow

# Import the factories from your conftest file
from tests.conftest import user_factory, api_client_factory

User = get_user_model()
pytestmark = pytest.mark.django_db


def test_user_can_send_connection_request(user_factory, api_client_factory):
    """
    Tests that an authenticated user can send a connection request to another user.
    """
    # Arrange: Create a sender and a receiver
    sender = user_factory()
    receiver = user_factory()
    
    # Create an authenticated client for the sender
    client = api_client_factory(user=sender)
    
    # Define the URL and the payload
    # The router automatically creates the '-list' suffix for the list/create URL
    url = reverse('community:connection-request-list')
    
    # --- THIS IS THE SECOND FIX ---
    # The payload key should match the serializer field name: 'receiver'
    payload = {'receiver': receiver.id}
    # --- END OF FIX ---

    # Act: Send a POST request to the endpoint
    response = client.post(url, payload)

    # Assert: Check that the request was successful and the object was created
    assert response.status_code == status.HTTP_201_CREATED, response.data
    
    # Verify the ConnectionRequest was created in the database
    assert ConnectionRequest.objects.count() == 1
    request = ConnectionRequest.objects.first()
    assert request.sender == sender
    assert request.receiver == receiver
    assert request.status == 'pending'


def test_user_can_list_received_connection_requests(user_factory, api_client_factory):
    """
    Tests that a user can retrieve a list of their pending connection requests.
    """
    # Arrange: Create two users and a connection request from A to B
    user_a = user_factory()
    user_b = user_factory()
    ConnectionRequest.objects.create(sender=user_a, receiver=user_b, status='pending')

    # Create another random request to ensure we only get B's requests
    user_c = user_factory()
    ConnectionRequest.objects.create(sender=user_a, receiver=user_c, status='pending')

    # Act: Authenticate as user_b and get the list of requests
    client = api_client_factory(user=user_b)
    url = reverse('community:connection-request-list')
    response = client.get(url)

    # Assert: Check that the request was successful and contains the correct data
    assert response.status_code == status.HTTP_200_OK
    
    # We expect only the one request where user_b is the receiver
    # This is the new, correct code
    response_data = response.json()
    results = response_data['results'] # <-- 1. Get the list from the 'results' key

    assert response_data['count'] == 1 # <-- 2. Check the 'count' from the paginator
    assert len(results) == 1           # <-- 3. Also check the length of the results list

    request_data = results[0]          # <-- 4. Get the first item from the results list


    assert request_data['sender']['id'] == user_a.id
    assert request_data['status'] == 'pending'  

def test_user_can_accept_connection_request(user_factory, api_client_factory):
    """
    Tests that the receiver can accept a pending connection request,
    which creates a mutual follow relationship.
    """
    # Arrange: Create a pending request from user_a to user_b
    user_a = user_factory()
    user_b = user_factory()
    request_obj = ConnectionRequest.objects.create(sender=user_a, receiver=user_b)

    # Act: Authenticate as user_b and send a POST request to the 'accept' action
    client = api_client_factory(user=user_b)
    
    # This URL will point to the 'accept' custom action on our ViewSet
    # DRF routers create this URL format automatically: {basename}-{action_name}
    url = reverse('community:connection-request-accept', kwargs={'pk': request_obj.id})
    response = client.post(url)

    # Assert: Check the outcomes
    assert response.status_code == status.HTTP_200_OK
    
    # 1. The request status is updated to 'accepted'
    request_obj.refresh_from_db()
    assert request_obj.status == 'accepted'

    # 2. A mutual follow now exists
    assert Follow.objects.filter(follower=user_a, following=user_b).exists()
    assert Follow.objects.filter(follower=user_b, following=user_a).exists()

def test_user_can_reject_connection_request(user_factory, api_client_factory):
    """
    Tests that the receiver can reject a pending connection request.
    """
    # Arrange: Create a pending request from user_a to user_b
    user_a = user_factory()
    user_b = user_factory()
    request_obj = ConnectionRequest.objects.create(sender=user_a, receiver=user_b)

    # Act: Authenticate as user_b and send a POST request to the 'reject' action
    client = api_client_factory(user=user_b)
    url = reverse('community:connection-request-reject', kwargs={'pk': request_obj.id})
    response = client.post(url)

    # Assert: Check the outcomes
    assert response.status_code == status.HTTP_200_OK
    
    # 1. The request status is updated to 'rejected'
    request_obj.refresh_from_db()
    assert request_obj.status == 'rejected'

    # 2. Assert that NO mutual follow was created
    assert not Follow.objects.filter(follower=user_b, following=user_a).exists()