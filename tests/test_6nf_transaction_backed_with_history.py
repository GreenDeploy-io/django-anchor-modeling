import pytest
from django.apps import apps
from django.conf import settings
from django.db import transaction
from django.test import TestCase

from django_anchor_modeling.exceptions import SentinelTransactionCannotBeUsedError
from django_anchor_modeling.models import Transaction
from tests.orders.models.transaction_backed_models import (
    ProductDescription,
    ProductName,
    ProductStockQuantity,
    TProduct,
)

HistorizedProductName = apps.get_model("orders", "HistorizedProductName")
HistorizedProductDescription = apps.get_model("orders", "HistorizedProductDescription")


@pytest.mark.django_db
class Test6NFTransactionBackedWithHistoryModel(TestCase):
    """
    total got 10 use cases:
    1. model->create->save
    2. model->edit->save
    3. model->delete
    4. queryset/manager->create
    5. queryset/manager->update
    6. queryset/manager->delete
    7. queryset/manager->get_or_create
    8. queryset/manager->update_or_create
    9. manager->bulk_update
    10. manager->bulk_delete

    exceptions:
    1. ActiveModelClassMustBeTransactionBackedError TE001
    2. CannotReuseExistingTransactionError TE002
    3. MissingTransactionInModelError TE003
    4. SentinelTransactionCannotBeUsedError TE004
    """

    def setUp(self):
        """
        setup a default p0
        """
        with transaction.atomic():
            t0 = Transaction.objects.create()

            p0 = TProduct(business_identifier="p0", transaction=t0)
            p0.save()

            n0 = ProductName()
            n0.anchor = p0
            n0.value = "Product 0"
            n0.transaction = t0
            n0.save()

            ProductDescription.objects.create(
                anchor=p0, value="description for P0", transaction=t0
            )

            ProductStockQuantity.objects.create(anchor=p0, value=100, transaction=t0)

    def test_sentinel_cannot_be_used(self):
        """
        test in all 10 use cases
        """
        # test under 1. model->create->save
        with pytest.raises(SentinelTransactionCannotBeUsedError):
            p1 = TProduct(business_identifier="p1")
            p1.save()

        # 4. queryset/manager->create
        with pytest.raises(SentinelTransactionCannotBeUsedError):
            p1 = TProduct.objects.create(business_identifier="p1")

    def test_model_n_manager_solo_create(self):
        """
        happy path
        1. model->create->save
        4. queryset/manager->create
        """
        with transaction.atomic():
            t1 = Transaction.objects.create()

            p1 = TProduct(business_identifier="p1", transaction=t1)
            p1.save()

            t_p1 = Transaction.objects.last()

            assert t_p1 == t1
            assert t_p1 == p1.transaction
            assert t_p1.id != settings.SENTINEL_NULL_TRANSACTION_ID

            n1 = ProductName()
            n1.anchor = p1
            n1.value = "Product 1"
            n1.transaction = t1
            n1.save()

            t_n1 = Transaction.objects.last()

            assert t_n1 == t1
            assert t_n1 == n1.transaction
            assert t_n1.id != settings.SENTINEL_NULL_TRANSACTION_ID

            pd1 = ProductDescription.objects.create(
                anchor=p1, value="description for P1", transaction=t1
            )

            t_pd1 = Transaction.objects.last()

            assert t_pd1 == t1
            assert t_pd1 == pd1.transaction
            assert t_pd1.id != settings.SENTINEL_NULL_TRANSACTION_ID

            psq1 = ProductStockQuantity.objects.create(
                anchor=p1, value=100, transaction=t1
            )

            t_psq1 = Transaction.objects.last()

            assert t_psq1 == t1
            assert t_psq1 == psq1.transaction
            assert t_psq1.id != settings.SENTINEL_NULL_TRANSACTION_ID

    def test_model_n_manager_solo_update(self):
        """
        happy path
        2. model->edit->save
        5. queryset/manager->update
        """
        with transaction.atomic():
            new_t = Transaction.objects.create()

            historized_product_name_of_p0_queryset = (
                HistorizedProductName.objects.filter(
                    original__anchor__business_identifier="p0"
                )
            )

            previous_most_recent_historized_product_name = (
                historized_product_name_of_p0_queryset.last()
            )

            assert previous_most_recent_historized_product_name.value == "Product 0"
            assert (
                previous_most_recent_historized_product_name.off_txn
                == Transaction.get_sentinel()
            )

            count_historized_records_of_name = (
                historized_product_name_of_p0_queryset.count()
            )

            n0 = ProductName.objects.get(anchor__business_identifier="p0")
            original_transaction_n0 = n0.transaction
            n0.value = "Product 0 - updated"
            n0.transaction = new_t
            n0.save()

            new_count_historized_records_of_name = (
                historized_product_name_of_p0_queryset.count()
            )

            most_recent_historized_product_name = (
                historized_product_name_of_p0_queryset.last()
            )

            previous_most_recent_historized_product_name.refresh_from_db()

            assert previous_most_recent_historized_product_name.off_txn == new_t

            assert n0.transaction != original_transaction_n0
            assert n0.transaction != settings.SENTINEL_NULL_TRANSACTION_ID
            assert n0.value == "Product 0 - updated"
            assert (
                count_historized_records_of_name + 1
            ) == new_count_historized_records_of_name
            assert most_recent_historized_product_name.value == "Product 0 - updated"
            assert most_recent_historized_product_name.on_txn == new_t
            assert (
                most_recent_historized_product_name.off_txn
                == Transaction.get_sentinel()
            )

            # test under 5. queryset/manager->update

            historized_product_desc_of_p0_queryset = (
                HistorizedProductDescription.objects.filter(
                    original__anchor__business_identifier="p0"
                )
            )

            previous_most_recent_historized_product_desc = (
                historized_product_desc_of_p0_queryset.last()
            )

            previous_most_recent_historized_product_desc_pk = (
                previous_most_recent_historized_product_desc.pk
            )

            assert (
                previous_most_recent_historized_product_desc.value
                == "description for P0"
            )
            assert (
                previous_most_recent_historized_product_desc.off_txn
                == Transaction.get_sentinel()
            )

            count_historized_records_of_desc = (
                historized_product_desc_of_p0_queryset.count()
            )

            product_desc_of_p0_queryset = ProductDescription.objects.filter(
                anchor__business_identifier="p0"
            )

            product_desc_of_p0_queryset.update(
                value="description for P0 - updated", transaction=new_t
            )

            n0 = product_desc_of_p0_queryset.first()

            new_count_historized_records_of_desc = (
                historized_product_desc_of_p0_queryset.count()
            )

            most_recent_historized_product_desc = (
                historized_product_desc_of_p0_queryset.last()
            )

            previous_most_recent_historized_product_desc = (
                HistorizedProductDescription.objects.get(
                    pk=previous_most_recent_historized_product_desc_pk
                )
            )

            assert previous_most_recent_historized_product_desc.off_txn == new_t

            assert n0.transaction != original_transaction_n0
            assert n0.transaction != settings.SENTINEL_NULL_TRANSACTION_ID
            assert n0.value == "description for P0 - updated"
            assert (
                count_historized_records_of_desc + 1
            ) == new_count_historized_records_of_desc
            assert (
                most_recent_historized_product_desc.value
                == "description for P0 - updated"
            )
            assert most_recent_historized_product_desc.on_txn == new_t
            assert (
                most_recent_historized_product_desc.off_txn
                == Transaction.get_sentinel()
            )
