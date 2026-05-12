from pathlib import Path
import os
from decouple import config
from datetime import timedelta

# =========================
# Base directory
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent  # Project root directory

# =========================
# Secrets & Debug
# =========================
SECRET_KEY = config('DJANGO_SECRET_KEY')  # Django secret key from .env
OTP_SECRET_KEY = config('OTP_SECRET_KEY')  # OTP hashing secret
OTP_LENGTH = config('OTP_LENGTH', cast=int, default=6)
OTP_EXPIRY_MINUTES = config('OTP_EXPIRY_MINUTES', cast=int, default=5)
OTP_RESEND_INTERVAL = config('OTP_RESEND_INTERVAL', cast=int, default=60)
OTP_MAX_USE_COUNT = config('OTP_MAX_USE_COUNT', cast=int, default=5)
DEBUG = config('DEBUG', cast=bool, default=False)  # Production=False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost').split(',')  # Allowed domains

# =========================
# Installed Applications
# =========================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'social_django',  # Google OAuth2 login
    'rest_framework',  # DRF
    # 'rest_framework.authtoken',  # Token auth
    'corsheaders',  # CORS
    'rest_framework_simplejwt',  # JWT auth
    'rest_framework_simplejwt.token_blacklist',  # JWT token blacklist

    # Local apps
    'account.apps.AccountConfig',
    'store.apps.StoreConfig',
]

# =========================
# Middleware
# =========================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # Enable CORS
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # CSRF protection
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  # Clickjacking protection
    'social_django.middleware.SocialAuthExceptionMiddleware',  # Social auth errors
]

ROOT_URLCONF = 'config.urls'

# =========================
# Templates
# =========================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',  # Social auth
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# =========================
# Database
# =========================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Production-ready MySQL recommended
        'NAME': config('DB_NAME'),
        # Production-ready MySQL configuration (commented)
        # 'USER': config('DB_USER'),
        # 'PASSWORD': config('DB_PASSWORD'),
        # 'HOST': config('DB_HOST', default='127.0.0.1'),
        # 'PORT': config('DB_PORT', default='3306'),
        # 'OPTIONS': {'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"},
    }
}

# =========================
# Password validation
# =========================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =========================
# Internationalization
# =========================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Dhaka'
USE_I18N = True
USE_TZ = True

# =========================
# Static & Media files
# =========================
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR / 'static')]  # Development static files
STATIC_ROOT = os.path.join(BASE_DIR / 'staticfiles')  # Production collectstatic
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR / 'media')
# Optional: Use S3/CDN for production
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'

# =========================
# Authentication & JWT
# =========================
AUTH_USER_MODEL = "account.User"
AUTHENTICATION_BACKENDS = [
    'social_core.backends.google.GoogleOAuth2',  # Google OAuth2 login
    'django.contrib.auth.backends.ModelBackend',  # Default
    'account.backends.AuthBackend',  # Email/Phone login
]

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config('GOOGLE_CLIENT_ID')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config('GOOGLE_CLIENT_SECRET')
LOGIN_URL = 'login'
LOGOUT_URL = 'logout'
LOGIN_REDIRECT_URL = 'home'

# =========================
# Email configuration
# =========================
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool, default=True)
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', cast=int, default=587)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')  # App Password production

# =========================
# Default primary key
# =========================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =========================
# Celery configuration
# =========================
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# =========================
# Django REST Framework
# =========================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # Token Authentication by default drf 
        # 'rest_framework.authentication.TokenAuthentication',
        # JWT Authentication this is used for API authentication
        'rest_framework_simplejwt.authentication.JWTAuthentication', 
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        # Default permission for API views 
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# =========================
# Simple JWT
# =========================
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# =========================
# Logging
# =========================
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {'standard': {'format': '[{levelname}] {asctime} {name} - {message}', 'style': '{'}},
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'level': 'INFO', 'formatter': 'standard'},
        'debug_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'filename': os.path.join(LOG_DIR, 'debug.log'),
            'maxBytes': 5*1024*1024,
            'backupCount': 5,
            'formatter': 'standard',
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'filename': os.path.join(LOG_DIR, 'error.log'),
            'maxBytes': 5*1024*1024,
            'backupCount': 5,
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django': {'handlers': ['console', 'error_file'], 'level': 'INFO', 'propagate': False},
        'project': {'handlers': ['console', 'debug_file', 'error_file'], 'level': 'DEBUG', 'propagate': False},
    },
}

# =========================
# Security headers
# =========================
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'