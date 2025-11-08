"""
Django settings for WBPMISUESO project.

Web-Based Project Management Information System for University Extension Services Office

For deployment checklist, see:
https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# CORE SETTINGS
# ============================================================

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback-key-change-in-production')

if os.getenv('DEPLOYED', 'False') == 'True':
    DEBUG = False
    ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', '').split(',') if host.strip()]
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if origin.strip()]
else:
    DEBUG = True
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

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

if os.getenv('DEPLOYED', 'False') == 'True' and os.getenv('DATABASE_URL'):
    # Railway PostgreSQL (auto-configured)
    try:
        import dj_database_url
        DATABASES = {
            'default': dj_database_url.config(
                default=os.getenv('DATABASE_URL'),
                conn_max_age=600,
                conn_health_checks=True,
            )
        }
        print("✓ Using DATABASE_URL for database connection")
    except ImportError:
        print("✗ dj-database-url not installed, falling back to manual config")
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.getenv('PGDATABASE', 'railway'),
                'USER': os.getenv('PGUSER', 'postgres'),
                'PASSWORD': os.getenv('PGPASSWORD', ''),
                'HOST': os.getenv('PGHOST', 'localhost'),
                'PORT': os.getenv('PGPORT', '5432'),
                'CONN_MAX_AGE': 600,
            }
        }

elif os.getenv('DB_ENGINE'):
    # Manual Database Configuration
    db_engine = os.getenv('DB_ENGINE')
    
    if 'sqlite' in db_engine:
        # SQLite configuration (no timeout option)
        DATABASES = {
            'default': {
                'ENGINE': db_engine,
                'NAME': os.getenv('DB_NAME', str(BASE_DIR / 'db.sqlite3')),
            }
        }
    else:
        # PostgreSQL/MySQL Manual Configuration
        DATABASES = {
            'default': {
                'ENGINE': db_engine,
                'NAME': os.getenv('DB_NAME', ''),
                'USER': os.getenv('DB_USER', ''),
                'PASSWORD': os.getenv('DB_PASSWORD', ''),
                'HOST': os.getenv('DB_HOST', ''),
                'PORT': os.getenv('DB_PORT', ''),
                'OPTIONS': {
                    'connect_timeout': 10,
                },
                'CONN_MAX_AGE': 600,
            }
        }
else:
    # Default to SQLite if no configuration provided
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


# ============================================================
# EMAIL CONFIGURATION
# ============================================================


EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@example.com')


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


if os.getenv('DEPLOYED', 'False') == 'True':
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_HTTPONLY = True
else: 
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_HTTPONLY = False


SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_NAME = 'wbpmisueso_sessionid'
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_NAME = 'csrftoken'


# ============================================================
# CACHE CONFIGURATION
# ============================================================

if os.getenv('DEPLOYED', 'False') == 'True':
    # Production Cache Configuration
    CACHES = {
        'default': {
            'BACKEND': os.getenv('CACHE_BACKEND', 'django.core.cache.backends.locmem.LocMemCache'),
            'LOCATION': os.getenv('REDIS_URL', 'unique-snowflake'),
            'TIMEOUT': 300,
            'OPTIONS': {
                'MAX_ENTRIES': 1000
            }
        }
    }
else:
    # Development Cache Configuration
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