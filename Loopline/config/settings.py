# The definitive settings.py for the NxtTurn project

import dj_database_url
from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / '.env')

# --- THE DEFINITIVE PRODUCTION SWITCH ---
IS_PRODUCTION = 'DATABASE_URL' in os.environ

# --- SECURITY SETTINGS ---
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = not IS_PRODUCTION
if not IS_PRODUCTION and not SECRET_KEY:
    SECRET_KEY = 'a-dummy-secret-key-for-local-development-only-do-not-use-in-prod'

# --- HOSTS CONFIGURATION ---
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
if IS_PRODUCTION:
    render_hostname = os.getenv('RENDER_HOSTNAME')
    if render_hostname:
        ALLOWED_HOSTS.append(render_hostname)
else:
    ALLOWED_HOSTS.append('192.168.31.35') # Your local IP for mobile testing

# --- APPLICATION DEFINITION ---
INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'django.contrib.sites', 'rest_framework', 'rest_framework.authtoken',
    'dj_rest_auth', 'allauth', 'allauth.account', 'allauth.socialaccount',
    'dj_rest_auth.registration', 'corsheaders', 'django_extensions',
    'cloudinary_storage', 'cloudinary', 'community.apps.CommunityConfig',
]
SITE_ID = 1
ACCOUNT_EMAIL_VERIFICATION = 'none'

# --- MIDDLEWARE ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', 'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [], 'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.request', 'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages']}}]

# --- DATABASE CONFIGURATION ---
if IS_PRODUCTION:
    DATABASES = {'default': dj_database_url.config(conn_max_age=600, ssl_require=True)}
else:
    DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': os.getenv('DB_NAME'), 'USER': os.getenv('DB_USER'), 'PASSWORD': os.getenv('DB_PASSWORD'), 'HOST': os.getenv('DB_HOST'), 'PORT': os.getenv('DB_PORT')}}

# --- PASSWORD VALIDATION ---
AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'}, {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'}, {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'}, {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE, TIME_ZONE, USE_I18N, USE_TZ = 'en-us', 'UTC', True, True

# --- STATIC & MEDIA FILES (THE MODERN DJANGO 5.x WAY) ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'

# This variable gives you explicit control for local testing with Cloudinary
USE_CLOUDINARY_IN_DEVELOPMENT = os.getenv('USE_CLOUDINARY_IN_DEVELOPMENT', 'false').lower() == 'true'

# The new STORAGES setting, which replaces the deprecated DEFAULT_FILE_STORAGE
if IS_PRODUCTION or USE_CLOUDINARY_IN_DEVELOPMENT:
    STORAGES = {
        "default": {
            "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

# This dictionary is still required to provide credentials to cloudinary_storage
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY'),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET'),
}

# --- OTHER SETTINGS ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
REST_FRAMEWORK = {'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.TokenAuthentication'], 'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticatedOrReadOnly'], 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination', 'PAGE_SIZE': 10}
REST_AUTH = {'USER_DETAILS_SERIALIZER': 'community.serializers.UserSerializer', 'REGISTER_SERIALIZER': 'community.serializers.CustomRegisterSerializer'}

# --- CORS SETTINGS (PRODUCTION-SAFE) ---
if IS_PRODUCTION:
    # This safely handles the environment variable from Render
    allowed_origins = os.getenv('NETLIFY_APP_URL', '').split(',')
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in allowed_origins if origin]
    CORS_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
else:
    CORS_ALLOWED_ORIGINS = ['http://localhost:5173', 'http://127.0.0.1:5173', 'http://192.168.31.35:5173']