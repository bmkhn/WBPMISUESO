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

# SECURITY WARNING: keep the secret key used in production secret!
# Generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
# DEVELOPMENT: DEBUG=True  | PRODUCTION: DEBUG=False
DEBUG = config('DEBUG', default=False, cast=bool)

# Allowed hosts for the application
# DEVELOPMENT: localhost,127.0.0.1 | PRODUCTION: yourdomain.com,www.yourdomain.com
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())


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
    'system.users.backends.EmailBackend',       # Email-based authentication (primary)
    'django.contrib.auth.backends.ModelBackend', # Username-based authentication (fallback)
]

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Password validation rules
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'  # Philippine Standard Time (UTC+8)
USE_I18N = True
USE_TZ = True  # Use timezone-aware datetimes


# ============================================================
# STATIC FILES (CSS, JavaScript, Images)
# ============================================================
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]

# Production: Collect static files with: python manage.py collectstatic
# STATIC_ROOT = BASE_DIR / 'staticfiles'

# ============================================================
# MEDIA FILES (User uploads)
# ============================================================

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Production: Consider using cloud storage (AWS S3, Google Cloud Storage)
# or a CDN for better performance and scalability


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

# Email Configuration Notes:
# --------------------------
# Development: Use console.EmailBackend (prints to console)
# Production: Use smtp.EmailBackend with proper credentials
#
# Gmail Setup:
#   1. Enable 2-Factor Authentication
#   2. Generate App Password: https://myaccount.google.com/apppasswords
#   3. Use App Password, not regular password
#
# Alternative Email Providers:
#   - SendGrid: EMAIL_HOST=smtp.sendgrid.net, PORT=587
#   - Mailgun: EMAIL_HOST=smtp.mailgun.org, PORT=587
#   - AWS SES: EMAIL_HOST=email-smtp.region.amazonaws.com, PORT=587


# ============================================================
# SITE CONFIGURATION
# ============================================================

# Base URL for email links and redirects
# DEVELOPMENT: http://localhost:8000
# PRODUCTION: https://yourdomain.com
SITE_URL = config('SITE_URL', default='http://localhost:8000')


# ============================================================
# MISCELLANEOUS
# ============================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================================================
# SESSION CONFIGURATION
# ============================================================

SESSION_COOKIE_AGE = 86400                      # 24 hours (1 day)
SESSION_SAVE_EVERY_REQUEST = True               # Reset timeout on each activity (sliding window)
SESSION_EXPIRE_AT_BROWSER_CLOSE = False         # Persist across browser restarts

# Session engine (database-backed for persistence across server restarts)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Session Configuration Notes:
# ----------------------------
# - SESSION_COOKIE_AGE: How long session lasts (24 hours = 86400 seconds)
# - SESSION_SAVE_EVERY_REQUEST: Sliding window - extends session on activity
# - SESSION_EXPIRE_AT_BROWSER_CLOSE: False = session persists (like "Remember Me")
#
# Alternative Session Backends:
# - 'django.contrib.sessions.backends.cache' (faster, not persistent)
# - 'django.contrib.sessions.backends.cached_db' (hybrid: cache + db fallback)


# ============================================================
# SECURITY SETTINGS
# ============================================================

# Cookie Security
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
SESSION_COOKIE_HTTPONLY = True                  # Prevent JavaScript access (XSS protection)
SESSION_COOKIE_SAMESITE = 'Lax'                 # CSRF protection (Strict/Lax/None)
SESSION_COOKIE_NAME = 'wbpmisueso_sessionid'    # Custom name for additional security

# CSRF Protection
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_HTTPONLY = False                    # Allow JavaScript access for AJAX
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_NAME = 'csrftoken'

# Security Headers
SECURE_BROWSER_XSS_FILTER = True                # XSS protection
X_FRAME_OPTIONS = 'DENY'                        # Prevent clickjacking
SECURE_CONTENT_TYPE_NOSNIFF = True              # Prevent MIME-sniffing

# HTTPS Settings (ENABLE IN PRODUCTION)
# Uncomment these when deploying with HTTPS/SSL certificate:
# SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
# SECURE_HSTS_SECONDS = 31536000                # HTTP Strict Transport Security (1 year)
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# Security Notes:
# ---------------
# DEVELOPMENT (HTTP):
#   - SESSION_COOKIE_SECURE = False
#   - CSRF_COOKIE_SECURE = False
#   - SECURE_SSL_REDIRECT = False
#
# PRODUCTION (HTTPS):
#   - SESSION_COOKIE_SECURE = True  (cookies only sent over HTTPS)
#   - CSRF_COOKIE_SECURE = True     (CSRF token only sent over HTTPS)
#   - SECURE_SSL_REDIRECT = True    (force all traffic to HTTPS)
#   - Enable HSTS headers for additional security


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

# Cache Backend Options:
# ----------------------
# Development:
#   - locmem.LocMemCache (in-memory, simple, not shared across processes)
#
# Production:
#   - redis.RedisCache (recommended, fast, shared)
#     * Install: pip install django-redis
#     * BACKEND: 'django_redis.cache.RedisCache'
#     * LOCATION: 'redis://127.0.0.1:6379/1'

# ============================================================
# PRODUCTION DEPLOYMENT CHECKLIST
# ============================================================
#
# Before deploying to production, ensure:
#
# 1. ENVIRONMENT VARIABLES (.env)
#    ✓ Generate new SECRET_KEY
#    ✓ Set DEBUG=False
#    ✓ Configure ALLOWED_HOSTS with your domain
#    ✓ Set up PostgreSQL database credentials
#    ✓ Configure email settings (use App Password for Gmail)
#    ✓ Update SITE_URL to your domain
#    ✓ Set SESSION_COOKIE_SECURE=True
#    ✓ Set CSRF_COOKIE_SECURE=True
#
# 2. SECURITY
#    ✓ Uncomment HTTPS settings (SECURE_SSL_REDIRECT, HSTS)
#    ✓ Install SSL certificate (Let's Encrypt, etc.)
#    ✓ Review ALLOWED_HOSTS
#    ✓ Change SESSION_COOKIE_NAME if needed
#
# 3. DATABASE
#    ✓ Create PostgreSQL database
#    ✓ Run migrations: python manage.py migrate
#    ✓ Create superuser: python manage.py createsuperuser
#    ✓ Set up database backups
#
# 4. STATIC FILES
#    ✓ Uncomment STATIC_ROOT in settings
#    ✓ Run: python manage.py collectstatic
#    ✓ Configure web server to serve /static/ and /media/
#
# 5. WEB SERVER
#    ✓ Set up Nginx/Apache as reverse proxy
#    ✓ Configure Gunicorn/uWSGI for Django
#    ✓ Set up systemd service for auto-restart
#    ✓ Configure firewall (allow ports 80, 443)
#
# 6. MONITORING & LOGGING
#    ✓ Set up error logging (Sentry, etc.)
#    ✓ Configure Django logging
#    ✓ Set up monitoring (New Relic, DataDog, etc.)
#    ✓ Configure log rotation
#
# 7. PERFORMANCE
#    ✓ Configure Redis/Memcached for caching
#    ✓ Set up CDN for static files (optional)
#    ✓ Configure database connection pooling
#    ✓ Enable Gzip compression
#
# 8. TESTING
#    ✓ Run all tests: python manage.py test
#    ✓ Check for security issues: python manage.py check --deploy
#    ✓ Test email functionality
#    ✓ Test file uploads
#
# 9. DOCUMENTATION
#    ✓ Document deployment process
#    ✓ Update README.md
#    ✓ Document environment variables
#    ✓ Create runbook for common tasks
#
# 10. BACKUP & RECOVERY
#     ✓ Set up automated database backups
#     ✓ Back up media files
#     ✓ Test restore procedure
#     ✓ Document recovery process
#
# Django Deployment Security Check:
# python manage.py check --deploy
#
# ============================================================