import django
from django.conf import settings
from django.core.management import call_command

# print("PYTHONPATH:", os.environ.get("PYTHONPATH", "Not set"))

# print(sys.path)

settings.configure(
    DEBUG=True,
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    },
    INSTALLED_APPS=(
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django_anchor_modeling",
        "dataviewer",
        "metadata",
        "tests.orders",
    ),
    # Add other required settings here
)

# Initialize Django
django.setup()

call_command("makemigrations", "orders")
call_command("makemigrations", "metadata")
call_command("makemigrations", "dataviewer")
