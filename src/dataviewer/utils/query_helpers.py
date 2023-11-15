# query_helpers.py


class QueryHelpers:
    @staticmethod
    def get_nested_attr(instance, attr_path):
        """
        Recursively get a nested attribute using dot notation.
        """
        current_attr = instance
        for attr in attr_path.split("."):
            if current_attr is not None:
                current_attr = getattr(current_attr, attr, None)
            else:
                return None
        return current_attr

    @staticmethod
    def process_nested_dict(instance, attribute_dict):
        """
        Process a dictionary of nested attributes.
        """
        return {
            key: QueryHelpers.get_nested_attr(instance, attr_path)
            for key, attr_path in attribute_dict.items()
        }

    @staticmethod
    def apply_field_processor_rule(instance, field, rule):
        """
        Apply a field processing rule to an instance.
        """
        import ipdb

        ipdb.set_trace()
        # Extract the actual field to process from the rule
        actual_field = rule.get("field", field)

        # Handle processing for nested attributes (like 'parents')
        if "attributes" in rule:
            # Check if a condition is specified and met
            if rule.get("condition") == "hasattr" and not hasattr(
                instance, actual_field
            ):
                return []

            related_objects = getattr(instance, actual_field, None)

            if related_objects is None:
                return []

            output_format = rule.get("format", "dict")

            return QueryHelpers.process_nested_relations(
                related_objects, rule["attributes"], output_format=output_format
            )

        # Check for special condition (like 'hasattr')
        elif rule.get("condition") == "hasattr":
            attr = getattr(instance, rule.get("attribute"), None)
            return (
                getattr(attr, rule.get("sub_field"), None) if attr is not None else None
            )

        # Handle direct attribute
        else:
            return QueryHelpers.get_nested_attr(
                instance, rule.get("attribute", actual_field)
            )

    @staticmethod
    def process_instance(instance, field_processor_rules):
        return {
            field: QueryHelpers.apply_field_processor_rule(instance, field, rule)
            for field, rule in field_processor_rules.items()
        }

    @staticmethod
    def process_nested_relations(instance, nested_attributes, output_format="dict"):
        """
        Process nested relations and return a list of dictionaries or a comma-delimited string.
        """
        processed_list = []
        for item in instance.all():  # Iterate over the queryset
            if output_format == "dict":
                processed_item = {
                    attr: QueryHelpers.get_nested_attr(item, path)
                    for attr, path in nested_attributes.items()
                }
                processed_list.append(processed_item)
            elif output_format == "string":
                values = [
                    str(QueryHelpers.get_nested_attr(item, path))
                    for path in nested_attributes.values()
                ]
                return ", ".join(values)
        return processed_list if output_format == "dict" else ", ".join(processed_list)

    @staticmethod
    def see_results(whatever):
        import ipdb

        ipdb.set_trace()

    @staticmethod
    def apply_nested_prefetch_rules(queryset, prefetch_rules):
        from django.db.models import Prefetch

        for rule in prefetch_rules:
            model_class = QueryHelpers._get_model_for_queryset(rule["model"])

            nested_queryset = None
            if "nested_prefetch" in rule:
                fields_to_fetch = rule.get(
                    "only_fields", []
                )  # Get only_fields or default to []
                nested_queryset = QueryHelpers.apply_nested_prefetch_rules(
                    model_class.objects.only(*fields_to_fetch),
                    rule["nested_prefetch"],
                )

            if rule.get("is_one_to_one"):
                # Use select_related for OneToOne relationships
                queryset = queryset.select_related(rule["prefetch_field"])
            else:
                # Use prefetch_related for other relationships
                queryset = queryset.prefetch_related(
                    Prefetch(rule["prefetch_field"], queryset=nested_queryset)
                    if nested_queryset
                    else rule["prefetch_field"]
                )

        return queryset

    @staticmethod
    def _get_model_for_queryset(main_model_class):
        """
        Get the model class based on its app label and class name.

        :param model_path: The string path of the model (e.g., 'myapp.ModelName').
        :return: The Django model class.
        """
        from django.apps import apps

        try:
            # Split the string into app_label and model_name
            app_label, model_name = main_model_class.split(".")

            # Dynamically get the model class
            return apps.get_model(app_label, model_name)
        except LookupError as e:
            # Handle the case where the model_path is not found
            raise ValueError(f"Model '{main_model_class}' not found.") from e
