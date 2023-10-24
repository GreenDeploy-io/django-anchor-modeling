from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate


class EnsureKnotChoicesExistConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_anchor_modeling"

    def ready(self):
        from django_anchor_modeling import signals

        if getattr(
            settings,
            "DJANGO_ANCHOR_MODELING_AUTO_POPULATE_CHOICES_FOR_KNOT_SUBCLASSES",
            False,
        ):
            post_migrate.connect(signals.populate_choices, sender=self)
