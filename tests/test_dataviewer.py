import pytest
from django.test import TestCase

from dataviewer.services import (
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
