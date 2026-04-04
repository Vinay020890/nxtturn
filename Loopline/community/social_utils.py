# community/social_utils.py
from allauth.socialaccount.providers.oauth2.client import OAuth2Client


class FixedOAuth2Client(OAuth2Client):
    """
    Compatibility Bridge: Ensures 'scope_delimiter' is not passed twice,
    which is a known bug in dj-rest-auth + allauth 5.x.
    """

    def __init__(self, *args, **kwargs):
        kwargs.pop("scope_delimiter", None)
        if len(args) > 6:
            args = list(args)
            args.pop(6)
        super().__init__(*args, **kwargs)
