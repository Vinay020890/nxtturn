# C:\Users\Vinay\Project\Loopline\community\management\commands\clear_seeded_data.py (Corrected Version)

from django.core.management.base import BaseCommand
from django.db import transaction, connection  # Added connection
from django.contrib.auth import get_user_model
from community.models import (
    StatusPost,
    PostMedia,
    Follow,
    Like,
    Comment,
    Notification,
    Poll,
    Group,
    PollVote,
    Report,
    GroupJoinRequest,
    GroupBlock,
    UserProfile,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Deletes all seeded data (users ending in @example.com) and their content."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("--- STARTING SEEDED DATA CLEANUP ---"))

        # 1. Identify all seeded users.
        users_to_delete = User.objects.filter(email__endswith="@example.com")
        if not users_to_delete.exists():
            self.stdout.write(
                self.style.SUCCESS("No seeded users found. Database is clean.")
            )
            return

        user_ids = list(users_to_delete.values_list("id", flat=True))
        self.stdout.write(f"Found {len(user_ids)} seeded users to clean up.")

        posts_to_delete = StatusPost.objects.filter(author__in=users_to_delete)
        groups_to_delete = Group.objects.filter(creator__in=users_to_delete)

        with transaction.atomic():
            self.stdout.write("Deleting all related content...")

            # 1. Safely clear the token blacklist table if it exists
            with connection.cursor() as cursor:
                # Get a list of all tables in the public schema
                cursor.execute(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                )
                all_tables = [table[0] for table in cursor.fetchall()]

                if "token_blacklist_outstandingtoken" in all_tables:
                    self.stdout.write(
                        self.style.NOTICE(
                            "  > Found token_blacklist table. Clearing it..."
                        )
                    )
                    cursor.execute(
                        "TRUNCATE TABLE token_blacklist_outstandingtoken CASCADE;"
                    )
                    self.stdout.write(
                        self.style.SUCCESS("  > Token blacklist cleared.")
                    )
                else:
                    self.stdout.write(
                        self.style.NOTICE(
                            "  > Token blacklist table not found. Skipping cleanup."
                        )
                    )

            # 2. Delete all other objects that depend on Posts or Users
            PostMedia.objects.filter(post__in=posts_to_delete).delete()
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

            # 3. Remove seeded users from any groups they might be members of
            for group in Group.objects.filter(members__in=user_ids).distinct():
                group.members.remove(*users_to_delete)

            # 4. Now delete the top-level objects
            posts_to_delete.delete()
            group_count, _ = groups_to_delete.delete()
            self.stdout.write(self.style.SUCCESS(f"  > Deleted {group_count} groups."))

            UserProfile.objects.filter(user__in=user_ids).delete()

            # 5. Finally, delete the users themselves
            user_count, _ = users_to_delete.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Deleted {user_count} user accounts and all their associated data."
                )
            )

        self.stdout.write(self.style.SUCCESS("--- SEEDED DATA CLEANUP COMPLETE ---"))
