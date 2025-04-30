# community/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
# Import the UserProfile model from models.py in the same directory
from .models import UserProfile

# Get the currently active User model (best practice)
User = settings.AUTH_USER_MODEL

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Uses get_or_create to ensure a UserProfile exists for every User.
    Creates one if it's missing (handles new users and existing users saved later).
    """
    UserProfile.objects.get_or_create(user=instance)
    # We don't need to do anything with the profile object returned here,
    # just ensuring it exists is enough for this signal.
    # print(f"Ensured profile exists for user: {instance.username}") # Optional debug print