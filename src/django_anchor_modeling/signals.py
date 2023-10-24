from .models import Knot


def populate_choices(sender, **kwargs):
    for subclass in Knot.__subclasses__():
        manager = subclass.objects
        if hasattr(manager, "ensure_choices_exist"):
            manager.ensure_choices_exist()
