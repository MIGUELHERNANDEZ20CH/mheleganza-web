# config/settings.py
import os
import sys
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

IS_TESTING = 'test' in sys.argv


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


DEBUG = env_bool('DJANGO_DEBUG', IS_TESTING)
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    if DEBUG or IS_TESTING:
        SECRET_KEY = 'django-insecure-local-development-only'
    else:
        raise ImproperlyConfigured('DJANGO_SECRET_KEY must be configured when DEBUG is disabled.')

# ==========================================
# CONFIGURACIÓN DE HOSTS (PythonAnywhere)
# ==========================================
PYTHONANYWHERE_HOST = 'mheleganza.pythonanywhere.com'

development_hosts = (
    ['localhost', '127.0.0.1', 'testserver', '.devtunnels.ms', '.githubpreview.dev']
    if DEBUG or IS_TESTING
    else []
)
configured_hosts = [
    host.strip()
    for host in os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')
    if host.strip()
]
ALLOWED_HOSTS = list(dict.fromkeys([*development_hosts, *configured_hosts, PYTHONANYWHERE_HOST, '*']))

development_csrf_origins = (
    [
        'http://127.0.0.1:8000',
        'http://localhost:8000',
        'https://*.devtunnels.ms',
        'https://*.githubpreview.dev',
    ]
    if DEBUG or IS_TESTING
    else []
)
configured_csrf_origins = [
    origin.strip()
    for origin in os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys([
    *development_csrf_origins,
    *configured_csrf_origins,
    f'https://{PYTHONANYWHERE_HOST}',
]))

if not DEBUG and not IS_TESTING and not ALLOWED_HOSTS:
    raise ImproperlyConfigured('DJANGO_ALLOWED_HOSTS must contain the production host names.')

if not DEBUG and not IS_TESTING and not os.getenv('DATABASE_URL'):
    pass

if not DEBUG and not IS_TESTING and not os.getenv('EMAIL_HOST'):
    pass

if (
    not DEBUG
    and not IS_TESTING
    and bool(os.getenv('EMAIL_HOST_USER')) != bool(os.getenv('EMAIL_HOST_PASSWORD'))
):
    raise ImproperlyConfigured('Configure both EMAIL_HOST_USER and EMAIL_HOST_PASSWORD, or neither.')

# Aplicaciones instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Módulos requeridos para autenticación con Google (django-allauth)
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # Apps del proyecto MH’ELEGANZA
    'app_usuarios',
    'app_productos',
    'app_carrito',
    'app_pedido',
    'app_inventario',
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
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{(BASE_DIR / "db.sqlite3").as_posix()}',
        conn_max_age=600,
        conn_health_checks=True,
    )
}

if os.getenv('DATABASE_URL', '').lower().startswith(('mysql://', 'mysql+')):
    import pymysql

    pymysql.install_as_MySQLdb()

# ==========================================
# CONFIGURACIÓN DE ALLAUTH / GOOGLE OAUTH
# ==========================================
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_EMAIL_VERIFICATION = 'none'

LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_PERMISSIONS = 0o640
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o750
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}
WHITENOISE_MAX_AGE = 0 if DEBUG else 31_536_000
WHITENOISE_MANIFEST_STRICT = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SESSION_COOKIE_AGE = 1800
SESSION_SAVE_EVERY_REQUEST = True
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)
EMAIL_USE_SSL = env_bool('EMAIL_USE_SSL')
EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '20'))
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'no-reply@mheleganza.com')
SERVER_EMAIL = os.getenv('SERVER_EMAIL', DEFAULT_FROM_EMAIL)
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', '').strip()

if DEBUG:
    EMAIL_BACKEND = os.getenv(
        'EMAIL_BACKEND',
        'django.core.mail.backends.console.EmailBackend',
    )
elif not IS_TESTING:
    if EMAIL_BACKEND != 'django.core.mail.backends.smtp.EmailBackend':
        pass
    if not os.getenv('DEFAULT_FROM_EMAIL'):
        pass
if EMAIL_USE_TLS and EMAIL_USE_SSL:
    raise ImproperlyConfigured('Choose either EMAIL_USE_TLS or EMAIL_USE_SSL, not both.')

STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')
STRIPE_CURRENCY = os.getenv('STRIPE_CURRENCY', 'cop').lower()

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER', '')
TWILIO_MESSAGING_SERVICE_SID = os.getenv('TWILIO_MESSAGING_SERVICE_SID', '')
TWILIO_DEFAULT_COUNTRY_CODE = os.getenv('TWILIO_DEFAULT_COUNTRY_CODE', '57')
SMS_OTP_TTL_SECONDS = int(os.getenv('SMS_OTP_TTL_SECONDS', '600'))
SMS_OTP_RESEND_SECONDS = int(os.getenv('SMS_OTP_RESEND_SECONDS', '60'))
SMS_OTP_MAX_ATTEMPTS = int(os.getenv('SMS_OTP_MAX_ATTEMPTS', '5'))

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL_REDIRECT', not DEBUG and not IS_TESTING)
SECURE_HSTS_SECONDS = int(os.getenv('DJANGO_SECURE_HSTS_SECONDS', '31536000' if not DEBUG else '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool('DJANGO_HSTS_INCLUDE_SUBDOMAINS')
SECURE_HSTS_PRELOAD = env_bool('DJANGO_HSTS_PRELOAD')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'

if env_bool('DJANGO_USE_X_FORWARDED_PROTO'):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ACCOUNT_LOGIN_TEMPLATE = 'app_usuarios/login.html'