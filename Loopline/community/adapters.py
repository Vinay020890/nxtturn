from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings  # This imports your settings


class NxtTurnAccountAdapter(DefaultAccountAdapter):
    def get_email_confirmation_url(self, request, emailconfirmation):
        """
        This now automatically builds the URL based on FRONTEND_URL from your .env
        """
        # It combines your FRONTEND_URL and the secret verification key
        return f"{settings.FRONTEND_URL}/verify-email/{emailconfirmation.key}"
