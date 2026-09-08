import os
from pathlib import Path

import dj_database_url


# =========================================================
# BASE DIRECTORY
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# =========================================================
# SECURITY
# =========================================================

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-change-this-secret-key"
)


# =========================================================
# DEBUG
# =========================================================

DEBUG = (
    os.environ.get(
        "DEBUG",
        "False"
    ).lower()
    == "true"
)


# =========================================================
# ALLOWED HOSTS
# =========================================================

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
]

render_hostname = os.environ.get(
    "RENDER_EXTERNAL_HOSTNAME"
)

if render_hostname:
    ALLOWED_HOSTS.append(
        render_hostname
    )

# Your Render domain
ALLOWED_HOSTS.append(
    "garden-ecommerce-django.onrender.com"
)


# =========================================================
# APPLICATIONS
# =========================================================

INSTALLED_APPS = [

    "django.contrib.admin",

    "django.contrib.auth",

    "django.contrib.contenttypes",

    "django.contrib.sessions",

    "django.contrib.messages",

    "django.contrib.staticfiles",

    "cloudinary",

    "cloudinary_storage",

    "store",
]


# =========================================================
# MIDDLEWARE
# =========================================================

MIDDLEWARE = [

    "django.middleware.security.SecurityMiddleware",

    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",

    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",

    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# =========================================================
# URL CONFIG
# =========================================================

ROOT_URLCONF = "myproject.urls"


# =========================================================
# TEMPLATES
# =========================================================

TEMPLATES = [

    {
        "BACKEND":
            "django.template.backends.django.DjangoTemplates",

        "DIRS": [
            BASE_DIR / "templates"
        ],

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


# =========================================================
# WSGI
# =========================================================

WSGI_APPLICATION = (
    "myproject.wsgi.application"
)


# =========================================================
# DATABASE
# =========================================================

DATABASES = {

    "default":
        dj_database_url.config(

            default=(
                "sqlite:///"
                + str(
                    BASE_DIR / "db.sqlite3"
                )
            ),

            conn_max_age=600,

            ssl_require=(
                bool(
                    os.environ.get(
                        "DATABASE_URL"
                    )
                )
            ),
        )
}


# =========================================================
# PASSWORD VALIDATION
# =========================================================

AUTH_PASSWORD_VALIDATORS = [

    {
        "NAME":
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },

    {
        "NAME":
            "django.contrib.auth.password_validation.MinimumLengthValidator",
    },

    {
        "NAME":
            "django.contrib.auth.password_validation.CommonPasswordValidator",
    },

    {
        "NAME":
            "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# =========================================================
# INTERNATIONALIZATION
# =========================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True


# =========================================================
# STATIC FILES
# =========================================================

STATIC_URL = "/static/"

STATIC_ROOT = (
    BASE_DIR / "staticfiles"
)

STATICFILES_DIRS = []

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)


# =========================================================
# MEDIA / CLOUDINARY
# =========================================================

MEDIA_URL = "/media/"

DEFAULT_FILE_STORAGE = (
    "cloudinary_storage.storage.MediaCloudinaryStorage"
)

CLOUDINARY_STORAGE = {

    "CLOUD_NAME": os.environ.get(
        "CLOUDINARY_CLOUD_NAME"
    ),

    "API_KEY": os.environ.get(
        "CLOUDINARY_API_KEY"
    ),

    "API_SECRET": os.environ.get(
        "CLOUDINARY_API_SECRET"
    ),
}


# =========================================================
# DEFAULT PRIMARY KEY
# =========================================================

DEFAULT_AUTO_FIELD = (
    "django.db.models.BigAutoField"
)


# =========================================================
# EMAIL CONFIGURATION
# =========================================================
#
# IMPORTANT:
# Use Render Environment Variables:
#
# EMAIL_HOST
# EMAIL_PORT
# EMAIL_HOST_USER
# EMAIL_HOST_PASSWORD
# EMAIL_USE_TLS
# DEFAULT_FROM_EMAIL
#
# DO NOT use GMAIL_EMAIL or
# GMAIL_APP_PASSWORD here.
# =========================================================

EMAIL_BACKEND = (
    "django.core.mail.backends.smtp.EmailBackend"
)

EMAIL_HOST = os.environ.get(
    "EMAIL_HOST",
    "smtp.gmail.com"
)

EMAIL_PORT = int(
    os.environ.get(
        "EMAIL_PORT",
        "587"
    )
)

EMAIL_HOST_USER = os.environ.get(
    "EMAIL_HOST",
    os.environ.get(
        "EMAIL_HOST_USER",
        ""
    )
)

# Fix:
# EMAIL_HOST_USER must come from
# EMAIL_HOST_USER environment variable.
EMAIL_HOST_USER = os.environ.get(
    "EMAIL_HOST_USER",
    ""
)

EMAIL_HOST_PASSWORD = os.environ.get(
    "EMAIL_HOST_PASSWORD",
    ""
)

EMAIL_USE_TLS = (
    os.environ.get(
        "EMAIL_USE_TLS",
        "True"
    ).lower()
    == "true"
)

# Very important for Render:
# prevents SMTP connection from hanging
# until Gunicorn kills the worker.
EMAIL_TIMEOUT = 5

DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    EMAIL_HOST_USER
)


# =========================================================
# RAZORPAY
# =========================================================

RAZORPAY_KEY_ID = os.environ.get(
    "RAZORPAY_KEY_ID",
    ""
)

RAZORPAY_KEY_SECRET = os.environ.get(
    "RAZORPAY_KEY_SECRET",
    ""
)


# =========================================================
# LOGIN / LOGOUT
# =========================================================

LOGIN_URL = "/admin/login/"

LOGIN_REDIRECT_URL = "/"

LOGOUT_REDIRECT_URL = "/"


# =========================================================
# CSRF
# =========================================================

CSRF_TRUSTED_ORIGINS = [
    "https://garden-ecommerce-django.onrender.com",
]


# =========================================================
# SESSION
# =========================================================

SESSION_COOKIE_SECURE = not DEBUG

CSRF_COOKIE_SECURE = not DEBUG


# =========================================================
# SECURITY HEADERS
# =========================================================

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


# =========================================================
# ADMIN USER ENVIRONMENT VARIABLES
# =========================================================

ADMIN_USERNAME = os.environ.get(
    "ADMIN_USERNAME",
    ""
)

ADMIN_EMAIL = os.environ.get(
    "ADMIN_EMAIL",
    ""
)

ADMIN_PASSWORD = os.environ.get(
    "ADMIN_PASSWORD",
    ""
)