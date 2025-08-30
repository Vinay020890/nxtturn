import pytest
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
import asyncio


# --- UPDATED IMPORTS: Added Notification ---
from community.models import StatusPost, Follow, Like, Comment, Group, GroupJoinRequest, Notification
from config.asgi import application

pytestmark = pytest.mark.django_db(transaction=True)

# --- Async Helper Functions ---

@database_sync_to_async
def create_user(username, password='password123'):
    User = get_user_model()
    return User.objects.create_user(username=username, password=password)

@database_sync_to_async
def create_follow(follower, following):
    return Follow.objects.create(follower=follower, following=following)

@database_sync_to_async
def create_post(author, content):
    return StatusPost.objects.create(author=author, content=content)

@database_sync_to_async
def get_auth_token(user):
    token, _ = Token.objects.get_or_create(user=user)
    return token.key

@database_sync_to_async
def create_like(user, content_object):
    return Like.objects.create(user=user, content_object=content_object)

@database_sync_to_async
def create_comment(author, content_object, content, parent=None):
    return Comment.objects.create(
        author=author,
        content_object=content_object,
        content=content,
        parent=parent
    )

# --- NEW HELPER FUNCTION: To create a Group asynchronously ---
@database_sync_to_async
def create_group(creator, name, privacy_level='public'):
    return Group.objects.create(creator=creator, name=name, privacy_level=privacy_level)

# ===============================================================
# POSITIVE PATH REAL-TIME TESTS
# ===============================================================

@pytest.mark.asyncio
async def test_new_post_sends_live_signal_to_follower():
    """
    Verifies that creating a post sends a real-time signal with the
    post's ID to an online follower.
    """
    author = await create_user('live_author')
    follower = await create_user('live_follower')
    await create_follow(follower=follower, following=author)

    follower_token = await get_auth_token(follower)
    connection_url = f"/ws/activity/?token={follower_token}"
    
    communicator = WebsocketCommunicator(application, connection_url)
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection failed."

    post = await create_post(author=author, content="A live post!")

    response_wrapper = await communicator.receive_json_from(timeout=1)
    
    assert response_wrapper['type'] == 'live_post'
    
    response = response_wrapper['message']
    assert response['type'] == 'new_post'
    assert response['payload']['id'] == post.id

    await communicator.disconnect()

@pytest.mark.asyncio
async def test_like_on_post_sends_realtime_notification():
    """
    Verifies that liking a post sends a full notification object in real-time
    to the post's author.
    """
    author = await create_user('notification_recipient')
    liker = await create_user('notification_actor')
    post = await create_post(author=author, content="A post to be liked.")

    author_token = await get_auth_token(author)
    communicator = WebsocketCommunicator(application, f"/ws/activity/?token={author_token}")
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection for author failed."

    await create_like(user=liker, content_object=post)

    response_wrapper = await communicator.receive_json_from(timeout=1)

    assert response_wrapper['type'] == 'notification'
    
    message = response_wrapper['message']
    assert message['type'] == 'new_notification'
    
    payload = message['payload']
    assert payload['verb'] == 'liked your post'
    assert payload['actor']['username'] == liker.username

    await communicator.disconnect()

@pytest.mark.asyncio
async def test_comment_on_post_sends_realtime_notification():
    """
    Verifies that commenting on a post sends a real-time notification
    to the post's author.
    """
    author = await create_user('post_author_rt')
    commenter = await create_user('commenter_rt')
    post = await create_post(author=author, content="A post to be commented on.")

    author_token = await get_auth_token(author)
    communicator = WebsocketCommunicator(application, f"/ws/activity/?token={author_token}")
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection for author failed."

    await create_comment(author=commenter, content_object=post, content="A real-time comment!")

    response_wrapper = await communicator.receive_json_from(timeout=1)
    
    assert response_wrapper['type'] == 'notification'
    message = response_wrapper['message']
    assert message['type'] == 'new_notification'
    payload = message['payload']
    
    assert payload['verb'] == 'commented on your post'
    assert payload['actor']['username'] == commenter.username
    assert payload['context_snippet'] == '"A real-time comment!"'

    await communicator.disconnect()

@pytest.mark.asyncio
async def test_mention_in_post_sends_realtime_notification():
    """
    Verifies that mentioning a user in a post sends a real-time notification
    to the mentioned user.
    """
    author = await create_user('mentioner_rt')
    mentioned_user = await create_user('mentioned_rt')

    mentioned_user_token = await get_auth_token(mentioned_user)
    communicator = WebsocketCommunicator(application, f"/ws/activity/?token={mentioned_user_token}")
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection for mentioned user failed."

    await create_post(
        author=author,
        content=f"This is a real-time mention for @{mentioned_user.username}!"
    )

    response_wrapper = await communicator.receive_json_from(timeout=1)
    
    assert response_wrapper['type'] == 'notification'
    message = response_wrapper['message']
    assert message['type'] == 'new_notification'
    payload = message['payload']
    
    assert payload['verb'] == 'mentioned you in a post'
    assert payload['actor']['username'] == author.username
    assert f"@{mentioned_user.username}" in payload['context_snippet']

    await communicator.disconnect()

@pytest.mark.asyncio
async def test_follow_sends_realtime_notification():
    """
    Verifies that following a user sends a real-time notification
    to the user who was followed.
    """
    followed_user = await create_user('followed_rt')
    follower = await create_user('follower_rt')

    followed_user_token = await get_auth_token(followed_user)
    communicator = WebsocketCommunicator(application, f"/ws/activity/?token={followed_user_token}")
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection for followed user failed."

    await create_follow(follower=follower, following=followed_user)

    response_wrapper = await communicator.receive_json_from(timeout=1)
    
    assert response_wrapper['type'] == 'notification'
    message = response_wrapper['message']
    assert message['type'] == 'new_notification'
    payload = message['payload']
    
    assert payload['verb'] == 'started following you'
    assert payload['actor']['username'] == follower.username

    await communicator.disconnect()

@pytest.mark.asyncio
async def test_like_on_comment_sends_realtime_notification():
    """
    Verifies that liking a comment sends a real-time notification
    to the comment's author.
    """
    comment_author = await create_user('comment_author_rt')
    liker = await create_user('liker_rt')
    post_author = await create_user('post_author_for_comment_like_rt')
    post = await create_post(author=post_author, content="A post.")
    comment = await create_comment(
        author=comment_author, 
        content_object=post, 
        content="A comment to be liked in real-time."
    )

    comment_author_token = await get_auth_token(comment_author)
    communicator = WebsocketCommunicator(application, f"/ws/activity/?token={comment_author_token}")
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection failed."

    await create_like(user=liker, content_object=comment)

    response_wrapper = await communicator.receive_json_from(timeout=1)
    
    assert response_wrapper['type'] == 'notification'
    message = response_wrapper['message']
    payload = message['payload']
    
    assert payload['verb'] == 'liked your comment'
    assert payload['actor']['username'] == liker.username

    await communicator.disconnect()

@pytest.mark.asyncio
async def test_reply_to_comment_sends_realtime_notification():
    """
    Verifies that replying to a comment sends a real-time notification
    to the parent comment's author.
    """
    comment_author = await create_user('parent_comment_author_rt')
    replier = await create_user('replier_rt')
    post_author = await create_user('post_author_for_reply_rt')
    post = await create_post(author=post_author, content="A post.")
    parent_comment = await create_comment(
        author=comment_author, 
        content_object=post, 
        content="The parent comment for the real-time reply."
    )

    comment_author_token = await get_auth_token(comment_author)
    communicator = WebsocketCommunicator(application, f"/ws/activity/?token={comment_author_token}")
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection failed."

    await create_comment(
        author=replier, 
        content_object=post, 
        content="This is a real-time reply.",
        parent=parent_comment
    )

    response_wrapper = await communicator.receive_json_from(timeout=1)
    
    assert response_wrapper['type'] == 'notification'
    message = response_wrapper['message']
    payload = message['payload']
    
    assert payload['verb'] == 'replied to your comment'
    assert payload['actor']['username'] == replier.username

    await communicator.disconnect()

@pytest.mark.asyncio
async def test_mention_in_comment_sends_realtime_notification():
    """
    Verifies that mentioning a user in a comment sends a real-time
    notification to the mentioned user.
    """
    comment_author = await create_user('comment_mentioner_rt')
    mentioned_user = await create_user('mentioned_in_comment_rt')
    post_author = await create_user('post_author_for_mention_rt')
    post = await create_post(author=post_author, content="A post.")

    mentioned_user_token = await get_auth_token(mentioned_user)
    communicator = WebsocketCommunicator(application, f"/ws/activity/?token={mentioned_user_token}")
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection failed."

    await create_comment(
        author=comment_author,
        content_object=post,
        content=f"This is a real-time mention in a comment for @{mentioned_user.username}!"
    )

    response_wrapper = await communicator.receive_json_from(timeout=1)
    
    assert response_wrapper['type'] == 'notification'
    message = response_wrapper['message']
    payload = message['payload']
    
    assert 'mentioned you in a comment' in payload['verb']
    assert payload['actor']['username'] == comment_author.username

    await communicator.disconnect()

@pytest.mark.asyncio
async def test_realtime_notification_on_group_join_request(user_factory, channel_layer):
    """
    Tests that a real-time notification is sent to the group owner
    when a user requests to join their private group.
    """
    group_owner = await database_sync_to_async(user_factory)(username_prefix='owner')
    requester = await database_sync_to_async(user_factory)(username_prefix='requester')
    
    private_group = await create_group(
        creator=group_owner, 
        name="Realtime Group Test", 
        privacy_level='private'
    )

    await database_sync_to_async(Notification.objects.all().delete)()
    assert await database_sync_to_async(Notification.objects.count)() == 0

    owner_token = await get_auth_token(group_owner)
    connection_url = f"/ws/activity/?token={owner_token}"
    
    communicator = WebsocketCommunicator(application, connection_url)
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection for group owner failed."

    join_request = await database_sync_to_async(GroupJoinRequest.objects.create)(
        user=requester, 
        group=private_group
    )

    assert await database_sync_to_async(Notification.objects.count)() == 1
    db_notification = await database_sync_to_async(Notification.objects.first)()
    assert (await database_sync_to_async(lambda: db_notification.recipient_id)()) == group_owner.id
    assert db_notification.notification_type == Notification.GROUP_JOIN_REQUEST

    received_message = await communicator.receive_json_from(timeout=1)

    assert received_message['type'] == 'notification'
    assert received_message['message']['type'] == 'new_notification'
    
    payload = received_message['message']['payload']
    assert payload['actor']['username'] == requester.username
    assert payload['verb'] == "sent a request to join"
    assert payload['notification_type'] == 'group_join_request'
    assert payload['target']['display_text'] == private_group.name
    assert payload['target']['slug'] == private_group.slug # Assert slug is included
    assert payload['action_object']['id'] == join_request.id

    await communicator.disconnect()


# ===============================================================
# NEGATIVE PATH REAL-TIME TESTS
# ===============================================================

@pytest.mark.asyncio
async def test_like_on_own_post_does_not_send_realtime_notification():
    """
    Verifies that liking your own post does NOT send a real-time notification.
    """
    user = await create_user('self_liker_rt')
    post = await create_post(author=user, content="A post to be self-liked.")
    user_token = await get_auth_token(user)
    communicator = WebsocketCommunicator(application, f"/ws/activity/?token={user_token}")
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection failed."

    await create_like(user=user, content_object=post)
    await communicator.receive_nothing()

    await communicator.disconnect()

@pytest.mark.asyncio
async def test_reply_to_own_comment_does_not_send_realtime_notification():
    """
    Verifies that replying to your own comment does NOT send a real-time notification.
    """
    user = await create_user('self_replier_rt')
    post = await create_post(author=user, content="A post for self-reply testing.")
    parent_comment = await create_comment(author=user, content_object=post, content="My parent comment.")
    user_token = await get_auth_token(user)
    communicator = WebsocketCommunicator(application, f"/ws/activity/?token={user_token}")
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection failed."

    await create_comment(author=user, content_object=post, content="My self-reply.", parent=parent_comment)
    await communicator.receive_nothing()

    await communicator.disconnect()

@pytest.mark.asyncio
async def test_self_mention_in_post_does_not_send_realtime_notification():
    """
    Verifies that mentioning yourself in a post does NOT send a real-time notification.
    """
    user = await create_user('self_mentioner_rt')
    user_token = await get_auth_token(user)
    communicator = WebsocketCommunicator(application, f"/ws/activity/?token={user_token}")
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection failed."

    await create_post(author=user, content=f"A note for @{user.username}")
    await communicator.receive_nothing()

    await communicator.disconnect()

@pytest.mark.asyncio
async def test_realtime_notification_on_group_join_approval():
    """
    Tests that a real-time notification is sent to the requester when their
    join request is approved by the group owner.
    """
    # --- Arrange ---
    # 1. Create all the necessary users and objects.
    group_owner = await create_user(username='approver_rt')
    requester = await create_user(username='requester_rt')
    
    private_group = await create_group(
        creator=group_owner, 
        name="Realtime Approval Group", 
        privacy_level='private'
    )
    
    # 2. Create the initial join request. We don't test the notification for this part.
    join_request = await database_sync_to_async(GroupJoinRequest.objects.create)(
        user=requester, 
        group=private_group
    )

    # 3. Simulate the REQUESTER'S browser connecting to the WebSocket to listen for the approval.
    requester_token = await get_auth_token(requester)
    connection_url = f"/ws/activity/?token={requester_token}"
    
    communicator = WebsocketCommunicator(application, connection_url)
    connected, _ = await communicator.connect()
    assert connected, "WebSocket connection for requester failed."

    # --- Act ---
    # 4. Simulate the group owner approving the request. This is the logic from the view.
    #    First, the user is added to the group's members.
    await database_sync_to_async(private_group.members.add)(requester)
    
    #    Then, the request status is updated.
    join_request.status = 'approved'
    await database_sync_to_async(join_request.save)()
    
    #    Finally, the view creates the notification. The post_save signal on THIS object
    #    is what triggers the real-time push to the requester.
    await database_sync_to_async(Notification.objects.create)(
        recipient=requester,
        actor=group_owner,
        verb=f"approved your request to join the group",
        notification_type=Notification.GROUP_JOIN_APPROVED,
        target=private_group
    )

    # --- Assert ---
    # 5. "Listen" for the incoming WebSocket message on the requester's connection.
    received_message = await communicator.receive_json_from(timeout=1)
    
    # 6. Verify the payload of the live notification.
    assert received_message['type'] == 'notification'
    assert received_message['message']['type'] == 'new_notification'
    
    payload = received_message['message']['payload']
    assert payload['actor']['username'] == group_owner.username
    assert payload['notification_type'] == 'group_join_approved'
    assert payload['target']['display_text'] == private_group.name

    # 7. Clean up the connection.
    await communicator.disconnect()