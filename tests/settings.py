from __future__ import annotations

# SECRET_KEY = "NOTASECRET"

# ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django_anchor_modeling",
    "dataviewer",
    "metadata",
    "tests.orders",
]

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3"}}

TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates"}]

# ROOT_URLCONF = "tests.urls"

# MIDDLEWARE = ["corsheaders.middleware.CorsMiddleware"]

# SECURE_PROXY_SSL_HEADER = ("HTTP_FAKE_SECURE", "true")

USE_TZ = True
