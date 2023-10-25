import pytest
from django.test import TestCase

from tests.orders.models import Order, OrderLineItem, Product, ProductIsUnderWhat


@pytest.mark.django_db
class TestOrderIsUnderWhatModel(TestCase):
    def test_confirm_composite_key_works(self):
        p1 = Product.objects.create()
        order1 = Order.objects.create()
        lineitem1 = OrderLineItem.objects.create()

        pu1 = ProductIsUnderWhat.objects.create(
            product=p1, under_what_id=order1.id, under_what_type="ORDERS__ORDER"
        )
        pu2 = ProductIsUnderWhat.objects.create(
            product=p1,
            under_what_id=lineitem1.id,
            under_what_type="ORDERS__ORDER_LINE_ITEM",
        )

        assert pu1.pk == f"{p1.pk}.{order1.pk}.ORDERS__ORDER"
        assert pu2.pk == f"{p1.pk}.{lineitem1.pk}.ORDERS__ORDER_LINE_ITEM"
