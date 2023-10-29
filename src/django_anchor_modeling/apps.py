from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import class_prepared, post_migrate


def historized_setup(sender, **kwargs):
    if hasattr(sender, "historized_setup"):
        sender.historized_setup()


class DjangoAnchorModelingApp(AppConfig):
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

    def __init__(self, *args, **kwargs):
        class_prepared.connect(historized_setup)
        super().__init__(*args, **kwargs)
