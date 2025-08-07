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
    # In a generic production environment, ALLOWED_HOSTS should list your production domain(s).
    # If not defined via an environment variable, it might default to an empty list or be explicitly added here.
    # Example: ALLOWED_HOSTS.append(os.getenv('PROD_DOMAIN', 'your-production-domain.com'))
    pass # Keep this empty for now, assuming external domain isn't directly configured via ENV in this setup
else:
    # This setting allows others on your local network to access the app
    ALLOWED_HOSTS.append('192.168.31.35')

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
SITE_ID = 1
ACCOUNT_EMAIL_VERIFICATION = 'none'

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

REST_AUTH = {
    'USER_DETAILS_SERIALIZER': 'community.serializers.UserSerializer',
    'REGISTER_SERIALIZER': 'community.serializers.CustomRegisterSerializer',
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
        'http://192.168.31.35:5173' # Your local network IP
    ]

# If you remove Whitenoise:
# You might need to add 'django.contrib.staticfiles.finders.FileSystemFinder'
# and 'django.contrib.staticfiles.finders.AppDirectoriesFinder' to STATICFILES_FINDERS
# if you had custom static file serving setup previously.

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}