from __future__ import annotations

import django
from django.conf import settings


def pytest_sessionstart(session):
    settings.configure(
        DEBUG=False,
        USE_TZ=True,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        # ROOT_URLCONF="tests.urls",
        INSTALLED_APPS=[
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.messages",
            "django.contrib.sessions",
            "django.contrib.sites",
            "django_anchor_modeling",
            "dataviewer",
            "tests.orders",
        ],
        SITE_ID=1,
        SILENCED_SYSTEM_CHECKS=["RemovedInDjango50Warning"],
    )
    django.setup()
