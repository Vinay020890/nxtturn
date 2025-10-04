# C:\Users\Vinay\Project\Loopline\community\management\commands\clear_seeded_data.py
# FINAL, UNSTOPPABLE VERSION

from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from community.models import (
    StatusPost, PostMedia, Follow, Like, Comment, Notification, Poll, Group,
    PollVote, Report, GroupJoinRequest, GroupBlock, UserProfile
)

User = get_user_model()

class Command(BaseCommand):
    help = 'FINAL SCRIPT: Deletes all seeded data in sequential, committed steps.'

    # REMOVED the @transaction.atomic decorator. We will manage transactions manually.
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('--- STARTING UNSTOPPABLE CLEANUP ---'))

        # 1. Identify all users to delete.
        users_to_delete = User.objects.filter(email__endswith='@example.com')
        if not users_to_delete.exists():
            self.stdout.write(self.style.SUCCESS('No seeded users found. Database is clean.'))
            return

        user_ids = list(users_to_delete.values_list('id', flat=True))
        self.stdout.write(f'Found {len(user_ids)} seeded users to clean up.')
        
        posts_to_delete = StatusPost.objects.filter(author__in=users_to_delete)

        # --- DELETION IN SEQUENTIAL, COMMITTED STEPS ---

        # STEP 1: Delete the lowest-level children (media)
        with transaction.atomic():
            self.stdout.write('Step 1: Deleting Post Media...')
            count, _ = PostMedia.objects.filter(post__in=posts_to_delete).delete()
            self.stdout.write(self.style.SUCCESS(f'  > Deleted {count} media objects.'))
        # This transaction is now COMMITTED. The media is gone from the database.

        # STEP 2: Delete everything else that depends on Users or Posts
        with transaction.atomic():
            self.stdout.write('Step 2: Deleting all other related content (Likes, Comments, Posts, etc.)...')
            Like.objects.filter(user__in=user_ids).delete()
            PollVote.objects.filter(user__in=user_ids).delete()
            Report.objects.filter(reporter__in=user_ids).delete()
            Notification.objects.filter(recipient__in=user_ids).delete()
            Notification.objects.filter(actor__in=user_ids).delete()
            Comment.objects.filter(author__in=user_ids).delete()
            Poll.objects.filter(post__in=posts_to_delete).delete()
            Follow.objects.filter(follower__in=user_ids).delete()
            Follow.objects.filter(following__in=user_ids).delete()
            GroupJoinRequest.objects.filter(user__in=user_ids).delete()
            GroupBlock.objects.filter(user__in=user_ids).delete()
            
            # Now delete the posts themselves, which is now safe.
            post_count, _ = posts_to_delete.delete()
            self.stdout.write(self.style.SUCCESS(f'  > Deleted {post_count} post objects.'))
        # This transaction is now COMMITTED.

        # STEP 3: Clean up final user-related objects
        with transaction.atomic():
            self.stdout.write('Step 3: Cleaning up profiles and group memberships...')
            for group in Group.objects.filter(members__in=user_ids).distinct():
                group.members.remove(*users_to_delete)
            UserProfile.objects.filter(user__in=user_ids).delete()
        # This transaction is now COMMITTED.

        # FINAL STEP: Delete the users themselves
        with transaction.atomic():
            self.stdout.write('Step 4: Deleting the user accounts...')
            user_count, _ = users_to_delete.delete()
            self.stdout.write(self.style.SUCCESS(f'  > Deleted {user_count} user accounts.'))
        # This transaction is now COMMITTED.

        self.stdout.write(self.style.SUCCESS('\n--- UNSTOPPABLE CLEANUP COMPLETE ---'))