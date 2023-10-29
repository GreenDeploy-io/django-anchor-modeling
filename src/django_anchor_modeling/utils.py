def get_knot_choice_value(instance: object):
    """
    Given any instance of a model, return the knot choice value
    format is

    APP__CLASS
    """
    app_label = instance._meta.app_label
    class_name = instance.__class__.__name__

    return f"{app_label}__{class_name}"
