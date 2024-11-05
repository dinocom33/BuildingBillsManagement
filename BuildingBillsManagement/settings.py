import os
from pathlib import Path
from django.contrib.messages import constants as messages

from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', None)

DEBUG = bool(int(os.getenv('DEBUG', 0)))

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(' ')

AUTH_USER_MODEL = "accounts.User"

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    "building.apps.BuildingConfig",
    "accounts.apps.AccountsConfig",
    "pages.apps.PagesConfig"
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'BuildingBillsManagement.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
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

WSGI_APPLICATION = 'BuildingBillsManagement.wsgi.application'

DATABASES = {
    "default": {
        # "ENGINE": "django.db.backends.postgresql",
        'ENGINE': 'django.db.backends.mysql',
        "NAME": os.getenv('DATABASE_NAME', None),
        "USER": os.getenv('DATABASE_USER', None),
        "PASSWORD": os.getenv('DATABASE_PASSWORD', None),
        "HOST": os.getenv('DATABASE_HOST', None),
        "PORT": os.getenv('DATABASE_PORT', None),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_ROOT = BASE_DIR / 'static'
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static_files'
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MESSAGE_TAGS = {
    messages.INFO: 'info',
    messages.ERROR: 'danger',
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', None)
EMAIL_USE_TLS = bool(int(os.getenv('EMAIL_USE_TLS', 0)))
EMAIL_PORT = os.getenv('EMAIL_PORT', 0)
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', None)
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', None)
CONTACT_FORM_EMAIL = os.getenv('CONTACT_FORM_EMAIL', None)

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 60 * 60
SESSION_SAVE_EVERY_REQUEST = True

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', None)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Sofia'

LOGIN_URL = '/accounts/login/'

# CSRF_TRUSTED_ORIGINS = ['https://11ab-78-90-113-174.ngrok-free.app']
