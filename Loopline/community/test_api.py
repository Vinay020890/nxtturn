import pytest
import json
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from community.models import StatusPost, Report, Comment, Group, GroupJoinRequest, GroupBlock, Notification, Poll, PollOption 
from rest_framework import status
from django.contrib.auth.models import User

# This is a convenient way to apply the @pytest.mark.django_db decorator
# to every single test function in this file. We know all API tests
# will need the database, so this saves us from typing it repeatedly.
pytestmark = pytest.mark.django_db


def test_unauthenticated_user_cannot_list_posts():
    """
    Verifies that a user who is not logged in receives a 401 Unauthorized
    error when trying to access the main posts list endpoint.
    """
    # 1. ARRANGE: 
    # APIClient simulates a web client (like a browser or Axios).
    # By default, it's an anonymous, logged-out user.
    client = APIClient()

    # 2. ACT: 
    # We use the client to make a GET request to our API endpoint.
    # This is exactly what the frontend would do to fetch the feed.
    response = client.get('/api/posts/')

    # 3. ASSERT: 
    # We check the status code of the response. A '401' code is the
    # standard way for an API to say "You are not logged in."
    assert response.status_code == status.HTTP_401_UNAUTHORIZED # Adjusted to match current DRF behavior


def test_authenticated_user_can_list_posts():
    """
    Verifies that a logged-in user CAN successfully access the
    posts list endpoint and receives a 200 OK status code.
    """
    # 1. ARRANGE:
    # First, we need a user to log in as.
    User = get_user_model()
    user = User.objects.create_user(username='testuser', password='password123')
    
    # Then, we create a client.
    client = APIClient()
    
    # This is the key step: we explicitly authenticate the client as our user.
    # The `force_authenticate` method simulates a successful login.
    client.force_authenticate(user=user)

    # 2. ACT:
    # Now, this GET request is being made by an authenticated user.
    response = client.get('/api/posts/')

    # 3. ASSERT:
    # We expect a '200 OK' because a logged-in user should be allowed to see the feed.
    assert response.status_code == 200

def test_user_cannot_delete_another_users_post():
    """
    Verifies that an authenticated user receives a 403 Forbidden or 404 Not Found
    error when trying to delete a post that they do not own.
    """
    # 1. ARRANGE: We need two different users to simulate the scenario.
    User = get_user_model()
    post_owner = User.objects.create_user(username='owner', password='password123')
    attacker = User.objects.create_user(username='attacker', password='password123')

    # The 'post_owner' creates the content.
    post = StatusPost.objects.create(author=post_owner, content="This is my post and should be safe.")
    
    # Create our test client and log them in as the 'attacker'.
    client = APIClient()
    client.force_authenticate(user=attacker)

    # 2. ACT: The logged-in 'attacker' attempts to send a DELETE request
    # to the endpoint for the other user's post.
    response = client.delete(f'/api/posts/{post.id}/')

    # 3. ASSERT: The request should be denied.
    # A 403 Forbidden is the most technically correct response, but some
    # views return a 404 Not Found to avoid revealing that the post exists.
    # Checking for either makes our test more robust.
    assert response.status_code in [403, 404]

    # As a final check, we assert that the post definitely still exists in the database.
    # This proves the DELETE operation failed completely.
    assert StatusPost.objects.filter(id=post.id).exists()

def test_user_can_delete_own_post():
    """
    Verifies that an authenticated user can successfully delete their own post.
    """
    # 1. ARRANGE: We only need one user for this test.
    User = get_user_model()
    user = User.objects.create_user(username='owner', password='password123')

    # The user creates a post.
    post = StatusPost.objects.create(author=user, content="This is my post to delete.")
    
    # Create a client and authenticate it as the post's owner.
    client = APIClient()
    client.force_authenticate(user=user)

    # 2. ACT: The owner sends a DELETE request to their own post's URL.
    response = client.delete(f'/api/posts/{post.id}/')

    # 3. ASSERT: The request should be successful.
    # The standard status code for a successful DELETE with no body is 204 No Content.
    assert response.status_code == 204

    # Also, assert that the post has been removed from the database.
    assert not StatusPost.objects.filter(id=post.id).exists()

def test_user_can_create_post():
    """
    Verifies that an authenticated user can create a new StatusPost.
    """
    # 1. ARRANGE
    User = get_user_model()
    user = User.objects.create_user(username='poster', password='password123')
    
    client = APIClient()
    client.force_authenticate(user=user)
    
    # This dictionary represents the JSON data the frontend would send.
    post_data = {
        'content': 'This is a brand new post from an API test!'
    }
    
    # Check that there are no posts to begin with.
    assert StatusPost.objects.count() == 0

    # 2. ACT: Send a POST request to the list endpoint with the new data.
    response = client.post('/api/posts/', post_data, format='json')

    # 3. ASSERT
    # A successful creation should return a 201 Created status code.
    assert response.status_code == 201
    
    # There should now be one post in the database.
    assert StatusPost.objects.count() == 1
    
    # The post in the database should have the correct content and author.
    new_post = StatusPost.objects.first()
    assert new_post.content == post_data['content']
    assert new_post.author == user

def test_post_list_returns_correct_data():
    """
    Verifies that the GET /api/posts/ endpoint returns a list containing
    the posts that have been created.
    """
    # 1. ARRANGE
    User = get_user_model()
    user = User.objects.create_user(username='reader', password='password123')
    
    # Create a specific post that we can look for in the API response.
    post_content = "This is the content we expect to find."
    StatusPost.objects.create(author=user, content=post_content)

    client = APIClient()
    client.force_authenticate(user=user)

    # 2. ACT: Get the list of posts from the API.
    response = client.get('/api/posts/')

    # 3. ASSERT
    # First, ensure the request was successful.
    assert response.status_code == 200
    
    # The response data is a dictionary for paginated results. The actual
    # list of posts is in the 'results' key.
    response_data = response.json()
    
    # Check that the API returned exactly one post.
    assert len(response_data['results']) == 1
    
    # Check that the content of the post in the response is correct.
    retrieved_post = response_data['results'][0]
    assert retrieved_post['content'] == post_content
    assert retrieved_post['author']['username'] == user.username

def test_user_can_update_own_post():
    """
    Verifies that a user can successfully update their own post using PATCH.
    """
    # 1. ARRANGE
    User = get_user_model()
    user = User.objects.create_user(username='updater', password='password123')
    post = StatusPost.objects.create(author=user, content="Original content.")
    
    client = APIClient()
    client.force_authenticate(user=user)
    
    updated_data = {
        'content': 'This content has been updated!'
    }

    # 2. ACT: Send a PATCH request with the new data.
    response = client.patch(f'/api/posts/{post.id}/', updated_data, format='json')

    # 3. ASSERT
    assert response.status_code == 200 # A successful PATCH returns 200 OK.
    
    # Refresh the post object from the database to get the latest data.
    post.refresh_from_db()
    
    # Check that the content was actually updated.
    assert post.content == updated_data['content']

def test_user_cannot_update_another_users_post():
    """
    Verifies that a user cannot update a post they do not own.
    """
    # 1. ARRANGE
    User = get_user_model()
    post_owner = User.objects.create_user(username='owner_2', password='password123')
    attacker = User.objects.create_user(username='attacker_2', password='password123')
    post = StatusPost.objects.create(author=post_owner, content="Original content.")
    
    client = APIClient()
    client.force_authenticate(user=attacker)
    
    updated_data = {
        'content': 'Attempting to overwrite content.'
    }

    # 2. ACT: The 'attacker' attempts to update the 'post_owner's post.
    response = client.patch(f'/api/posts/{post.id}/', updated_data, format='json')

    # 3. ASSERT
    assert response.status_code in [403, 404] # Should be forbidden or not found.
    
    # Verify the post content in the database has NOT changed.
    post.refresh_from_db()
    assert post.content == "Original content."

# Make sure ContentType is imported at the top of the file:
# from django.contrib.contenttypes.models import ContentType

def test_user_can_report_post():
    """
    Verifies that an authenticated user can successfully report a post.
    """
    # 1. ARRANGE
    User = get_user_model()
    post_owner = User.objects.create_user(username='post_owner_2', password='password123')
    reporter = User.objects.create_user(username='reporter', password='password123')
    post_to_report = StatusPost.objects.create(author=post_owner, content="Some content to report.")

    client = APIClient()
    client.force_authenticate(user=reporter)

    # The data sent in the body now only contains the 'reason' and optional 'details'.
    report_data = {
        'reason': 'SPAM', # Using one of the likely choices from your model
        'details': 'This is a test report reason.'
    }

    # Get the ContentType object for the StatusPost model to build the URL.
    from django.contrib.contenttypes.models import ContentType
    post_content_type = ContentType.objects.get_for_model(StatusPost)

    # Construct the URL that matches your urls.py file.
    report_url = f'/api/content/{post_content_type.id}/{post_to_report.id}/report/'
    
    assert Report.objects.count() == 0

    # 2. ACT: Send the POST request to the correct, existing URL.
    response = client.post(report_url, report_data, format='json')

    # 3. ASSERT
    assert response.status_code == 201 # Successful creation.
    
    assert Report.objects.count() == 1
    
    new_report = Report.objects.first()
    assert new_report.reporter == reporter
    assert new_report.reason == report_data['reason']
    assert new_report.content_object == post_to_report

def test_user_can_create_comment_on_post():
    """
    Verifies that an authenticated user can create a new Comment on a StatusPost.
    """
    # 1. ARRANGE
    User = get_user_model()
    post_owner = User.objects.create_user(username='post_owner_3', password='password123')
    commenter = User.objects.create_user(username='commenter', password='password123')
    post = StatusPost.objects.create(author=post_owner, content="A post to be commented on.")

    client = APIClient()
    client.force_authenticate(user=commenter)

    comment_data = {
        'content': 'This is a new test comment!'
    }

    # The URL for creating a comment is nested under the object it belongs to.
    # The content_type here is the lowercase model name.
    comment_url = f'/api/comments/statuspost/{post.id}/'

    assert Comment.objects.count() == 0

    # 2. ACT: Send a POST request to the comment creation URL.
    response = client.post(comment_url, comment_data, format='json')

    # 3. ASSERT
    assert response.status_code == 201 # Successful creation.
    
    assert Comment.objects.count() == 1
    
    new_comment = Comment.objects.first()
    assert new_comment.author == commenter
    assert new_comment.content == comment_data['content']
    # Verify it's linked to the correct post.
    assert new_comment.content_object == post

def test_user_cannot_delete_another_users_comment():
    """
    Verifies a user cannot delete a comment they do not own.
    """
    # 1. ARRANGE
    User = get_user_model()
    comment_owner = User.objects.create_user(username='comment_owner', password='password123')
    attacker = User.objects.create_user(username='comment_attacker', password='password123')
    post = StatusPost.objects.create(author=comment_owner, content="A post.")
    comment = Comment.objects.create(author=comment_owner, content_object=post, content="A comment to attack.")

    client = APIClient()
    client.force_authenticate(user=attacker)

    # 2. ACT: The attacker attempts to delete the other user's comment.
    response = client.delete(f'/api/comments/{comment.id}/')

    # 3. ASSERT
    assert response.status_code in [403, 404]
    assert Comment.objects.filter(id=comment.id).exists()

def test_user_can_delete_own_comment():
    """
    Verifies a user can successfully delete their own comment.
    """
    # 1. ARRANGE
    User = get_user_model()
    user = User.objects.create_user(username='comment_deleter', password='password123')
    post = StatusPost.objects.create(author=user, content="Another post.")
    comment = Comment.objects.create(author=user, content_object=post, content="This comment will be deleted.")

    client = APIClient()
    client.force_authenticate(user=user)

    # 2. ACT: The owner of the comment deletes it.
    response = client.delete(f'/api/comments/{comment.id}/')

    # 3. ASSERT
    assert response.status_code == 204 # Successful deletion.
    assert not Comment.objects.filter(id=comment.id).exists()

def test_user_can_update_own_comment():
    """
    Verifies a user can successfully update their own comment.
    """
    # 1. ARRANGE
    User = get_user_model()
    user = User.objects.create_user(username='comment_updater', password='password123')
    post = StatusPost.objects.create(author=user, content="A post.")
    comment = Comment.objects.create(author=user, content_object=post, content="Original comment.")
    
    client = APIClient()
    client.force_authenticate(user=user)
    
    updated_data = {
        'content': 'This comment has been updated.'
    }

    # 2. ACT: Send a PATCH request to update the comment.
    response = client.patch(f'/api/comments/{comment.id}/', updated_data, format='json')

    # 3. ASSERT
    assert response.status_code == 200 # Successful update.
    comment.refresh_from_db()
    assert comment.content == updated_data['content']

def test_user_cannot_update_another_users_comment():
    """
    Verifies a user cannot update a comment they do not own.
    """
    # 1. ARRANGE
    User = get_user_model()
    comment_owner = User.objects.create_user(username='comment_owner_2', password='password123')
    attacker = User.objects.create_user(username='comment_attacker_2', password='password123')
    post = StatusPost.objects.create(author=comment_owner, content="Another post.")
    comment = Comment.objects.create(author=comment_owner, content_object=post, content="Original comment.")

    client = APIClient()
    client.force_authenticate(user=attacker)
    
    updated_data = {
        'content': 'Trying to hack this comment.'
    }

    # 2. ACT: The attacker attempts to update the comment.
    response = client.patch(f'/api/comments/{comment.id}/', updated_data, format='json')

    # 3. ASSERT
    assert response.status_code in [403, 404]
    comment.refresh_from_db()
    assert comment.content == "Original comment."

def test_user_can_report_comment():
    """
    Verifies that an authenticated user can successfully report a comment.
    """
    # 1. ARRANGE
    User = get_user_model()
    comment_owner = User.objects.create_user(username='comment_owner_3', password='password123')
    reporter = User.objects.create_user(username='reporter_2', password='password123')
    post = StatusPost.objects.create(author=comment_owner, content="A post.")
    comment_to_report = Comment.objects.create(
        author=comment_owner, 
        content_object=post, 
        content="This comment will be reported."
    )

    client = APIClient()
    client.force_authenticate(user=reporter)

    report_data = {
        'reason': 'HATE_SPEECH',
        'details': 'This is a test report for a comment.'
    }

    # Get the ContentType for the Comment model to build the URL.
    comment_content_type = ContentType.objects.get_for_model(Comment)

    # Construct the URL that matches your urls.py file.
    report_url = f'/api/content/{comment_content_type.id}/{comment_to_report.id}/report/'
    
    assert Report.objects.count() == 0

    # 2. ACT: Send a POST request to the report creation endpoint for the comment.
    response = client.post(report_url, report_data, format='json')

    # 3. ASSERT
    assert response.status_code == 201 # Successful creation.
    
    assert Report.objects.count() == 1
    
    new_report = Report.objects.first()
    assert new_report.reporter == reporter
    # Check that the report is correctly linked to the COMMENT, not the post.
    assert new_report.content_object == comment_to_report

def test_user_can_create_reply_to_comment():
    """
    Verifies that an authenticated user can create a reply to a comment.
    """
    # 1. ARRANGE
    User = get_user_model()
    post_owner = User.objects.create_user(username='post_owner_4', password='password123')
    comment_author = User.objects.create_user(username='comment_author_4', password='password123')
    replier = User.objects.create_user(username='replier', password='password123')
    
    post = StatusPost.objects.create(author=post_owner, content="A post for reply testing.")
    parent_comment = Comment.objects.create(author=comment_author, content_object=post, content="The parent comment.")

    client = APIClient()
    client.force_authenticate(user=replier)

    # When creating a reply, the frontend must specify the parent comment's ID.
    reply_data = {
        'content': 'This is a brand new reply!',
        'parent': parent_comment.id
    }

    # The URL for creating a reply is the same as for a comment.
    reply_url = f'/api/comments/statuspost/{post.id}/'

    # 2. ACT: Send a POST request to the comment creation URL with parent data.
    response = client.post(reply_url, reply_data, format='json')

    # 3. ASSERT
    assert response.status_code == 201
    
    # We created two comments in total (parent and reply).
    assert Comment.objects.count() == 2
    
    new_reply = Comment.objects.get(content=reply_data['content'])
    assert new_reply.author == replier
    assert new_reply.parent == parent_comment

def test_user_cannot_delete_another_users_reply():
    """
    Verifies a user cannot delete a reply they do not own.
    """
    # 1. ARRANGE
    User = get_user_model()
    reply_owner = User.objects.create_user(username='reply_owner', password='password123')
    attacker = User.objects.create_user(username='reply_attacker', password='password123')
    post = StatusPost.objects.create(author=reply_owner, content="A post.")
    parent_comment = Comment.objects.create(author=reply_owner, content_object=post, content="Parent comment.")
    reply = Comment.objects.create(author=reply_owner, content_object=post, content="A reply to attack.", parent=parent_comment)

    client = APIClient()
    client.force_authenticate(user=attacker)

    # 2. ACT: The attacker attempts to delete the other user's reply.
    # The endpoint is the same as for a regular comment.
    response = client.delete(f'/api/comments/{reply.id}/')

    # 3. ASSERT
    assert response.status_code in [403, 404]
    assert Comment.objects.filter(id=reply.id).exists()

def test_user_can_delete_own_reply():
    """
    Verifies a user can successfully delete their own reply.
    """
    # 1. ARRANGE
    User = get_user_model()
    user = User.objects.create_user(username='reply_deleter', password='password123')
    post = StatusPost.objects.create(author=user, content="Another post.")
    parent_comment = Comment.objects.create(author=user, content_object=post, content="Parent comment.")
    reply = Comment.objects.create(author=user, content_object=post, content="This reply will be deleted.", parent=parent_comment)

    client = APIClient()
    client.force_authenticate(user=user)

    # 2. ACT: The owner of the reply deletes it.
    response = client.delete(f'/api/comments/{reply.id}/')

    # 3. ASSERT
    assert response.status_code == 204
    assert not Comment.objects.filter(id=reply.id).exists()

def test_user_can_update_own_reply():
    """
    Verifies a user can successfully update their own reply.
    """
    # 1. ARRANGE
    User = get_user_model()
    user = User.objects.create_user(username='reply_updater', password='password123')
    post = StatusPost.objects.create(author=user, content="A post.")
    parent_comment = Comment.objects.create(author=user, content_object=post, content="Parent comment.")
    reply = Comment.objects.create(author=user, content_object=post, content="Original reply.", parent=parent_comment)

    client = APIClient()
    client.force_authenticate(user=user)
    
    updated_data = {
        'content': 'This reply has been updated.'
    }

    # 2. ACT: Send a PATCH request to update the reply.
    response = client.patch(f'/api/comments/{reply.id}/', updated_data, format='json')

    # 3. ASSERT
    assert response.status_code == 200
    reply.refresh_from_db()
    assert reply.content == updated_data['content']

def test_user_cannot_update_another_users_reply():
    """
    Verifies a user cannot update a reply they do not own.
    """
    # 1. ARRANGE
    User = get_user_model()
    reply_owner = User.objects.create_user(username='reply_owner_2', password='password123')
    attacker = User.objects.create_user(username='reply_attacker_2', password='password123')
    post = StatusPost.objects.create(author=reply_owner, content="Another post.")
    parent_comment = Comment.objects.create(author=reply_owner, content_object=post, content="Parent comment.")
    reply = Comment.objects.create(author=reply_owner, content_object=post, content="Original reply.", parent=parent_comment)

    client = APIClient()
    client.force_authenticate(user=attacker)
    
    updated_data = {
        'content': 'Trying to hack this reply.'
    }

    # 2. ACT: The attacker attempts to update the reply.
    response = client.patch(f'/api/comments/{reply.id}/', updated_data, format='json')

    # 3. ASSERT
    assert response.status_code in [403, 404]
    reply.refresh_from_db()
    assert reply.content == "Original reply."

def test_user_can_report_reply():
    """
    Verifies that an authenticated user can successfully report a reply.
    """
    # 1. ARRANGE
    User = get_user_model()
    reply_owner = User.objects.create_user(username='reply_owner_3', password='password123')
    reporter = User.objects.create_user(username='reporter_3', password='password123')
    post = StatusPost.objects.create(author=reply_owner, content="A post.")
    parent_comment = Comment.objects.create(author=reply_owner, content_object=post, content="Parent comment.")
    reply_to_report = Comment.objects.create(
        author=reply_owner, 
        content_object=post, 
        content="This reply will be reported.",
        parent=parent_comment
    )

    client = APIClient()
    client.force_authenticate(user=reporter)

    report_data = {
        'reason': 'SPAM',
        'details': 'This is a test report for a reply.'
    }

    # Get the ContentType for the Comment model (same as for a top-level comment).
    reply_content_type = ContentType.objects.get_for_model(Comment)

    # Construct the URL.
    report_url = f'/api/content/{reply_content_type.id}/{reply_to_report.id}/report/'
    
    # We start with no reports.
    assert Report.objects.count() == 0

    # 2. ACT: Send a POST request to the report creation endpoint for the reply.
    response = client.post(report_url, report_data, format='json')

    # 3. ASSERT
    assert response.status_code == 201
    
    assert Report.objects.count() == 1
    
    new_report = Report.objects.first()
    assert new_report.reporter == reporter
    # Check that the report is correctly linked to the REPLY.
    assert new_report.content_object == reply_to_report

def test_user_can_toggle_saved_post():
    """
    Verifies a user can save and unsave a post.
    """
    # 1. ARRANGE
    User = get_user_model()
    post_owner = User.objects.create_user(username='post_owner_5', password='password123')
    saver = User.objects.create_user(username='saver', password='password123')
    post = StatusPost.objects.create(author=post_owner, content="A post to be saved.")
    
    client = APIClient()
    client.force_authenticate(user=saver)
    
    save_url = f'/api/posts/{post.id}/save/'

    # --- ACTION 1: SAVE THE POST ---
    
    # Pre-condition: The user has not saved any posts.
    assert saver.profile.saved_posts.count() == 0

    # 2. ACT (SAVE): Send a POST request to the save toggle endpoint.
    response_save = client.post(save_url)

    # 3. ASSERT (SAVE)
    assert response_save.status_code == 200
    # The user should now have 1 saved post.
    assert saver.profile.saved_posts.count() == 1
    assert saver.profile.saved_posts.first() == post
    
    # The API response should indicate the post is now saved.
    assert response_save.json()['is_saved'] == True

    # --- ACTION 2: UNSAVE THE POST ---

    # 4. ACT (UNSAVE): Send the exact same POST request again to toggle it off.
    response_unsave = client.post(save_url)

    # 5. ASSERT (UNSAVE)
    assert response_unsave.status_code == 200
    # The user should now have 0 saved posts.
    assert saver.profile.saved_posts.count() == 0
    
    # The API response should indicate the post is no longer saved.
    assert response_unsave.json()['is_saved'] == False

def test_user_can_list_own_saved_posts():
    """
    Verifies that the saved posts endpoint only returns posts saved
    by the authenticated user.
    """
    # 1. ARRANGE: We need two users to ensure data is properly isolated.
    User = get_user_model()
    user_a = User.objects.create_user(username='user_a', password='password123')
    user_b = User.objects.create_user(username='user_b', password='password123')
    
    # Create two posts.
    post_1 = StatusPost.objects.create(author=user_a, content="Post number 1.")
    post_2 = StatusPost.objects.create(author=user_b, content="Post number 2.")
    
    # User A saves post 2.
    user_a.profile.saved_posts.add(post_2)

    # User B saves post 1.
    user_b.profile.saved_posts.add(post_1)
    
    # Create a client and authenticate as User A.
    client = APIClient()
    client.force_authenticate(user=user_a)

    # 2. ACT: User A requests their list of saved posts.
    response = client.get('/api/posts/saved/')

    # 3. ASSERT
    assert response.status_code == 200
    
    response_data = response.json()
    
    # The API should return exactly one post.
    assert len(response_data['results']) == 1
    
    # That one post must be post_2, which is the one User A saved.
    saved_post = response_data['results'][0]
    assert saved_post['id'] == post_2.id

@pytest.mark.django_db
def test_user_must_request_to_join_private_group(user_factory, api_client_factory):
    """
    Tests that a user cannot instantly join a private group. Instead,
    a join request should be created.
    """
    # --- Arrange ---
    # 1. Create the group owner and the user who will request to join.
    group_owner = user_factory()
    requester = user_factory()

    # 2. Create a private group owned by the group_owner.
    private_group = Group.objects.create(
        creator=group_owner,
        name="Exclusive Developers",
        privacy_level='private'
    )

    # 3. Authenticate the client as the user requesting to join.
    client = api_client_factory(user=requester)
    url = f"/api/groups/{private_group.slug}/membership/"

    # --- Act ---
    # 4. The requester attempts to join the group.
    response = client.post(url)

    # --- Assert ---
    # 5. Check that the request was accepted by the server.
    assert response.status_code == 201, "The API should accept the request."

    # 6. CRITICAL: The requester should NOT be a member of the group yet.
    # This is the assertion we expect to FAIL initially.
    assert requester not in private_group.members.all(), "User should not be added directly to a private group."

    # 7. CRITICAL: A GroupJoinRequest object must have been created.
    assert GroupJoinRequest.objects.filter(user=requester, group=private_group).exists(), "A join request should be created."

    # 8. Verify the status of the newly created request is 'pending'.
    join_request = GroupJoinRequest.objects.get(user=requester, group=private_group)
    assert join_request.status == 'pending', "The request status should be 'pending'."

# === TESTS FOR PRIVATE GROUP JOIN REQUEST MANAGEMENT (STEP 5) ===
# =========================================================================

# =========================================================================
# === SIMPLIFIED TESTS FOR PRIVATE GROUP JOIN REQUEST MANAGEMENT ===
# =========================================================================

@pytest.mark.django_db
def test_group_creator_can_list_pending_requests(join_request_scenario, api_client_factory):
    """Verifies the group creator can successfully list pending join requests."""
    # --- Arrange ---
    # The 'join_request_scenario' fixture handles all the setup.
    scenario = join_request_scenario
    client = api_client_factory(user=scenario['creator'])
    url = f"/api/groups/{scenario['group'].slug}/requests/"

    # --- Act ---
    response = client.get(url)

    # --- Assert ---
    assert response.status_code == 200
    results = response.json()['results']
    assert len(results) == 1
    assert results[0]['user']['username'] == scenario['requester'].username

@pytest.mark.django_db
def test_non_creator_cannot_list_pending_requests(join_request_scenario, api_client_factory, user_factory):
    """Verifies a random user gets a 403 Forbidden error."""
    # --- Arrange ---
    scenario = join_request_scenario
    random_user = user_factory() # We only need to create the user who shouldn't have access.
    client = api_client_factory(user=random_user)
    url = f"/api/groups/{scenario['group'].slug}/requests/"

    # --- Act ---
    response = client.get(url)

    # --- Assert ---
    assert response.status_code == 403

@pytest.mark.django_db
def test_group_creator_can_approve_join_request(join_request_scenario, api_client_factory):
    """Verifies the creator can approve a request, adding the user to the group."""
    # --- Arrange ---
    scenario = join_request_scenario
    client = api_client_factory(user=scenario['creator'])
    url = f"/api/groups/{scenario['group'].slug}/requests/{scenario['request'].id}/"
    payload = {"action": "approve"}

    # --- Act ---
    response = client.patch(url, data=payload)

    # --- Assert ---
    assert response.status_code == 200
    scenario['group'].refresh_from_db()
    scenario['request'].refresh_from_db()
    assert scenario['requester'] in scenario['group'].members.all()
    assert scenario['request'].status == 'approved'

# In community/test_api.py

@pytest.mark.django_db
def test_group_creator_can_deny_join_request(join_request_scenario, api_client_factory):
    """
    Verifies the creator can deny a request, which DELETES the request
    but does NOT add the user or block them.
    """
    # --- Arrange ---
    scenario = join_request_scenario
    client = api_client_factory(user=scenario['creator'])
    url = f"/api/groups/{scenario['group'].slug}/requests/{scenario['request'].id}/"
    payload = {"action": "deny"}

    # --- Act ---
    response = client.patch(url, data=payload)

    # --- Assert ---
    assert response.status_code == 200
    
    # --- THIS IS THE FIX ---
    # The request object should no longer exist in the database.
    assert not GroupJoinRequest.objects.filter(id=scenario['request'].id).exists()
    
    # Verify the user was NOT added to the group.
    scenario['group'].refresh_from_db()
    assert scenario['requester'] not in scenario['group'].members.all()
    
    # Verify the user was NOT blocked.
    assert not GroupBlock.objects.filter(group=scenario['group'], user=scenario['requester']).exists()

# === TESTS FOR GROUP MANAGEMENT (ListView & RetrieveView) ===
# =========================================================================

def test_unauthenticated_user_cannot_create_group(api_client):
    """
    Verify that an unauthenticated user receives a 401 Unauthorized
    error when attempting to create a group.
    """
    group_data = {
        'name': 'Unauthenticated Group Test',
        'description': 'This should not be created.',
        'privacy_level': 'public'
    }
    response = api_client.post('/api/groups/', group_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert Group.objects.count() == 0

def test_authenticated_user_can_create_group(user_factory, api_client_factory):
    """
    Verify that an authenticated user can successfully create a new group.
    """
    # Arrange: Create a user and an authenticated client for them.
    user = user_factory()
    client = api_client_factory(user=user)

    group_data = {
        'name': 'My Awesome New Group',
        'description': 'A group created via an API test.',
        'privacy_level': 'public'
    }

    # Pre-condition check: Ensure no groups exist yet.
    assert Group.objects.count() == 0

    # Act: Send the POST request to the create endpoint.
    response = client.post('/api/groups/', group_data)

    # Assert: Check for a successful creation.
    assert response.status_code == status.HTTP_201_CREATED
    assert Group.objects.count() == 1

    # Verify the details of the created group.
    new_group = Group.objects.first()
    assert new_group.name == group_data['name']
    assert new_group.creator == user
    # On creation, the creator should automatically be a member.
    assert user in new_group.members.all()

def test_user_can_list_groups(user_factory, api_client_factory):
    """
    Verifies that an authenticated user can retrieve a paginated list of groups.
    """
    # Arrange: Create a user to perform the action and a creator for the groups.
    lister_user = user_factory()
    creator_user = user_factory()
    client = api_client_factory(user=lister_user)

    # Create a couple of groups to ensure the list is not empty.
    Group.objects.create(creator=creator_user, name="Python Developers", privacy_level='public')
    Group.objects.create(creator=creator_user, name="Django Ninjas", privacy_level='private')

    # Act: Make a GET request to the group list endpoint.
    response = client.get('/api/groups/')

    # Assert: Check for a successful response.
    assert response.status_code == status.HTTP_200_OK

    # The response is paginated, so our data is in the 'results' key.
    results = response.json()['results']
    assert len(results) == 2

    # Verify that the names of the groups are present in the response.
    # The default ordering isn't guaranteed, so we check for presence.
    group_names = {group['name'] for group in results}
    assert "Python Developers" in group_names
    assert "Django Ninjas" in group_names

def test_user_can_search_groups_by_name(user_factory, api_client_factory):
    """
    Verifies that the group list can be filtered using a search query parameter.
    """
    # Arrange
    user = user_factory()
    client = api_client_factory(user=user)

    # Create a set of groups with specific names for filtering.
    Group.objects.create(creator=user, name="Python Developers")
    Group.objects.create(creator=user, name="Advanced Pythonistas")
    Group.objects.create(creator=user, name="Django Fan Club") # This should not appear in the search result.

    # Act: Perform a GET request with a search query.
    response = client.get('/api/groups/?search=Python')

    # Assert
    assert response.status_code == status.HTTP_200_OK

    results = response.json()['results']
    
    # We expect only the two groups with "Python" in their name.
    assert len(results) == 2

    # Verify the names of the groups that were returned.
    group_names = {group['name'] for group in results}
    assert "Python Developers" in group_names
    assert "Advanced Pythonistas" in group_names
    assert "Django Fan Club" not in group_names

# === TESTS FOR GROUP MANAGEMENT (Retrieve/Update/Delete) ===
# =========================================================================

def test_user_can_retrieve_group_details(user_factory, api_client_factory):
    """
    Verifies that a user can successfully retrieve the details of a single group.
    """
    # Arrange
    user = user_factory()
    client = api_client_factory(user=user)

    # Create a specific group to fetch.
    group = Group.objects.create(creator=user, name="Test Group for Retrieval", description="Details here.")
    
    url = f'/api/groups/{group.slug}/'

    # Act: Make a GET request to the group's detail URL.
    response = client.get(url)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    
    # Verify the data in the response matches the group we created.
    response_data = response.json()
    assert response_data['name'] == group.name
    assert response_data['description'] == group.description
    assert response_data['slug'] == group.slug

# ================== REPLACE THE OLD FAILING TEST WITH THIS NEW VERSION ==================
def test_non_member_sees_limited_private_group_details(user_factory, api_client_factory):
    """
    Verifies that a non-member can retrieve a private group's basic details,
    but sensitive information like the full member list is hidden.
    """
    # Arrange
    group_creator = user_factory()
    random_user = user_factory() # This user will try to access the group.
    
    # Create another member to ensure the member list isn't empty in the database.
    another_member = user_factory()

    private_group = Group.objects.create(
        creator=group_creator,
        name="Top Secret Private Group",
        privacy_level='private'
    )
    private_group.members.add(group_creator, another_member)

    # Authenticate as the random user (the non-member).
    client = api_client_factory(user=random_user)
    url = f'/api/groups/{private_group.slug}/'

    # Act: The non-member attempts to GET the private group's details.
    response = client.get(url)

    # Assert
    # The expected status code is now 200 OK, as we allow viewing basic details.
    assert response.status_code == status.HTTP_200_OK
    
    response_data = response.json()
    
    # Verify that basic, non-sensitive data is present.
    assert response_data['name'] == "Top Secret Private Group"
    assert response_data['creator']['username'] == group_creator.username
    
    # --- THIS IS THE CRITICAL SECURITY CHECK ---
    # Verify that the 'members' list in the API response is empty,
    # even though there are members in the database.
    assert response_data['members'] == []
# ====================================================================================


# Add this new test function

def test_member_can_see_full_private_group_details(user_factory, api_client_factory):
    """
    Verifies that a member of a private group CAN retrieve the full details,
    including the complete member list.
    """
    # Arrange
    group_creator = user_factory()
    group_member = user_factory() # This user will be the one making the request.

    private_group = Group.objects.create(
        creator=group_creator,
        name="The Inner Circle",
        privacy_level='private'
    )
    # Both users are members of the group.
    private_group.members.add(group_creator, group_member)

    # Authenticate as the regular group_member.
    client = api_client_factory(user=group_member)
    url = f'/api/groups/{private_group.slug}/'

    # Act: The member GETs the private group's details.
    response = client.get(url)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    
    response_data = response.json()
    
    # --- THIS IS THE CRITICAL VERIFICATION ---
    # The 'members' list in the API response should contain 2 members.
    assert len(response_data['members']) == 2
    
    # We can also check that the usernames are correct.
    member_usernames = {member['username'] for member in response_data['members']}
    assert group_creator.username in member_usernames
    assert group_member.username in member_usernames


def test_non_creator_cannot_update_group(user_factory, api_client_factory):
    """
    Verifies that a random authenticated user cannot update a group's details.
    """
    # Arrange
    group_creator = user_factory()
    random_user = user_factory()
    
    group = Group.objects.create(creator=group_creator, name="Original Name")
    
    # Authenticate as the random (non-creator) user.
    client = api_client_factory(user=random_user)
    
    url = f'/api/groups/{group.slug}/'
    update_data = {'name': 'Hacker trying to change name'}

    # Act: Attempt to PATCH the group's data.
    response = client.patch(url, update_data)

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    # Verify that the group's name did NOT change in the database.
    group.refresh_from_db()
    assert group.name == "Original Name"


def test_creator_can_update_group(user_factory, api_client_factory):
    """
    Verifies that the creator of a group can successfully update its details.
    """
    # Arrange
    creator = user_factory()
    
    group = Group.objects.create(creator=creator, name="Original Name", description="Original Desc.")
    
    # Authenticate as the group's creator.
    client = api_client_factory(user=creator)
    
    url = f'/api/groups/{group.slug}/'
    update_data = {
        'name': 'Updated Group Name',
        'description': 'This description has been updated.'
    }

    # Act: The creator sends a PATCH request with new data.
    response = client.patch(url, update_data)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    
    # Verify the data in the database has changed.
    group.refresh_from_db()
    assert group.name == update_data['name']
    assert group.description == update_data['description']

def test_non_creator_cannot_delete_group(user_factory, api_client_factory):
    """
    Verifies that a random authenticated user cannot delete a group.
    """
    # Arrange
    group_creator = user_factory()
    random_user = user_factory()
    
    group = Group.objects.create(creator=group_creator, name="A Group to Protect")
    
    # Authenticate as the non-creator.
    client = api_client_factory(user=random_user)
    
    url = f'/api/groups/{group.slug}/'

    # Act: Attempt to DELETE the group.
    response = client.delete(url)

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    # Verify the group still exists in the database.
    assert Group.objects.filter(pk=group.pk).exists()

def test_creator_can_delete_group(user_factory, api_client_factory):
    """
    Verifies that the creator of a group can successfully delete it.
    """
    # Arrange
    creator = user_factory()
    
    group = Group.objects.create(creator=creator, name="Group to be Deleted")
    
    # Authenticate as the group's creator.
    client = api_client_factory(user=creator)
    
    url = f'/api/groups/{group.slug}/'

    # Pre-condition check
    assert Group.objects.count() == 1

    # Act: The creator sends a DELETE request.
    response = client.delete(url)

    # Assert
    # A successful DELETE should return a 204 No Content response.
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify the group has been removed from the database.
    assert Group.objects.count() == 0

# === TESTS FOR GROUP OWNERSHIP TRANSFER ===
# =========================================================================

def test_creator_can_transfer_ownership(user_factory, api_client_factory):
    """
    Verifies that the creator can successfully transfer group ownership
    to another member of the group.
    """
    # Arrange
    creator = user_factory()
    new_owner = user_factory()
    
    group = Group.objects.create(creator=creator, name="Community Group")
    # The new owner must be a member of the group first.
    group.members.add(creator, new_owner)
    
    # Authenticate as the current creator.
    client = api_client_factory(user=creator)
    
    url = f'/api/groups/{group.slug}/transfer-ownership/'
    payload = {'new_owner_id': new_owner.id}

    # Act: The creator sends a POST request to transfer ownership.
    response = client.post(url, payload)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['detail'] == f"Ownership successfully transferred to {new_owner.username}."
    
    # Verify the creator has changed in the database.
    group.refresh_from_db()
    assert group.creator == new_owner

def test_non_creator_cannot_transfer_ownership(user_factory, api_client_factory):
    """
    Verifies that a user who is not the creator (even if they are a member)
    cannot transfer group ownership.
    """
    # Arrange
    creator = user_factory()
    imposter = user_factory() # This user will attempt the transfer
    new_owner = user_factory()
    
    group = Group.objects.create(creator=creator, name="Secure Group")
    # All three users are members
    group.members.add(creator, imposter, new_owner)
    
    # Authenticate as the IMPOSTER, not the creator.
    client = api_client_factory(user=imposter)
    
    url = f'/api/groups/{group.slug}/transfer-ownership/'
    payload = {'new_owner_id': new_owner.id}

    # Act: The non-creator attempts to transfer ownership.
    response = client.post(url, payload)

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    # Verify the creator did NOT change in the database.
    group.refresh_from_db()
    assert group.creator == creator

def test_creator_cannot_transfer_to_non_member(user_factory, api_client_factory):
    """
    Verifies that the creator cannot transfer ownership to a user who
    is not a member of the group.
    """
    # Arrange
    creator = user_factory()
    non_member = user_factory() # A user who is NOT in the group
    
    group = Group.objects.create(creator=creator, name="Members Only Club")
    # CRITICAL: The creator is a member, but `non_member` is NOT added.
    group.members.add(creator)
    
    # Authenticate as the creator.
    client = api_client_factory(user=creator)
    
    url = f'/api/groups/{group.slug}/transfer-ownership/'
    payload = {'new_owner_id': non_member.id}

    # Act: The creator attempts to transfer to the non-member.
    response = client.post(url, payload)

    # Assert
    # This is a validation error, so we expect a 400 Bad Request.
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == "The selected user is not a member of this group."
    
    # Verify the creator did not change.
    group.refresh_from_db()
    assert group.creator == creator

def test_creator_cannot_transfer_ownership_to_self(user_factory, api_client_factory):
    """
    Verifies that the creator cannot transfer ownership to themselves.
    """
    # Arrange
    creator = user_factory()
    
    group = Group.objects.create(creator=creator, name="Self-Owned Group")
    group.members.add(creator)
    
    # Authenticate as the creator.
    client = api_client_factory(user=creator)
    
    url = f'/api/groups/{group.slug}/transfer-ownership/'
    # The payload contains the creator's OWN ID.
    payload = {'new_owner_id': creator.id}

    # Act: The creator attempts to transfer to themselves.
    response = client.post(url, payload)

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == "You cannot transfer ownership to yourself."
    
    # Verify the creator did not change.
    group.refresh_from_db()
    assert group.creator == creator

# === TESTS FOR GROUP BLOCKING FUNCTIONALITY ===
# =========================================================================

def test_blocked_user_cannot_request_to_join_private_group(user_factory, api_client_factory):
    """
    Verifies that a user who has been blocked from a group receives a 403
    error when they attempt to send a new join request.
    """
    # Arrange
    group_creator = user_factory()
    blocked_user = user_factory()
    
    private_group = Group.objects.create(
        creator=group_creator,
        name="Fort Knox Group",
        privacy_level='private'
    )
    
    # Manually create the block record in the database.
    GroupBlock.objects.create(
        group=private_group,
        user=blocked_user,
        blocked_by=group_creator
    )
    
    # Authenticate as the user who is now blocked.
    client = api_client_factory(user=blocked_user)
    url = f'/api/groups/{private_group.slug}/membership/'
    
    # Pre-condition check
    assert GroupJoinRequest.objects.count() == 0

    # Act: The blocked user attempts to send a join request.
    response = client.post(url)

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    # Verify no new join request was created.
    assert GroupJoinRequest.objects.count() == 0

def test_creator_can_deny_and_block_request(join_request_scenario, api_client_factory):
    """
    Verifies that the creator can deny a request and simultaneously create a
    GroupBlock record to prevent the user from re-requesting.
    """
    # Arrange
    # The fixture sets up the creator, requester, group, and the initial join request.
    scenario = join_request_scenario
    client = api_client_factory(user=scenario['creator'])
    
    url = f"/api/groups/{scenario['group'].slug}/requests/{scenario['request'].id}/"
    payload = {"action": "deny_and_block"}
    
    # Pre-condition checks
    assert GroupBlock.objects.count() == 0
    assert GroupJoinRequest.objects.count() == 1

    # Act: The creator sends the 'deny_and_block' action.
    response = client.patch(url, data=payload)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == "Request denied and user blocked."
    
    # Verify the join request was deleted.
    # NOTE: For "deny", we decided the request should be DELETED, not just status changed.
    assert not GroupJoinRequest.objects.filter(id=scenario['request'].id).exists()
    
    # CRITICAL: Verify that a GroupBlock record was created.
    assert GroupBlock.objects.filter(
        group=scenario['group'],
        user=scenario['requester']
    ).exists()

# In community/test_api.py

# In community/test_api.py

def test_former_member_can_re_request_to_join_private_group(user_factory, api_client_factory):
    """
    Verifies that a user who joined, was approved, and then left a private
    group can successfully send a new join request, AND that this action
    creates a new notification for the group owner.
    """
    # Arrange
    creator = user_factory()
    former_member = user_factory()
    group = Group.objects.create(creator=creator, name="Rejoin Test Group", privacy_level='private')
    
    # 1. Simulate the original join request. This creates the first notification.
    request_obj = GroupJoinRequest.objects.create(group=group, user=former_member, status='pending')
    
    # Verify the initial notification for the owner exists.
    initial_notification = Notification.objects.get(
        recipient=creator,
        actor=former_member,
        notification_type=Notification.GROUP_JOIN_REQUEST
    )
    assert initial_notification is not None

    # 2. Simulate the owner APPROVING the request. This should delete the notification.
    # We do this manually instead of calling the API to keep the test focused.
    group.members.add(creator, former_member)
    request_obj.status = 'approved'
    request_obj.save()
    initial_notification.delete() # Replicating the logic from our view

    # 3. The user leaves the group.
    group.members.remove(former_member)
    assert former_member not in group.members.all()
    
    # Verify the initial notification is now gone.
    assert not Notification.objects.filter(id=initial_notification.id).exists()
    
    # 4. Authenticate as the former member for the re-request.
    client = api_client_factory(user=former_member)
    url = f'/api/groups/{group.slug}/membership/'

    # Act: The former member attempts to rejoin.
    response = client.post(url)
    
    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    
    request_obj.refresh_from_db()
    assert request_obj.status == 'pending'
    
    # CRITICAL: Verify that a NEW notification has been created for the re-request.
    assert Notification.objects.filter(
        recipient=creator,
        actor=former_member,
        notification_type=Notification.GROUP_JOIN_REQUEST
    ).count() == 1 # There should be exactly one such notification now.

# In community/test_api.py, inside the blocking tests section

def test_creator_can_list_blocked_users(user_factory, api_client_factory):
    """
    Verifies that the group creator can successfully retrieve a list of
    users who are blocked from their group.
    """
    # Arrange
    creator = user_factory()
    blocked_user = user_factory()
    group = Group.objects.create(creator=creator, name="Test Group")
    GroupBlock.objects.create(group=group, user=blocked_user, blocked_by=creator)
    
    client = api_client_factory(user=creator)
    url = f'/api/groups/{group.slug}/blocks/'

    # Act
    response = client.get(url)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    results = response.json()['results']
    assert len(results) == 1
    assert results[0]['user']['username'] == blocked_user.username

def test_non_creator_cannot_list_blocked_users(user_factory, api_client_factory):
    """
    Verifies that a random user (even a member) cannot see the blocked list.
    """
    # Arrange
    creator = user_factory()
    random_user = user_factory()
    group = Group.objects.create(creator=creator, name="Test Group")
    
    client = api_client_factory(user=random_user)
    url = f'/api/groups/{group.slug}/blocks/'

    # Act
    response = client.get(url)

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN

# In community/test_api.py, inside the blocking tests section

def test_creator_can_unblock_user(user_factory, api_client_factory):
    """
    Verifies that the group creator can successfully unblock a user by
    deleting the GroupBlock record.
    """
    # Arrange
    creator = user_factory()
    blocked_user = user_factory()
    group = Group.objects.create(creator=creator, name="Test Group")
    GroupBlock.objects.create(group=group, user=blocked_user, blocked_by=creator)
    
    assert GroupBlock.objects.count() == 1
    
    client = api_client_factory(user=creator)
    url = f'/api/groups/{group.slug}/blocks/{blocked_user.id}/'

    # Act
    response = client.delete(url)

    # Assert
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert GroupBlock.objects.count() == 0

def test_non_creator_cannot_unblock_user(user_factory, api_client_factory):
    """
    Verifies that a random user cannot unblock someone from a group.
    """
    # Arrange
    creator = user_factory()
    blocked_user = user_factory()
    random_user = user_factory()
    group = Group.objects.create(creator=creator, name="Test Group")
    GroupBlock.objects.create(group=group, user=blocked_user, blocked_by=creator)
    
    client = api_client_factory(user=random_user)
    url = f'/api/groups/{group.slug}/blocks/{blocked_user.id}/'

    # Act
    response = client.delete(url)

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert GroupBlock.objects.count() == 1

def test_unblocking_non_blocked_user_returns_404(user_factory, api_client_factory):
    """
    Verifies that trying to unblock a user who isn't blocked returns
    a 404 Not Found error.
    """
    # Arrange
    creator = user_factory()
    non_blocked_user = user_factory()
    group = Group.objects.create(creator=creator, name="Test Group")
    
    client = api_client_factory(user=creator)
    url = f'/api/groups/{group.slug}/blocks/{non_blocked_user.id}/'

    # Act
    response = client.delete(url)

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND

# =========================================================================
# === TESTS FOR POLL CREATION ===
# =========================================================================

# =========================================================================
# === TESTS FOR POLL CREATION (Corrected Version) ===
# =========================================================================

def test_member_can_create_valid_poll_in_group(user_factory, api_client_factory):
    """
    Ensure an authenticated group member can successfully create a poll post
    by POSTing to the main /api/posts/ endpoint with a group slug.
    """
    # Arrange
    creator = user_factory()
    group = Group.objects.create(creator=creator, name="Polling Group", privacy_level='public')
    group.members.add(creator)
    
    client = api_client_factory(user=creator)
    
    poll_dict = {
        "question": "What is the best feature of DRF?",
        "options": ["Serializers", "Viewsets", "Permissions"]
    }
    
    payload = {
        "group": group.slug,
        "poll_data": json.dumps(poll_dict) 
    }
    
    # Pre-condition checks using the correct model name: StatusPost
    assert StatusPost.objects.count() == 0
    assert Poll.objects.count() == 0

    # Act
    response = client.post('/api/posts/', payload, format='json')
    
    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    
    # Verify database state using the correct model name: StatusPost
    assert StatusPost.objects.count() == 1
    assert Poll.objects.count() == 1
    assert PollOption.objects.count() == 3
    
    # Verify content correctness using the correct model name: StatusPost
    new_post = StatusPost.objects.first()
    assert new_post.group == group
    assert hasattr(new_post, 'poll')
    
    new_poll = new_post.poll
    assert new_poll.question == poll_dict["question"]
    
    option_texts = list(new_poll.options.order_by('text').values_list('text', flat=True))
    expected_options = sorted(poll_dict["options"])
    assert option_texts == expected_options

def test_create_poll_with_insufficient_options_fails(user_factory, api_client_factory):
    """
    Ensure the API rejects a poll creation request with fewer than 2 options,
    based on the validation logic in StatusPostSerializer.
    """
    # Arrange
    user = user_factory()
    client = api_client_factory(user=user)
    
    poll_dict = {
        "question": "This poll should fail",
        "options": ["Only one option"] 
    }
    payload = {"poll_data": json.dumps(poll_dict)}

    # Act
    response = client.post('/api/posts/', payload, format='json')
    
    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "A poll must have at least two options." in str(response.data['poll_data'])
    
    # Use the correct model name: StatusPost
    assert StatusPost.objects.count() == 0
    assert Poll.objects.count() == 0

def test_create_poll_with_empty_question_fails(user_factory, api_client_factory):
    """
    Ensure the API rejects a poll creation request with an empty question.
    """
    # Arrange
    user = user_factory()
    client = api_client_factory(user=user)
    
    poll_dict = {
        "question": "   ",
        "options": ["Option A", "Option B"] 
    }
    payload = {"poll_data": json.dumps(poll_dict)}
    
    # Act
    response = client.post('/api/posts/', payload, format='json')
    
    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Poll question cannot be empty." in str(response.data['poll_data'])
    
    # Use the correct model name: StatusPost
    assert StatusPost.objects.count() == 0

def test_non_member_cannot_create_poll_in_group(user_factory, api_client_factory):
    """
    Ensure a user who is not a member of a group gets a 403 Forbidden error
    when trying to create a poll associated with that group.
    """
    # Arrange
    creator = user_factory()
    non_member = user_factory()
    group = Group.objects.create(creator=creator, name="Private Polling")
    
    client = api_client_factory(user=non_member)

    poll_dict = {
        "question": "This should be forbidden",
        "options": ["Yes", "No"] 
    }
    payload = {
        "group": group.slug,
        "poll_data": json.dumps(poll_dict)
    }

    # Act
    response = client.post('/api/posts/', payload, format='json')
    
    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    # Use the correct model name: StatusPost
    assert StatusPost.objects.count() == 0

# In C:\Users\Vinay\Project\Loopline\community\test_api.py
# Add this function alongside the other poll creation tests

def test_user_can_create_valid_poll_on_main_feed(user_factory, api_client_factory):
    """
    Ensure an authenticated user can create a poll post on the main feed,
    not associated with any group.
    """
    # Arrange
    user = user_factory()
    client = api_client_factory(user=user)
    
    poll_dict = {
        "question": "Which frontend framework do you prefer for personal projects?",
        "options": ["Vue.js", "React", "Svelte"]
    }
    
    # The payload is simpler: no "group" key is sent.
    payload = {
        "poll_data": json.dumps(poll_dict) 
    }
    
    # Pre-condition check
    assert StatusPost.objects.count() == 0

    # Act
    response = client.post('/api/posts/', payload, format='json')
    
    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    
    # Verify database state
    assert StatusPost.objects.count() == 1
    
    new_post = StatusPost.objects.first()
    
    # CRITICAL: Verify that the post is NOT associated with a group.
    assert new_post.group is None
    
    assert hasattr(new_post, 'poll')
    assert new_post.poll.question == poll_dict["question"]

# In C:\Users\Vinay\Project\Loopline\community\test_api.py

def test_join_request_to_private_group_creates_notification_for_owner(user_factory, api_client_factory):
    """
    Verifies that when a user requests to join a private group via the API,
    a Notification object is correctly created in the database for the group's owner.
    """
    # --- Arrange ---
    # 1. Create the necessary users and the private group.
    creator = user_factory()
    requester = user_factory()
    private_group = Group.objects.create(
        creator=creator, 
        name="Exclusive API Test Group", 
        privacy_level='private'
    )
    
    # 2. Authenticate the client as the user who will make the request.
    client = api_client_factory(user=requester)
    url = f"/api/groups/{private_group.slug}/membership/"
    
    # 3. Pre-condition: Assert that the database starts with no notifications.
    assert Notification.objects.count() == 0

    # --- Act ---
    # 4. Simulate the user action by making the API call to request to join.
    response = client.post(url)

    # --- Assert ---
    # 5. First, check that the API call itself was successful.
    assert response.status_code == status.HTTP_201_CREATED
    
    # 6. CRITICAL: Verify that exactly one notification was created in the database.
    assert Notification.objects.count() == 1
    
    notification = Notification.objects.first()
    
    # 7. Verify the contents of the notification are perfect.
    assert notification.recipient == creator
    assert notification.actor == requester
    assert notification.notification_type == Notification.GROUP_JOIN_REQUEST
    assert notification.target == private_group


def test_approving_join_request_creates_notification_for_requester(join_request_scenario, api_client_factory):
    """
    Verifies that when a group owner approves a join request via the API,
    a Notification object is correctly created for the user who made the request.
    """
    # --- Arrange ---
    # 1. The fixture sets up the creator, requester, group, and the pending join request.
    scenario = join_request_scenario
    
    # 2. Authenticate as the group creator who will approve the request.
    client = api_client_factory(user=scenario['creator'])
    url = f"/api/groups/{scenario['group'].slug}/requests/{scenario['request'].id}/"
    payload = {"action": "approve"}
    
    # 3. Pre-condition: We clear any notifications created by the initial request
    #    to ensure we are only testing the notification created by the approval action.
    Notification.objects.all().delete()
    assert Notification.objects.count() == 0

    # --- Act ---
    # 4. Simulate the owner's action by making the API call to approve the request.
    response = client.patch(url, data=payload)

    # --- Assert ---
    # 5. Check that the API call was successful.
    assert response.status_code == status.HTTP_200_OK
    
    # 6. CRITICAL: Verify that a new notification was created.
    assert Notification.objects.count() == 1
    
    notification = Notification.objects.first()
    
    # 7. Verify the notification was sent to the correct person with the correct details.
    assert notification.recipient == scenario['requester']
    assert notification.actor == scenario['creator']
    assert notification.notification_type == Notification.GROUP_JOIN_APPROVED
    assert notification.target == scenario['group']

def test_user_registration_success(api_client):
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