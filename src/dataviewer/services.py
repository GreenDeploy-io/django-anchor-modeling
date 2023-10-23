from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Prefetch

from dataviewer.models import BusinessToDataFieldMap
from metadata.services import create_change_with_reason


def get_model_class(model_name):
    cache_key = f"content_type:{model_name}"
    model_class = cache.get(cache_key)
    if not model_class:
        try:
            lower_case_model_name = model_name.lower()
            model_class = ContentType.objects.get(
                model=lower_case_model_name
            ).model_class()
            cache.set(cache_key, model_class)
        except ContentType.DoesNotExist as e:
            raise ContentType.DoesNotExist(
                f"ContentType with model {model_name} does not exist"
            ) from e
    return model_class


def get_biz_to_data_field_map(key):
    cache_key = cache_key_for_biz_to_data_field_map(key)
    field_model_map = cache.get(cache_key)
    if not field_model_map:
        try:
            data_map = BusinessToDataFieldMap.objects.get(id=key)
            field_model_map = data_map.map
            cache_biz_to_data_field_map(key, field_model_map)
        except BusinessToDataFieldMap.DoesNotExist as e:
            raise BusinessToDataFieldMap.DoesNotExist(
                f"BusinessToDataFieldMap with id {key} does not exist"
            ) from e
    return field_model_map


def create_biz_to_data_field_map(key, field_model_map, description=""):
    """
    Example:
        {
            "id": {
                "model": "WorkScope", "field": "id"
            },
            "description": {
                "model": "HistorizedWorkScopeDescription", "type": "prefetch_related",
                "field": "description",
                "order_by": "-from_epoch"
            }
        }
    """
    with transaction.atomic():
        obj, created = BusinessToDataFieldMap.objects.get_or_create(
            id=key, defaults={"map": field_model_map, "description": description}
        )
        if not created:
            raise ValueError(
                f"BusinessToDataFieldMap with id {key} already exists. Use delete_and_create_biz_to_data_field_map instead."
            )
        return obj


def delete_and_create_biz_to_data_field_map(
    key, reason_to_rewrite, field_model_map, description=""
):
    with transaction.atomic():
        # delete from database
        BusinessToDataFieldMap.objects.filter(id=key).delete()
        # create from database
        change = create_change_with_reason(reason_to_rewrite)
        # update the cache
        data_map_model = BusinessToDataFieldMap.objects.create(
            id=key, map=field_model_map, description=description, metadata=change
        )
        field_model_map = data_map_model.map
        cache_biz_to_data_field_map(key, field_model_map)


def cache_key_for_biz_to_data_field_map(key):
    return f"biz_to_data_field_map:{key}"


def cache_biz_to_data_field_map(key, model_dot_map=None):
    if model_dot_map is None:
        model_dot_map = {}
    cache_key = cache_key_for_biz_to_data_field_map(key)
    cache.set(cache_key, model_dot_map)


def get_hydrated_anchor_based_on_data_map(
    anchor_pk, main_model_class, field_model_map, fields
):
    """
    This only works when the map follows BusinessToDataFieldMap.
    Returns the hydrated instance
    """

    queryset = get_hydrated_queryset_based_on_data_map(
        {"id": anchor_pk}, main_model_class, field_model_map, fields
    )
    return queryset.first()


def get_hydrated_queryset_based_on_data_map(
    filter_parameter_and_values, main_model_class, field_model_map, fields=None
):
    """
    This only works when the map follows BusinessToDataFieldMap.
    Returns the hydrated instance
    """

    select_related_fields = []
    prefetch_related_fields = []
    only_fields = []

    if fields is None:
        fields = field_model_map.keys()

    for field in fields:
        if model_info := field_model_map.get(field):
            (only_fields, model_class) = append_only_fields_get_model_class(
                model_info, main_model_class, only_fields
            )

            (
                select_related_fields,
                prefetch_related_fields,
            ) = append_select_or_prefetch_related_fields(
                field,
                model_info,
                model_class,
                select_related_fields,
                prefetch_related_fields,
            )
            queryset = main_model_class.objects.only(*only_fields).filter(
                **filter_parameter_and_values
            )

    if select_related_fields:
        queryset = queryset.select_related(*select_related_fields)

    if prefetch_related_fields:
        queryset = queryset.prefetch_related(*prefetch_related_fields)

    return queryset


def append_only_fields_get_model_class(model_info, main_model_class, only_fields):
    model_name = model_info["model"]
    main_model_name = main_model_class.__name__

    if main_model_name == model_name:
        model_class = main_model_class

        field_name = model_info["field"]
        only_fields.append(field_name)
    else:
        model_class = get_model_class(model_name)

    return only_fields, model_class


def append_select_or_prefetch_related_fields(
    field,
    model_info,
    model_class,
    select_related_fields,
    prefetch_related_fields,
    custom_filters=[],
):
    fetch_type = model_info.get("type")
    field_name = model_info["field"]
    order_by = model_info.get("order_by", "")

    if fetch_type == "select_related":
        select_related_fields.append(field_name)
    elif fetch_type == "prefetch_related":
        related_name = model_info.get("related_name", field)
        prefetch = Prefetch(
            related_name,
            queryset=model_class.objects.only(field_name).order_by(order_by),
        )
        prefetch_related_fields.append(prefetch)

    if model_info.get("is_related_field"):
        lookup_type = model_info.get("related_lookup_type", "filter")
        if custom_filter := model_info.get("custom_filter"):
            custom_filters[custom_filter] = {
                "field": field,
                "lookup_type": lookup_type,
                "model_class": model_class,
                # other needed info
            }

    return select_related_fields, prefetch_related_fields


def transform_hydrated_instance_into_dict(anchor, field_model_map, fields=None):
    result = {}
    if not fields:
        fields = field_model_map.keys()
    for field in fields:
        if model_info := field_model_map.get(field):
            result = append_result_with_right_data_in_field(
                anchor, model_info, field, result
            )
    return result


def transform_many_hydrated_instances(anchors, field_model_map, fields):
    return [
        transform_hydrated_instance_into_dict(anchor, field_model_map, fields)
        for anchor in anchors
    ]


def append_result_with_right_data_in_field(anchor, model_info, field, result):
    field_name = model_info["field"]
    fetch_type = model_info.get("type")

    if fetch_type == "select_related" or fetch_type != "prefetch_related":
        result[field] = getattr(anchor, field_name, None)
    else:
        related_name = model_info.get("related_name", field)
        try:
            if related_object := getattr(anchor, related_name).first():
                result[field] = getattr(related_object, field_name, None)
        except (AttributeError, ObjectDoesNotExist):
            result[field] = None
    return result
