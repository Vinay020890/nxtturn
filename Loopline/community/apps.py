from django.apps import AppConfig

# This class was already here
class CommunityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'community'

    # Add this method VVV
    def ready(self):
        # Import signals here so they are registered when Django starts
        try:
            import community.models # Or specifically import community.signals if you move the code later
        except ImportError:
            pass
    # Add this method ^^^

    
