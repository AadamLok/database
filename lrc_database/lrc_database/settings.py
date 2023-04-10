"""
Django settings for lrc_database project.

Generated by 'django-admin startproject' using Django 3.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import os
from pathlib import Path
from typing import List

import sentry_sdk
from django.contrib import messages
from sentry_sdk.integrations.django import DjangoIntegration

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

SECRET_KEY = os.environ.get("LRC_DATABASE_SECRET_KEY", "INSECURE-REPLACE-ME")

ALLOWED_HOSTS: List[str] = os.environ.get("LRC_DATABASE_ALLOWED_HOSTS", ".localhost,127.0.0.1,[::1]").split(",")

# ALLOWED_HOSTS = ["0.0.0.0"]

CSRF_TRUSTED_ORIGINS = ["http://3.137.183.137:80"]

CORS_ORIGIN_WHITELIST = ["http://3.137.183.137:80"]

CORS_ALLOWED_ORIGINS = ["https://www.umass.edu"]

DEBUG = os.environ.get("LRC_DATABASE_DEBUG", "0") == "1"


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "crispy_forms",
    "crispy_bootstrap5",
    "corsheaders",
    "main",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    #custom
    "main.middleware.TimezoneMiddleware"
]

ROOT_URLCONF = "lrc_database.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR.joinpath("main", "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "main.context_processors.alert_counts",
            ],
        },
    },
]

WSGI_APPLICATION = "lrc_database.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTH_USER_MODEL = "main.LRCDatabaseUser"

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/New_York"

USE_I18N = True

USE_L10N = False # True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "/static/"

STATIC_ROOT = "/srv/static"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Authentication

LOGIN_REDIRECT_URL = "index"

LOGOUT_REDIRECT_URL = "index"


# Crispy Forms

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

CRISPY_TEMPLATE_PACK = "bootstrap5"


# Form input formats

DATETIME_INPUT_FORMATS = ["%Y-%m-%d %I:%M %p"]


# Messages

MESSAGE_TAGS = {
    messages.DEBUG: "primary",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "danger",
}
"""
Relevant documentation:
 - Bootstrap classes: https://getbootstrap.com/docs/5.0/components/alerts/
 - Message levels: https://docs.djangoproject.com/en/4.0/ref/settings/#message-tags

Also see the messages.html template.
"""


# Email

EMAIL_BACKEND = "django_ses.SESBackend"

# AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set via environment variables

AWS_SES_REGION_NAME = "us-east-2"

AWS_SES_REGION_ENDPOINT = "email.us-east-2.amazonaws.com"

# Sentry

if SENTRY_DSN := os.environ.get("SENTRY_DSN"):
    sentry_sdk.init(dsn=SENTRY_DSN, integrations=[DjangoIntegration()], traces_sample_rate=1.0, send_default_pii=True)
