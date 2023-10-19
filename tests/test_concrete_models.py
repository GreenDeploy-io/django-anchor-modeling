import pytest
from django.test import TestCase

from tests.orders.models import (
    Business,
    BusinessBuyProductTie,
    Order,
    OrderLineItem,
    OrderLineItemOrder,
    OrderLineItemProduct,
    Product,
    ProductSeller,
)


@pytest.mark.django_db
class TestBusinessModel(TestCase):
    def test_create_and_retrieve_business(self):
        Business.objects.create()
        assert Business.objects.count() == 1


@pytest.mark.django_db
class TestProductModel(TestCase):
    def test_create_and_retrieve_product(self):
        Product.objects.create()
        assert Product.objects.count() == 1


@pytest.mark.django_db
class TestProductSellerModel(TestCase):
    def test_create_and_retrieve_product_seller(self):
        business = Business.objects.create()
        product = Product.objects.create()
        ProductSeller.objects.create(anchor=product, value=business)
        assert ProductSeller.objects.count() == 1


@pytest.mark.django_db
class TestBusinessBuyProductTieModel(TestCase):
    def test_create_and_retrieve_tie(self):
        business = Business.objects.create()
        product = Product.objects.create()
        BusinessBuyProductTie.objects.create(business=business, product=product)
        assert BusinessBuyProductTie.objects.count() == 1


@pytest.mark.django_db
class TestOrderModel(TestCase):
    def test_create_and_retrieve_order(self):
        Order.objects.create()
        assert Order.objects.count() == 1


@pytest.mark.django_db
class TestOrderLineItemModel(TestCase):
    def test_create_and_retrieve_order_line_item(self):
        OrderLineItem.objects.create()
        assert OrderLineItem.objects.count() == 1


@pytest.mark.django_db
class TestOrderLineItemOrderModel(TestCase):
    def test_create_and_retrieve_order_line_item_order(self):
        order = Order.objects.create()
        line_item = OrderLineItem.objects.create()
        OrderLineItemOrder.objects.create(anchor=line_item, value=order)
        assert OrderLineItemOrder.objects.count() == 1


@pytest.mark.django_db
class TestOrderLineItemProductModel(TestCase):
    def test_create_and_retrieve_order_line_item_product(self):
        product = Product.objects.create()
        line_item = OrderLineItem.objects.create()
        OrderLineItemProduct.objects.create(anchor=line_item, value=product)
        assert OrderLineItemProduct.objects.count() == 1
