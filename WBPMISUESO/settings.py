"""
Django settings for WBPMISUESO project.

Web-Based Project Management Information System for University Extension Services Office

For deployment checklist, see:
https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
"""

from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# CORE SETTINGS
# ============================================================

if os.environ.get('DEPLOYED', 'False') == 'True':
    DEBUG = False
else:
    DEBUG = True

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-fallback-key-change-in-production')

ALLOWED_HOSTS = [ 'localhost', '127.0.0.1', 'uesopmis.up.railway.app', 'healthcheck.railway.app', 'uesomis.pythonanywhere.com' ]
CSRF_TRUSTED_ORIGINS = [ 'https://uesopmis.up.railway.app' ]

# ============================================================
# APPLICATION DEFINITION
# ============================================================

INSTALLED_APPS = [
    # Django Built-in Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # External Apps
    'external.home',

    # Internal Apps
    'internal.agenda',
    'internal.analytics',
    'internal.dashboard',
    'internal.experts',
    'internal.goals',
    'internal.submissions',

    # Shared Apps
    'shared.about_us',
    'shared.announcements',
    'shared.archive',
    'shared.budget',
    'shared.event_calendar',
    'shared.downloadables',
    'shared.projects',
    'shared.request',

    # System Apps (Core functionality)
    'system.exports',
    'system.logs',
    'system.users',
    'system.notifications',
    'system.settings',
    'system.scheduler',

    # Third-party Apps
    'rest_framework',
    'rest_framework_api_key',
    'rest_framework.authtoken',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'system.users.middleware.SessionSecurityMiddleware',
    'system.users.middleware.RoleBasedSessionMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication', 
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ]
}

ROOT_URLCONF = 'WBPMISUESO.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'system.notifications.context_processors.unread_notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'WBPMISUESO.wsgi.application'


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

if os.environ.get('DEPLOYED', 'False') == 'True':    
    DATABASES = {
        'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
    }
    
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': str(BASE_DIR / 'db.sqlite3'),
        }
    }

# ============================================================
# AUTHENTICATION & AUTHORIZATION
# ============================================================


AUTHENTICATION_BACKENDS = [
    'system.users.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

PASSWORD_RESET_TIMEOUT = 3600

LOGIN_URL = '/login/'
LOGOUT_REDIRECT_URL = '/login/'


# ============================================================
# INTERNATIONALIZATION
# ============================================================


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'
USE_I18N = True
USE_TZ = True


# ============================================================
# STATIC FILES (CSS, JavaScript, Images)
# ============================================================


STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# ============================================================
# MEDIA FILES (User uploads)
# ============================================================


MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# File upload settings
# Increase max upload size to 10MB (default is 2.5MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB in bytes
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB in bytes

# Use MEDIA_ROOT for temp uploads on Railway
# Railway filesystem is ephemeral by default - for persistent storage, mount a volume at /app/media
# Guide: https://docs.railway.app/guides/volumes
if os.environ.get('DEPLOYED', 'False') == 'True':
    FILE_UPLOAD_TEMP_DIR = os.path.join(MEDIA_ROOT, 'temp_uploads')
    # Create temp directory if it doesn't exist
    os.makedirs(FILE_UPLOAD_TEMP_DIR, exist_ok=True)


# ============================================================
# EMAIL CONFIGURATION
# ============================================================


EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@example.com')


# ============================================================
# SITE CONFIGURATION
# ============================================================


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SESSION_COOKIE_AGE = 86400
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_ENGINE = 'django.contrib.sessions.backends.db'


# ============================================================
# SECURITY SETTINGS
# ============================================================


SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True


if os.environ.get('DEPLOYED', 'False') == 'True':
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
else: 
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = False


SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_NAME = 'wbpmisueso_sessionid'
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_NAME = 'csrftoken'


# ============================================================
# CACHE CONFIGURATION
# ============================================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}