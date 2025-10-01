# C:\Users\Vinay\Project\Loopline\tests\community\test_password_reset_api.py

import pytest
from django.core import mail
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()
pytestmark = pytest.mark.django_db


class TestPasswordResetAPI:
    
    reset_url = "/api/auth/password/reset/"

    def test_user_can_request_password_reset(self, user_factory, api_client):
        """
        Verifies that a POST request with a valid, existing email
        sends a password reset email and returns a success message.
        """
        # Arrange: Create a verified user whose password we want to reset
        user = user_factory()
        
        # Act: Make the API call to request the reset
        response = api_client.post(self.reset_url, {"email": user.email})
        
        # Assert: The API should return a success status
        assert response.status_code == status.HTTP_200_OK
        assert "detail" in response.data
        assert response.data["detail"] == "Password reset e-mail has been sent."
        
        # Assert: An email should have been sent
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to[0] == user.email
        assert "Password Reset" in mail.outbox[0].subject

    def test_password_reset_request_fails_for_nonexistent_email(self, api_client):
        """
        Verifies that requesting a reset for an email that is not in the
        database still returns a success message to prevent user enumeration.
        """
        # Arrange: An email that does not belong to any user
        non_existent_email = "ghost@example.com"
        assert not User.objects.filter(email=non_existent_email).exists()
        
        # Act: Make the API call
        response = api_client.post(self.reset_url, {"email": non_existent_email})
        
        # Assert: The API should still return a success status for security
        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"] == "Password reset e-mail has been sent."
        
        # Assert: Critically, NO email should have been sent
        assert len(mail.outbox) == 0