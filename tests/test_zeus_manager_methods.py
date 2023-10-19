import pytest
from django.db import IntegrityError, transaction
from django.test import TestCase

from tests.orders.models import Business, Product, ProductSeller


@pytest.mark.django_db
class TestAnchorModel(TestCase):
    def test_delete_and_create_with_pk(self):
        # Create a Business instance
        business1 = Business.objects.create()
        pk = business1.id

        # Delete and recreate with new data
        business2 = Business.objects.delete_and_create(pk=pk)

        # Assert new instance is created and old one is deleted
        assert Business.objects.count() == 1
        # same database rows since Business only has id
        assert business2.id == pk
        # Check they are different Python objects despite being same database rows
        # This proves that there really was deletion that took place
        assert id(business1) != id(business2)

    def test_delete_and_create_without_pk(self):
        with pytest.raises(ValueError) as excinfo:
            Business.objects.delete_and_create(pk=None)
        assert "pk must be provided for regular models." in str(excinfo.value)

    def test_delete_and_create_in_atomic_block(self):
        # Create a Business instance
        business1 = Business.objects.create()
        pk = business1.id

        # Simulate an error in the atomic block
        with pytest.raises(IntegrityError), transaction.atomic():
            Business.objects.delete_and_create(pk=pk)
            raise IntegrityError("Simulated error.")

        # Assert that the original instance still exists
        assert Business.objects.count() == 1
        assert Business.objects.first().id == pk


@pytest.mark.django_db
class TestAttributeModel(TestCase):
    def test_delete_and_create_with_pk(self):
        # Create a Business instance
        business1 = Business.objects.create()
        product1 = Product.objects.create(
            business_identifier="test_delete_and_create_with_pk"
        )
        productseller1 = ProductSeller.objects.create(anchor=product1, value=business1)

        # Delete and recreate with new data
        productseller2 = ProductSeller.objects.delete_and_create(
            anchor=product1, value=business1
        )

        # Assert new instance is created and old one is deleted
        assert ProductSeller.objects.count() == 1
        # Assert same database rows since ProductSeller only has id
        assert productseller2.anchor == product1
        assert productseller2.value == business1
        # Check they are different Python objects despite being same database rows
        # This proves that there really was deletion that took place
        assert id(productseller1) != id(productseller2)

    def test_delete_and_create_without_anchor(self):
        with pytest.raises(ValueError) as excinfo:
            ProductSeller.objects.delete_and_create(anchor=None)
        assert (
            "anchor must be provided for models " "with OneToOneField as primary key."
        ) in str(excinfo.value)

    # def test_delete_and_create_in_atomic_block(self):
    #     # Create a Business instance
    #     business1 = Business.objects.create()
    #     pk = business1.id

    #     # Simulate an error in the atomic block
    #     with pytest.raises(IntegrityError), transaction.atomic():
    #         Business.objects.delete_and_create(pk=pk)
    #         raise IntegrityError("Simulated error.")

    #     # Assert that the original instance still exists
    #     assert Business.objects.count() == 1
    #     assert Business.objects.first().id == pk

    # # Add more tests as necessary
