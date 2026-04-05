# C:\Users\Vinay\Project\Loopline\config\settings.py

import dj_database_url
from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

IS_PRODUCTION = "DATABASE_URL" in os.environ
SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = not IS_PRODUCTION
if not IS_PRODUCTION and not SECRET_KEY:
    SECRET_KEY = "a-dummy-secret-key-for-local-development-only-do-not-use-in-prod"

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "192.168.10.33", "192.168.10.33.nip.io"]
if IS_PRODUCTION:
    pass
else:
    ALLOWED_HOSTS.extend(["*", "192.168.10.33", "192.168.10.33.nip.io"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://192.168.10.33.nip.io:5173")

# --- ADD THIS BLOCK IMMEDIATELY BELOW IT ---
if os.getenv("CYPRESS_TESTING", "false").lower() == "true":
    # Force raw IP during tests so it matches the Cypress browser origin
    FRONTEND_URL = "http://192.168.10.33:5173"
# --------------------------------------------

# This tells dj-rest-auth where to send the user for password resets
# It will build a link like: http://192.168.10.33:5173/auth/reset-password/UID/TOKEN

# PASSWORD_RESET_CONFIRM_URL = f"{FRONTEND_URL}/auth/reset-password/{{uid}}/{{token}}/"

INSTALLED_APPS = [
    "channels",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "anymail",
    "rest_framework",
    "rest_framework.authtoken",
    "dj_rest_auth",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "dj_rest_auth.registration",
    "corsheaders",
    "django_extensions",
    "community.apps.CommunityConfig",
    "allauth.socialaccount.providers.google",
]

if DEBUG:
    INSTALLED_APPS.append("e2e_test_utils")

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

if IS_PRODUCTION:
    DATABASES = {"default": dj_database_url.config(conn_max_age=600, ssl_require=True)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME"),
            "USER": os.getenv("DB_USER"),
            "PASSWORD": os.getenv("DB_PASSWORD"),
            "HOST": os.getenv("DB_HOST"),
            "PORT": os.getenv("DB_PORT"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE, TIME_ZONE, USE_I18N, USE_TZ = "en-us", "UTC", True, True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
# Email Configuration (Brevo)
# ==============================================================================
# --- SMART EMAIL CONFIGURATION (Final Version for Tests) ---
EMAIL_MODE = os.getenv("EMAIL_MODE", "console")
DEFAULT_FROM_EMAIL = "nxtturn <noreply@nxtturn.com>"
SERVER_EMAIL = "admin@nxtturn.com"

# 1. Check if we are running Cypress tests (This overrides everything else)
# This handles missing variables and mixed casing (True/true) perfectly
if os.getenv("CYPRESS_TESTING", "false").lower() == "true":
    EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    # This makes the link match the Cypress browser window:


# 2. Otherwise, check our normal dev/prod mode
elif EMAIL_MODE == "brevo":
    EMAIL_BACKEND = "anymail.backends.brevo.EmailBackend"
    ANYMAIL = {
        "BREVO_API_KEY": os.getenv("BREVO_API_KEY"),
    }
else:
    # Default local console mode
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# This allows users to confirm email just by clicking the link in the email
ACCOUNT_CONFIRM_EMAIL_ON_GET = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_FILTER_BACKENDS": ["rest_framework.filters.SearchFilter"],
}

AUTHENTICATION_BACKENDS = (
    "allauth.account.auth_backends.AuthenticationBackend",
    "django.contrib.auth.backends.ModelBackend",
)

ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"

ACCOUNT_ADAPTER = "community.adapters.NxtTurnAccountAdapter"
SOCIALACCOUNT_ADAPTER = "community.adapters.NxtTurnSocialAccountAdapter"

REST_AUTH = {
    "USE_SESSION_AUTH": False,
    "SESSION_LOGIN": False,
    "USER_DETAILS_SERIALIZER": "community.serializers.UserSerializer",
    "REGISTER_SERIALIZER": "community.serializers.CustomRegisterSerializer",
    "LOGIN_SERIALIZER": "community.serializers.CustomLoginSerializer",
    "PASSWORD_RESET_CONFIRM_SERIALIZER": "community.serializers.CustomPasswordResetConfirmSerializer",
    "PASSWORD_RESET_CONFIRM_URL": f"{FRONTEND_URL}/auth/reset-password/{{uid}}/{{token}}/",
    "SIGNUP_FIELDS": {
        "username": {"required": True},
        "email": {"required": True},
    },
}

# CORS (Cross-Origin Resource Sharing) SETTINGS
# ==============================================================================
# This section defines which frontend URLs are allowed to make requests to our API.

# In a production environment, you would use environment variables to populate this.
# For local development, we explicitly list the allowed origins for simplicity and reliability.
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # For local-only frontend development
    "http://127.0.0.1:5173",  # Alternative for local-only
    "http://192.168.10.33:5173",  # For accessing the frontend from other devices on the network
    "http://192.168.10.33.nip.io:5173",
]

# ==============================================================================
# CSRF (Cross-Site Request Forgery) SETTINGS
# ==============================================================================
# This tells Django which origins are trusted for POST/PUT/DELETE requests.
# It's good practice to keep this in sync with the CORS settings.

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.10.33:5173",
    "http://192.168.10.33.nip.io:5173",
]

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")],
        },
    },
}

# --- GOOGLE SOCIAL AUTHENTICATION ---
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APPS": [
            {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "key": "",  # Leave as empty string
            },
        ],
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
        # Industry Standard: Add leeway specifically for the Google Provider
        "JWT_LEEWAY": 300,
    }
}

# This tells Allauth to automatically create the account if the email is new
SOCIALACCOUNT_AUTO_SIGNUP = True

# --- IDENTITY CONFLICT MANAGEMENT ---
# 1. Allow logging in with Google if the email matches an existing manual account
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True

# 2. Automatically link the Google account to the existing manual account
SOCIALACCOUNT_QUERY_EMAIL = True

# 3. Trust Google's verification status (prevents double-verification loops)
SOCIALACCOUNT_EMAIL_VERIFICATION = "optional"


# Allow 5 minutes of clock drift globally for all social accounts
SOCIALACCOUNT_JWT_LEEWAY = 300
