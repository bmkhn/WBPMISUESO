"""
Django settings for WBPMISUESO project.

Web-Based Project Management Information System for University Extension Services Office

For deployment checklist, see:
https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
"""

from pathlib import Path
from decouple import config, Csv
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# CORE SETTINGS
# ============================================================

SECRET_KEY = config('SECRET_KEY')

DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*", cast=Csv())
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())


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
# Supports both PostgreSQL (recommended) and SQLite (development)
# Configure via .env file

DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': config('DB_NAME', default=str(BASE_DIR / 'db.sqlite3')),
        'USER': config('DB_USER', default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default=''),
        'PORT': config('DB_PORT', default=''),
        'OPTIONS': {
            'connect_timeout': 10,  # Connection timeout in seconds
        },
        'CONN_MAX_AGE': 600,  # Keep database connections alive for 10 minutes (connection pooling)
    }
}

# ============================================================
# AUTHENTICATION & AUTHORIZATION
# ============================================================

# Custom authentication backend to allow email login
AUTHENTICATION_BACKENDS = [
    'system.users.backends.EmailBackend',           # Email-based authentication (primary)
    'django.contrib.auth.backends.ModelBackend',    # Username-based authentication (fallback)
]

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Password validation rules
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,  # Minimum 8 characters
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Password reset timeout (1 hour)
PASSWORD_RESET_TIMEOUT = 3600

# Login/Logout URLs
LOGIN_URL = '/login/'
LOGOUT_REDIRECT_URL = '/login/'


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'  # Philippine Standard Time (UTC+8)
USE_I18N = True
USE_TZ = True  # Use timezone-aware datetimes


# ============================================================
# STATIC FILES (CSS, JavaScript, Images)
# ============================================================

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]

# Production: Collect static files with: python manage.py collectstatic
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ============================================================
# MEDIA FILES (User uploads)
# ============================================================

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Production: Consider using cloud storage (AWS S3, Google Cloud Storage) or a CDN for better performance and scalability

# ============================================================
# EMAIL CONFIGURATION
# ============================================================

EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@example.com')

# ============================================================
# SITE CONFIGURATION
# ============================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SESSION_COOKIE_AGE = 86400                      # 24 hours (1 day)
SESSION_SAVE_EVERY_REQUEST = True               # Reset timeout on each activity (sliding window)
SESSION_EXPIRE_AT_BROWSER_CLOSE = False         # Persist across browser restarts

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# ============================================================
# SECURITY SETTINGS
# ============================================================

# Security Headers
SECURE_BROWSER_XSS_FILTER = True                # XSS protection
X_FRAME_OPTIONS = 'DENY'                        # Prevent clickjacking
SECURE_CONTENT_TYPE_NOSNIFF = True              # Prevent MIME-sniffing

# PRODUCTION (HTTPS):
SESSION_COOKIE_SECURE = True                    # Cookies only sent over HTTPS
CSRF_COOKIE_SECURE = True                       # CSRF token only sent over HTTPS
SECURE_SSL_REDIRECT = True                      # Force all traffic to HTTPS

SESSION_COOKIE_HTTPONLY = True                  # Prevent JavaScript access (XSS protection)
SESSION_COOKIE_SAMESITE = 'Lax'                 # CSRF protection (Strict/Lax/None)
SESSION_COOKIE_NAME = 'wbpmisueso_sessionid'    # Custom name for additional security

CSRF_COOKIE_HTTPONLY = False                    # Allow JavaScript access for AJAX
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_NAME = 'csrftoken'

# ============================================================
# CACHE CONFIGURATION
# ============================================================
# Used for notification count optimization and query caching

CACHES = {
    'default': {
        'BACKEND': config('CACHE_BACKEND', default='django.core.cache.backends.locmem.LocMemCache'),
        'LOCATION': config('CACHE_LOCATION', default='unique-snowflake'),
        'TIMEOUT': 300,  # 5 minutes default
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}