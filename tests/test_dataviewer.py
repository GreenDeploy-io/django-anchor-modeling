import pytest
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from dataviewer.models import BusinessToDataFieldMap
from dataviewer.services import (
    get_biz_to_data_field_map,
    get_hydrated_anchor_based_on_data_map,
    get_hydrated_queryset_based_on_data_map,
    transform_hydrated_instance_into_dict,
)
from django_anchor_modeling.models import Transaction
from tests.orders.models.transaction_backed_models import ProductName, TProduct


@pytest.mark.django_db
class TestBusinessToDataFieldMap(TestCase):
    def test_get_hydrated_anchor_based_on_data_map(self):
        t0 = Transaction.objects.create()

        p0 = TProduct(business_identifier="p0", transaction=t0)
        p0.save()

        n0 = ProductName()
        n0.anchor = p0
        n0.value = "Product 0"
        n0.transaction = t0
        n0.save()
        field_model_map = {
            "id": {"field": "id", "model": "TProduct"},
            "name": {
                "field": "value",
                "model": "ProductName",
                "type": "select_related",
                "related_field": "name",
            },
            # "name": {
            #     "field": "value",
            #     "model": "ProductName",
            # },
        }

        with CaptureQueriesContext(connection) as queries:
            hydrated_p1 = get_hydrated_anchor_based_on_data_map(
                p0.pk, TProduct, field_model_map
            )
            queryset = get_hydrated_queryset_based_on_data_map(
                {"id": p0.pk}, TProduct, field_model_map
            )
            hydrated_p2 = queryset.first()

            assert hydrated_p1 == hydrated_p2

            hydrated_dict = transform_hydrated_instance_into_dict(
                hydrated_p1, field_model_map
            )
            # sourcery skip: no-loop-in-tests
            for query in queries.captured_queries:
                print(query["sql"])
            assert hydrated_dict == {"id": p0.pk, "name": "Product 0"}
            # 1 query to use contenttype to get model class for productname
            # 1 query to get productname and product in get_hydrated_anchor_based_on_data_map
            # 1 query to get productname and product in get_hydrated_queryset_based_on_data_map
            assert len(queries) == 3

    def test_get_biz_to_data_field_map(self):
        field_model_map = {"id": {"field": "id", "model": "TProduct"}}
        b2dfm = BusinessToDataFieldMap.objects.create(
            description="", id="Product.GENERIC", map=field_model_map
        )
        assert b2dfm.map == field_model_map
        cached_map = get_biz_to_data_field_map("Product.GENERIC")
        assert cached_map == field_model_map
