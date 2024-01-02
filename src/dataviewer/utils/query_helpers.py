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
    def apply_field_processor_rule(instance, rule):
        """
        Apply a field processing rule to an instance.
        """
        if "full_path_to_single" in rule:
            if "conditions" in rule:
                return QueryHelpers.process_conditions(
                    instance, rule["full_path_to_single"], rule["conditions"]
                )
            return QueryHelpers.get_nested_attr(instance, rule["full_path_to_single"])

        if "path_to_many" in rule:
            if "return_dict" in rule:
                return QueryHelpers.process_many_relations(
                    instance, rule["path_to_many"], rule["return_dict"], "dict"
                )
            if "return_string" in rule:
                return QueryHelpers.process_many_relations(
                    instance, rule["path_to_many"], rule["return_string"], "string"
                )

        return None

    @staticmethod
    def process_conditions(instance, path, conditions):
        """
        Process conditions for a given path.
        """
        for condition, value in conditions.items():
            if condition == "hasattr" and not hasattr(instance, value):
                return None
        return QueryHelpers.get_nested_attr(instance, path)

    @staticmethod
    def process_many_relations(instance, primary_path, sub_fields, output_format):
        """
        Process many related objects and return the specified output format.
        """
        related_objects = getattr(instance, primary_path, None)
        if related_objects is None:
            return []

        if output_format == "dict":
            return [
                {
                    key: QueryHelpers.get_nested_attr(item, path)
                    for key, path in sub_fields.items()
                }
                for item in related_objects.all()
            ]

        if output_format == "string":
            values = [
                str(QueryHelpers.get_nested_attr(item, sub_fields))
                for item in related_objects.all()
            ]
            return ", ".join(filter(None, values))

        return []

    @staticmethod
    def process_instance(instance, field_processor_rules):
        """
        Process an instance with given field processing rules.
        """
        return {
            field: QueryHelpers.apply_field_processor_rule(instance, rule)
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
