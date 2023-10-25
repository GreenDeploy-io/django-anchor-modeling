import pytest
from django.test import TestCase

from tests.orders.models import Business, Product, ProductSeller


@pytest.mark.django_db
class TestStaticAttributeModel(TestCase):
    def test_get_by_related_parent(self):
        # Create a Business instance
        business1 = Business.objects.create()
        product1 = Product.objects.create(business_identifier="p1")
        ProductSeller.objects.create(anchor=product1, value=business1)
        product2 = Product.objects.create(business_identifier="p2")
        ProductSeller.objects.create(anchor=product2, value=business1)

        # 1. {"parent_work_scope__value": work_scope}
        filter_args_and_values = Product.filters.get_by_parent_seller(business1)
        assert filter_args_and_values == {"parent_seller__value": business1}

        # 2. {"parent_work_scope__value_id": work_scope}
        filter_args_and_values = Product.filters.get_by_parent_seller(business1.id)
        assert filter_args_and_values == {"parent_seller__value_id": business1.id}
