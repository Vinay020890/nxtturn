import pytest
from django.urls import reverse
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
import os

# Mark all tests to use the database
pytestmark = pytest.mark.django_db


@pytest.fixture
def resume_file():
    """
    Creates a dummy PDF file in memory for testing.
    """
    return SimpleUploadedFile(
        "test_resume.pdf",
        b"%PDF-1.4 content...",  # Dummy binary content
        content_type="application/pdf",
    )


def test_upload_resume(api_client_factory, user_factory, resume_file):
    """
    Test that a user can upload a resume file via the profile endpoint.
    """
    user = user_factory()
    client = api_client_factory(user=user)

    url = reverse("community:userprofile-detail", kwargs={"username": user.username})

    payload = {"resume": resume_file}
    response = client.patch(url, payload, format="multipart")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["resume"] is not None

    # Verify DB
    user.profile.refresh_from_db()
    # UPDATED CHECK: Verify name contains the original name and ends with .pdf
    assert "test_resume" in user.profile.resume.name
    assert user.profile.resume.name.endswith(".pdf")

    # Verify file exists on disk
    assert os.path.exists(user.profile.resume.path)

    # Cleanup
    if user.profile.resume:
        user.profile.resume.delete()


def test_delete_resume(api_client_factory, user_factory, resume_file):
    """
    Test that a user can delete their resume by sending null.
    """
    user = user_factory()
    client = api_client_factory(user=user)

    # 1. Setup: Upload a resume first directly to the profile
    user.profile.resume = resume_file
    user.profile.save()
    assert user.profile.resume

    # 2. Action: Send null to delete it
    url = reverse("community:userprofile-detail", kwargs={"username": user.username})
    payload = {"resume": None}
    response = client.patch(url, payload, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["resume"] is None

    # Verify DB
    user.profile.refresh_from_db()
    assert not user.profile.resume
