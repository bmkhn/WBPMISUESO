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

ALLOWED_HOSTS = [ 'localhost', '127.0.0.1', 'testserver', 'uesopmis.up.railway.app', 'healthcheck.railway.app', 'uesomis.pythonanywhere.com' ]
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
    'system.utils',

    # Third-party Apps
    'rest_framework',
    'rest_framework_api_key',
    'rest_framework.authtoken',
    'drf_spectacular',
    'social_django',

    # Bootstrap
    'widget_tweaks',
]

MIDDLEWARE = [
    # Security and Static Files
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    # Sessions, Common Middleware, CSRF
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    # Authentication and Messages
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    # Custom Cache Middleware
    'system.users.middleware.SmartCacheMiddleware',

    # Clickjacking Protection
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication', 
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# API Documentation Metadata
SPECTACULAR_SETTINGS = {
    'TITLE': 'UESO-PMIS',
    'DESCRIPTION': 'UESO-PMIS, the project monitorinf and management system of Palawan State University, University Extension Services Office.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
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
    'social_core.backends.google.GoogleOAuth2',
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

# Social Auth Settings
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', '')

# Social Auth Pipeline
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'system.users.pipeline.get_username',
    'system.users.pipeline.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'system.users.pipeline.user_details',
)

# Redirect after successful social auth
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/redirector/'
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/redirector/'
SOCIAL_AUTH_LOGIN_ERROR_URL = '/login/?error=social_auth_failed'


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

# For Railway deployment with volume mounted at /media/ ### Check this ###
if os.environ.get('DEPLOYED', 'False') == 'True':
    MEDIA_ROOT = '/media'
else:
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# File upload settings
# Increase max upload size to 10MB (default is 2.5MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB in bytes
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB in bytes

# Use MEDIA_ROOT for temp uploads on Railway
if os.environ.get('DEPLOYED', 'False') == 'True':
    FILE_UPLOAD_TEMP_DIR = os.path.join(MEDIA_ROOT, 'temp_uploads')
    # Create temp directory if it doesn't exist
    os.makedirs(FILE_UPLOAD_TEMP_DIR, exist_ok=True)


# ============================================================
# EMAIL CONFIGURATION
# ============================================================


if os.environ.get('DEPLOYED', 'False') == 'True':
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')
    SENDGRID_FROM_EMAIL = os.environ.get('SENDGRID_FROM_EMAIL', 'noreply@example.com')
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


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

USER_CACHE_SECONDS = 600            # 10 minutes for logged-in pages
CACHE_MIDDLEWARE_SECONDS = 86400    # 24 hours for anonymous pages
CACHE_MIDDLEWARE_KEY_PREFIX = ''

if os.environ.get('DEPLOYED', 'False') == 'True':  
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379')
else:
    REDIS_URL = 'redis://127.0.0.1:6379'

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"{REDIS_URL}/1",  # General cache (for anonymous pages)
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"{REDIS_URL}/2",  # Sessions only
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'KEY_PREFIX': 'session:',
        }
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'

SESSION_COOKIE_AGE = 86400          # 24 hours
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False


# ============================================================
# CELERY CONFIGURATION
# ============================================================


CELERY_BROKER_URL = f"{REDIS_URL}/0"
CELERY_RESULT_BACKEND = f"{REDIS_URL}/0"


CELERY_BEAT_SCHEDULE = {
    'publish_announcements_every_minute': {
        'task': 'system.scheduler.tasks.celery_publish_scheduled_announcements',
        'schedule': 60.0,  # every minute
    },
    'clear_sessions_daily': {
        'task': 'system.scheduler.tasks.celery_clear_expired_sessions',
        'schedule': 24 * 60 * 60,  # every 24 hours
    },
    'update_event_statuses_daily': {
        'task': 'system.scheduler.tasks.celery_update_event_statuses',
        'schedule': 24 * 60 * 60,  # every 24 hours
    },
    'update_project_statuses_daily': {
        'task': 'system.scheduler.tasks.celery_update_project_statuses',
        'schedule': 24 * 60 * 60,  # every 24 hours
    },
    'update_user_expert_status_daily': {
        'task': 'system.scheduler.tasks.celery_update_user_expert_status',
        'schedule': 24 * 60 * 60,  # every 24 hours
    },
    'send_event_reminders_daily': {
        'task': 'system.scheduler.tasks.celery_send_event_reminders',
        'schedule': 24 * 60 * 60,  # every 24 hours
    },
}