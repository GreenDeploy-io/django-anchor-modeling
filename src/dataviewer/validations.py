from django.apps import apps
from django.core.exceptions import FieldError
from django.db.models import Prefetch

from dataviewer.services import get_model_class


def validate_filter_params(app_name, model_name, filter_params):
    try:
        model_class = apps.get_model(app_name, model_name)
    except LookupError as e:
        raise ValueError(f"Model {model_name} in app {app_name} not found.") from e

    model_fields = [field.name for field in model_class._meta.fields]
    for key in filter_params.keys():
        if key not in model_fields:
            raise FieldError(f"Invalid field: {key} for model {model_name}")


# Example usage:
# try:
#     filter_params = {"name": "John", "invalid_field": "test"}
#     validate_filter_params("my_app", "MyModel", filter_params)
# except (FieldError, ValueError) as e:
#     print(e)


from django.core.exceptions import FieldDoesNotExist, FieldError


def validate_field_model_map(main_model_class, field_model_map):
    """
    returns True if the field_model_map is valid, False, Exception otherwise.
    """
    app_label, main_model_name = main_model_class.split(".")

    try:
        main_model = apps.get_model(app_label, main_model_name)
    except LookupError:
        return False, ValueError(f"Invalid main_model_class: {main_model_class}")

    prefetch_fields = []
    select_related_fields = []
    only_fields = []

    for (
        conceptual_label_for_field,
        actual_definition_of_field,
    ) in field_model_map.items():
        field_type = actual_definition_of_field.get("type", "")
        field_name_in_home_model = actual_definition_of_field["field"]
        name_of_home_model_of_field = actual_definition_of_field["model"]
        order_by = actual_definition_of_field.get("order_by", "")

        if main_model_name == name_of_home_model_of_field:
            home_model = main_model_class
            only_fields.append(field_name_in_home_model)
        else:
            home_model = get_model_class(name_of_home_model_of_field)

        if field_type == "prefetch_related":
            related_name = actual_definition_of_field.get(
                "related_name", conceptual_label_for_field
            )
            prefetch = Prefetch(
                related_name,
                queryset=home_model.objects.only(field_name_in_home_model).order_by(
                    order_by
                ),
            )
            prefetch_fields.append(prefetch)
        elif field_type == "select_related":
            select_related_fields.append(field_name_in_home_model)

    try:
        query = main_model.objects.only(*only_fields)

        if prefetch_fields:
            query = query.prefetch_related(*prefetch_fields)

        if select_related_fields:
            query = query.select_related(*select_related_fields)

        query.first()  # Make a test query
    except (FieldDoesNotExist, FieldError):
        return False

    return True


# ... rest of the code remains the same
