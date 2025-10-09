# C:\Users\Vinay\Project\Loopline\tests\community\test_connections_api.py

import pytest
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from community.models import ConnectionRequest, Follow

from tests.conftest import user_factory, api_client_factory

User = get_user_model()
pytestmark = pytest.mark.django_db

def test_user_can_send_connection_request(user_factory, api_client_factory):
    sender = user_factory()
    receiver = user_factory()
    client = api_client_factory(user=sender)
    url = reverse('community:connection-request-list')
    payload = {'receiver': receiver.id}
    response = client.post(url, payload)
    assert response.status_code == status.HTTP_201_CREATED, response.data
    assert ConnectionRequest.objects.count() == 1
    request = ConnectionRequest.objects.first()
    assert request.sender == sender
    assert request.receiver == receiver
    assert request.status == 'pending'

def test_user_can_list_received_connection_requests(user_factory, api_client_factory):
    user_a = user_factory()
    user_b = user_factory()
    ConnectionRequest.objects.create(sender=user_a, receiver=user_b, status='pending')
    user_c = user_factory()
    ConnectionRequest.objects.create(sender=user_a, receiver=user_c, status='pending')
    client = api_client_factory(user=user_b)
    url = reverse('community:connection-request-list')
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    results = response_data['results']
    assert response_data['count'] == 1
    assert len(results) == 1
    request_data = results[0]
    assert request_data['sender']['id'] == user_a.id
    assert request_data['status'] == 'pending'  

def test_user_can_accept_connection_request(user_factory, api_client_factory):
    user_a = user_factory()
    user_b = user_factory()
    request_obj = ConnectionRequest.objects.create(sender=user_a, receiver=user_b)
    client = api_client_factory(user=user_b)
    url = reverse('community:connection-request-accept', kwargs={'pk': request_obj.id})
    response = client.post(url)
    assert response.status_code == status.HTTP_200_OK
    request_obj.refresh_from_db()
    assert request_obj.status == 'accepted'
    assert Follow.objects.filter(follower=user_a, following=user_b).exists()
    assert Follow.objects.filter(follower=user_b, following=user_a).exists()

def test_user_can_reject_connection_request(user_factory, api_client_factory):
    user_a = user_factory()
    user_b = user_factory()
    request_obj = ConnectionRequest.objects.create(sender=user_a, receiver=user_b)
    client = api_client_factory(user=user_b)
    url = reverse('community:connection-request-reject', kwargs={'pk': request_obj.id})
    response = client.post(url)
    assert response.status_code == status.HTTP_200_OK
    request_obj.refresh_from_db()
    assert request_obj.status == 'rejected'
    assert not Follow.objects.filter(follower=user_b, following=user_a).exists()

# --- NEW TESTS FOR "CONNECTION-FIRST" LOGIC ---

def test_follow_back_on_pending_request_accepts_connection(user_factory, api_client_factory):
    """
    Tests the special case where following a user who has sent a request
    automatically accepts the connection and creates a mutual follow.
    """
    user_a = user_factory()
    user_b = user_factory()
    ConnectionRequest.objects.create(sender=user_a, receiver=user_b, status='pending')
    client = api_client_factory(user=user_b)
    url = reverse('community:follow-toggle', kwargs={'username': user_a.username})
    response = client.post(url)
    assert response.status_code == status.HTTP_201_CREATED
    updated_request = ConnectionRequest.objects.get(sender=user_a, receiver=user_b)
    assert updated_request.status == 'accepted'
    assert Follow.objects.filter(follower=user_b, following=user_a).exists()
    assert Follow.objects.filter(follower=user_a, following=user_b).exists()

def test_unfollow_breaks_connection(user_factory, api_client_factory):
    """
    Tests that if a connected user unfollows the other, the connection
    is broken (request status is changed).
    """
    user_a = user_factory()
    user_b = user_factory()
    Follow.objects.create(follower=user_a, following=user_b)
    Follow.objects.create(follower=user_b, following=user_a)
    request_obj = ConnectionRequest.objects.create(sender=user_a, receiver=user_b, status='accepted')
    client = api_client_factory(user=user_b)
    url = reverse('community:follow-toggle', kwargs={'username': user_a.username})
    response = client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    request_obj.refresh_from_db()
    assert request_obj.status == 'rejected' # Check it's marked as broken
    assert not Follow.objects.filter(follower=user_b, following=user_a).exists()

# --- END OF NEW TESTS ---

@pytest.mark.django_db
class TestRelationshipStatusAPI:
    def test_no_relationship(self, user_factory, api_client_factory):
        user_a = user_factory()
        user_b = user_factory()
        client = api_client_factory(user=user_a)
        url = reverse('community:user-relationship', kwargs={'username': user_b.username})
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"follow_status": "not_following", "connection_status": "not_connected"}

    def test_user_a_follows_user_b(self, user_factory, api_client_factory):
        user_a = user_factory()
        user_b = user_factory()
        Follow.objects.create(follower=user_a, following=user_b)
        client = api_client_factory(user=user_a)
        url = reverse('community:user-relationship', kwargs={'username': user_b.username})
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"follow_status": "following", "connection_status": "not_connected"}

    def test_user_b_follows_user_a(self, user_factory, api_client_factory):
        user_a = user_factory()
        user_b = user_factory()
        Follow.objects.create(follower=user_b, following=user_a)
        client = api_client_factory(user=user_a)
        url = reverse('community:user-relationship', kwargs={'username': user_b.username})
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"follow_status": "followed_by", "connection_status": "not_connected"}

    def test_request_sent_from_a_to_b(self, user_factory, api_client_factory):
        user_a = user_factory()
        user_b = user_factory()
        ConnectionRequest.objects.create(sender=user_a, receiver=user_b, status='pending')
        client = api_client_factory(user=user_a)
        url = reverse('community:user-relationship', kwargs={'username': user_b.username})
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"follow_status": "not_following", "connection_status": "request_sent"}
        
    def test_request_received_by_a_from_b(self, user_factory, api_client_factory):
        user_a = user_factory()
        user_b = user_factory()
        ConnectionRequest.objects.create(sender=user_b, receiver=user_a, status='pending')
        client = api_client_factory(user=user_a)
        url = reverse('community:user-relationship', kwargs={'username': user_b.username})
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"follow_status": "not_following", "connection_status": "request_received"}

    def test_users_are_connected(self, user_factory, api_client_factory):
        user_a = user_factory()
        user_b = user_factory()
        Follow.objects.create(follower=user_a, following=user_b)
        Follow.objects.create(follower=user_b, following=user_a)
        client = api_client_factory(user=user_a)
        url = reverse('community:user-relationship', kwargs={'username': user_b.username})
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"follow_status": "following", "connection_status": "connected"}

def test_user_can_accept_request_via_username_endpoint(user_factory, api_client_factory):
    sender = user_factory()
    receiver = user_factory()
    ConnectionRequest.objects.create(sender=sender, receiver=receiver)
    client = api_client_factory(user=receiver)
    url = reverse('community:user-accept-request', kwargs={'username': sender.username})
    response = client.post(url)
    assert response.status_code == status.HTTP_200_OK
    assert Follow.objects.filter(follower=receiver, following=sender).exists()
    assert Follow.objects.filter(follower=sender, following=receiver).exists()