from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress


class NxtTurnAccountAdapter(DefaultAccountAdapter):
    def get_email_confirmation_url(self, request, emailconfirmation):
        return f"{settings.FRONTEND_URL}/verify-email/{emailconfirmation.key}"


# community/adapters.py


# community/adapters.py


class NxtTurnSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return

        email = sociallogin.user.email or sociallogin.account.extra_data.get("email")
        if email:
            User = get_user_model()
            try:
                user = User.objects.get(email__iexact=email)
                # Link the account in the DB
                sociallogin.connect(request, user)

                # FORCE the user onto every attribute to prevent 500 errors
                sociallogin.user = user
                sociallogin.account.user = user  # This satisfies the ORM
            except User.DoesNotExist:
                pass
