import pytest
from django.test import TestCase

from dataviewer.models import BusinessToDataFieldMap
from dataviewer.services import (
    get_biz_to_data_field_map,
    get_hydrated_anchor_based_on_data_map,
    get_hydrated_queryset_based_on_data_map,
)
from tests.orders.models import Product


@pytest.mark.django_db
class TestBusinessToDataFieldMap(TestCase):
    def test_get_hydrated_anchor_based_on_data_map(self):
        p1 = Product.objects.create()
        field_model_map = {
            "id": {"field": "id", "model": "Product"},
        }
        hydrated_p1 = get_hydrated_anchor_based_on_data_map(
            p1.pk, Product, field_model_map
        )
        queryset = get_hydrated_queryset_based_on_data_map(
            {"id": p1.pk}, Product, field_model_map
        )
        hydrated_p2 = queryset.first()

        assert hydrated_p1 == hydrated_p2

    def test_get_biz_to_data_field_map(self):
        field_model_map = {"id": {"field": "id", "model": "Product"}}
        b2dfm = BusinessToDataFieldMap.objects.create(
            description="", id="Product.GENERIC", map=field_model_map
        )
        assert b2dfm.map == field_model_map
        cached_map = get_biz_to_data_field_map("Product.GENERIC")
        assert cached_map == field_model_map
