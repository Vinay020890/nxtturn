# The definitive settings.py for the NxtTurn project
# Version: Cleaned for local/generic production

import dj_database_url
from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / '.env')

# --- THE DEFINITIVE PRODUCTION SWITCH ---
# Determines if the application is running in a production environment
# based on the presence of a DATABASE_URL environment variable.
IS_PRODUCTION = 'DATABASE_URL' in os.environ

# --- SECURITY SETTINGS ---
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = not IS_PRODUCTION
if not IS_PRODUCTION and not SECRET_KEY:
    SECRET_KEY = 'a-dummy-secret-key-for-local-development-only-do-not-use-in-prod'

# --- HOSTS CONFIGURATION ---
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
if IS_PRODUCTION:
    # ...
    pass
else:
    # When running the server with 0.0.0.0, we need to allow all hosts for local network access.
    # This is safe for local development but should NOT be used in production.
    ALLOWED_HOSTS.append('*')

# --- APPLICATION DEFINITION ---
INSTALLED_APPS = [
    'channels',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'rest_framework',
    'rest_framework.authtoken',
    'dj_rest_auth',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'dj_rest_auth.registration',
    'corsheaders',
    'django_extensions',
    'community.apps.CommunityConfig',
    
]

# --- ADD THIS BLOCK RIGHT HERE ---
# Conditionally add our custom testing app ONLY when in development (DEBUG=True).
# This ensures no testing code ever makes it into a production environment.
if DEBUG:
    INSTALLED_APPS.append('e2e_test_utils')
# --- END OF BLOCK --

SITE_ID = 1
# ACCOUNT_EMAIL_VERIFICATION = 'none'

# --- MIDDLEWARE ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise is for serving static files in production. Keep if you plan to use it for self-hosting.
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages'
            ]
        }
    }
]

# --- DATABASE CONFIGURATION ---
if IS_PRODUCTION:
    # Uses DATABASE_URL environment variable for production.
    # Keep dj_database_url as it's a standard way to parse PostgreSQL URLs.
    DATABASES = {'default': dj_database_url.config(conn_max_age=600, ssl_require=True)}
else:
    # Local PostgreSQL database configuration from .env file
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST'),
            'PORT': os.getenv('DB_PORT')
        }
    }

# --- PASSWORD VALIDATION ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}
]
LANGUAGE_CODE, TIME_ZONE, USE_I18N, USE_TZ = 'en-us', 'UTC', True, True

# --- STATIC & MEDIA FILES (STANDARD LOCAL HANDLING) ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (user-uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'

# Storage settings
STORAGES = {
    # Default storage engine for media files (e.g., ImageField, FileField)
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    # Storage engine for static files (CSS, JS)
    "staticfiles": {
        # Using FileSystemStorage for static files in both dev and production
        # if no specialized cloud storage (like S3 or Cloudinary) is configured.
        # If deploying to a host that requires WhiteNoise, ensure it's in requirements.txt.
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# --- OTHER SETTINGS ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# REST Framework Settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    # Keep default pagination as PageNumberPagination for now,
    # and explicitly set CursorPagination in relevant views.
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    # Cursor pagination specific settings can be added here if needed,
    # but often managed directly on the CursorPagination class or subclass.
    'DEFAULT_FILTER_BACKENDS': ['rest_framework.filters.SearchFilter'],
}

# --- AUTHENTICATION & REGISTRATION SETTINGS (dj-rest-auth & allauth) ---


# It tells Django to use allauth's authentication system.
AUTHENTICATION_BACKENDS = (
    'allauth.account.auth_backends.AuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# django-allauth settings
# This is the modern way to specify requirements for accounts.
ACCOUNT_AUTHENTICATION_METHOD = 'username_email' # Allow login with username or email
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none' # Keep this for development ease

# dj-rest-auth settings
# This configures dj-rest-auth itself and how it handles registration.
REST_AUTH = {
    'USE_SESSION_AUTH': False, # We use Token Authentication, not sessions
    'SESSION_LOGIN': False,
    'USER_DETAILS_SERIALIZER': 'community.serializers.UserSerializer',
    'REGISTER_SERIALIZER': 'community.serializers.CustomRegisterSerializer',
    
    # This setting, combined with the ACCOUNT_* settings above, resolves all warnings.
    'SIGNUP_FIELDS': {
        'username': {'required': True},
        'email': {'required': True},
    }
}

# --- CORS SETTINGS ---
CORS_ALLOWED_ORIGINS = [] # Default to empty for production unless explicitly defined below

if IS_PRODUCTION:
    # For production, define your exact frontend origins.
    # Example: CORS_ALLOWED_ORIGINS.append("https://your-production-frontend.com")
    # For now, it's an empty list if not explicitly populated by an ENV variable.
    CORS_ALLOWED_ORIGINS.extend(
        [origin.strip() for origin in os.getenv('CORS_PROD_WHITELIST', '').split(',') if origin.strip()]
    )
    # Note: CORS_TRUSTED_ORIGINS is generally not needed unless using Django's CSRF across origins,
    # which is typically not the case for DRF Token/Session authentication.
else:
    # Local development origins
    CORS_ALLOWED_ORIGINS = [
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://192.168.1.11:5173' # Your local network IP
    ]

# This tells Django that it's safe to accept POST requests from your frontend's network IP
CSRF_TRUSTED_ORIGINS = [
    'http://192.168.1.11:5173',
]

# If you remove Whitenoise:
# You might need to add 'django.contrib.staticfiles.finders.FileSystemFinder'
# and 'django.contrib.staticfiles.finders.AppDirectoriesFinder' to STATICFILES_FINDERS
# if you had custom static file serving setup previously.

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            # This now reads the full Redis URL from your .env file
            # It defaults to the local URL if the .env variable is missing
            "hosts": [os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')],
        },
    },
}