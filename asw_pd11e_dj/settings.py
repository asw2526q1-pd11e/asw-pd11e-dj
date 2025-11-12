# flake8: noqa: E501
"""
Django settings for asw_pd11e_dj project.
"""
import os

from pathlib import Path

# -----------------------
# Base Settings
# -----------------------
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-8qu^s(p(l2xfx*u9b1qe%uucei#%9@q!lv$d==t5l!lk(+u2qs"
DEBUG = True
ALLOWED_HOSTS = ["asw-pd11e-dj.onrender.com", "localhost", "127.0.0.1"]

# -----------------------
# Installed Apps
# -----------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "blog",
    "communities",
    "accounts",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
]

SITE_ID = 1

# -----------------------
# Middleware
# -----------------------
MIDDLEWARE = [
    "allauth.account.middleware.AccountMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# -----------------------
# URLs and Templates
# -----------------------
ROOT_URLCONF = "asw_pd11e_dj.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

WSGI_APPLICATION = "asw_pd11e_dj.wsgi.application"

# -----------------------
# Database
# -----------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# -----------------------
# Password Validators
# -----------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -----------------------
# Internationalization
# -----------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# -----------------------
# Static Files (local)
# -----------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# -----------------------
# AWS S3 Settings for Media
# -----------------------
# -------------------------------
# Media Files (S3)
# -------------------------------
# Require these environment variables:
# AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN


def get_env_variable(var_name):
    try:
        return os.environ[var_name]
    except KeyError:
        raise ImproperlyConfigured(f"Set the {var_name} environment variable.")


AWS_ACCESS_KEY_ID = get_env_variable("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = get_env_variable("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = get_env_variable("AWS_SESSION_TOKEN")
AWS_STORAGE_BUCKET_NAME = "asw-pd11e-dj"
AWS_S3_REGION_NAME = "us-east-1"

STORAGES = {
    "default": {  # Media files
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "region_name": AWS_S3_REGION_NAME,
        },
    },
    "staticfiles": {  # Keep static files local
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/"

# -----------------------
# Auth / Allauth
# -----------------------
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': "392869001985-s2nnjrdrt2kv36hirrchk73t17gd84tu.apps.googleusercontent.com",
            'secret': "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",
            'key': ''
        }
    }
}

SOCIALACCOUNT_LOGIN_ON_GET = True
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# -----------------------
# Default primary key
# -----------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
