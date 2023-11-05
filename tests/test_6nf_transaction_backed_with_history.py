import pytest
from django.apps import apps
from django.db import transaction
from django.test import TestCase

from django_anchor_modeling import constants
from django_anchor_modeling.exceptions import SentinelTransactionCannotBeUsedError
from django_anchor_modeling.models import Transaction
from tests.orders.models.transaction_backed_models import (
    ProductDescription,
    ProductHasSeller,
    ProductName,
    ProductStockQuantity,
    TBusiness,
    TProduct,
)

HistorizedTProduct = apps.get_model("orders", "HistorizedTProduct")
HistorizedProductName = apps.get_model("orders", "HistorizedProductName")
HistorizedProductDescription = apps.get_model("orders", "HistorizedProductDescription")
HistorizedProductStockQuantity = apps.get_model(
    "orders", "HistorizedProductStockQuantity"
)


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
    11. attribute->create_or_update_if_different

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
        # sourcery skip: extract-duplicate-method, inline-immediately-returned-variable
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
            assert t_p1.id != constants.SENTINEL_NULL_TRANSACTION_ID

            n1 = ProductName()
            n1.anchor = p1
            n1.value = "Product 1"
            n1.transaction = t1
            n1.save()

            t_n1 = Transaction.objects.last()

            assert t_n1 == t1
            assert t_n1 == n1.transaction
            assert t_n1.id != constants.SENTINEL_NULL_TRANSACTION_ID

            pd1 = ProductDescription.objects.create(
                anchor=p1, value="description for P1", transaction=t1
            )

            t_pd1 = Transaction.objects.last()

            assert t_pd1 == t1
            assert t_pd1 == pd1.transaction
            assert t_pd1.id != constants.SENTINEL_NULL_TRANSACTION_ID

            psq1 = ProductStockQuantity.objects.create(
                anchor=p1, value=100, transaction=t1
            )

            t_psq1 = Transaction.objects.last()

            assert t_psq1 == t1
            assert t_psq1 == psq1.transaction
            assert t_psq1.id != constants.SENTINEL_NULL_TRANSACTION_ID

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
            n0.save(transaction=new_t)

            new_count_historized_records_of_name = (
                historized_product_name_of_p0_queryset.count()
            )

            most_recent_historized_product_name = (
                historized_product_name_of_p0_queryset.last()
            )

            previous_most_recent_historized_product_name.refresh_from_db()

            assert previous_most_recent_historized_product_name.off_txn == new_t

            assert (
                most_recent_historized_product_name.pk
                != previous_most_recent_historized_product_name.pk
            )
            assert n0.transaction != original_transaction_n0
            assert n0.transaction != constants.SENTINEL_NULL_TRANSACTION_ID
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

            assert (
                most_recent_historized_product_desc.pk
                != previous_most_recent_historized_product_desc.pk
            )
            assert n0.transaction != original_transaction_n0
            assert n0.transaction != constants.SENTINEL_NULL_TRANSACTION_ID
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

    def test_model_n_manager_solo_delete(self):  # noqa: PLR0915
        # sourcery skip: extract-duplicate-method, inline-immediately-returned-variable
        """
        happy path
        3. model->delete
        6. queryset/manager->delete
        """
        with transaction.atomic():
            new_t = Transaction.objects.create()

            p0 = TProduct.objects.get(business_identifier="p0")

            historized_product_name_of_p0_queryset = (
                HistorizedProductName.objects.filter(original_id=p0.pk)
            )

            previous_most_recent_historized_product_name = (
                historized_product_name_of_p0_queryset.last()
            )

            assert (
                previous_most_recent_historized_product_name.off_txn
                == Transaction.get_sentinel()
            )

            count_historized_records_of_name = (
                historized_product_name_of_p0_queryset.count()
            )

            n0 = ProductName.objects.get(anchor__business_identifier="p0")
            original_transaction_n0 = n0.transaction
            n0.delete(transaction=new_t)

            new_count_historized_records_of_name = (
                historized_product_name_of_p0_queryset.count()
            )

            most_recent_historized_product_name = (
                historized_product_name_of_p0_queryset.last()
            )

            previous_most_recent_historized_product_name.refresh_from_db()

            assert previous_most_recent_historized_product_name.off_txn == new_t

            assert (
                most_recent_historized_product_name.pk
                == previous_most_recent_historized_product_name.pk
            )
            assert new_t != original_transaction_n0
            assert (
                ProductName.objects.filter(anchor__business_identifier="p0").count()
                == 0
            )

            assert (
                count_historized_records_of_name == new_count_historized_records_of_name
            )
            assert most_recent_historized_product_name.on_txn != new_t
            assert most_recent_historized_product_name.off_txn == new_t

            # test under 5. queryset/manager->delete
            # and also make sure anchor delete will delete
            # all the associated attributes

            # left with
            # Product
            #  - Desc
            #  - StockQuantity

            # this is Product
            historized_product_of_p0_queryset = HistorizedTProduct.objects.filter(
                original_id=p0.pk
            )

            previous_most_recent_historized_product = (
                historized_product_of_p0_queryset.last()
            )

            previous_most_recent_historized_product_pk = (
                previous_most_recent_historized_product.pk
            )
            count_historized_records_of_product = (
                historized_product_of_p0_queryset.count()
            )
            assert (
                previous_most_recent_historized_product.off_txn
                == Transaction.get_sentinel()
            )

            # end this is Product

            # this is ProductDesc
            historized_product_desc_of_p0_queryset = (
                HistorizedProductDescription.objects.filter(original_id=p0.pk)
            )

            previous_most_recent_historized_product_desc = (
                historized_product_desc_of_p0_queryset.last()
            )

            previous_most_recent_historized_product_desc_pk = (
                previous_most_recent_historized_product_desc.pk
            )

            count_historized_records_of_product_desc = (
                historized_product_desc_of_p0_queryset.count()
            )
            assert (
                previous_most_recent_historized_product_desc.off_txn
                == Transaction.get_sentinel()
            )

            # end this is ProductDesc

            # this is ProductStockQuantity
            historized_product_qty_of_p0_queryset = (
                HistorizedProductStockQuantity.objects.filter(original_id=p0.pk)
            )

            previous_most_recent_historized_product_qty = (
                historized_product_qty_of_p0_queryset.last()
            )

            previous_most_recent_historized_product_qty_pk = (
                previous_most_recent_historized_product_qty.pk
            )

            count_historized_records_of_product_qty = (
                historized_product_qty_of_p0_queryset.count()
            )

            assert (
                previous_most_recent_historized_product_qty.off_txn
                == Transaction.get_sentinel()
            )

            # end this is ProductStockQuantity

            # now we delete the Product

            TProduct.objects.filter(business_identifier="p0").delete(transaction=new_t)

            # end of Txn

            # this is TProduct
            new_count_historized_records_of_product = (
                historized_product_of_p0_queryset.count()
            )

            most_recent_historized_product = historized_product_of_p0_queryset.last()

            previous_most_recent_historized_product = HistorizedTProduct.objects.get(
                pk=previous_most_recent_historized_product_pk
            )

            assert previous_most_recent_historized_product.off_txn == new_t

            assert (
                most_recent_historized_product.pk
                == previous_most_recent_historized_product.pk
            )
            assert (
                new_count_historized_records_of_product
                == count_historized_records_of_product
            )

            assert TProduct.objects.filter(business_identifier="p0").exists() is False
            # end this is TProduct

            # this is ProductDescription
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

            assert (
                most_recent_historized_product_desc.pk
                == previous_most_recent_historized_product_desc.pk
            )
            assert (
                new_count_historized_records_of_desc
                == count_historized_records_of_product_desc
            )
            assert (
                ProductDescription.objects.filter(
                    anchor__business_identifier="p0"
                ).exists()
                is False
            )
            # end this is ProductDesc

            # this is ProductStockQuantity
            new_count_historized_records_of_qty = (
                historized_product_qty_of_p0_queryset.count()
            )

            most_recent_historized_product_qty = (
                historized_product_qty_of_p0_queryset.last()
            )

            previous_most_recent_historized_product_qty = (
                HistorizedProductStockQuantity.objects.get(
                    pk=previous_most_recent_historized_product_qty_pk
                )
            )

            assert previous_most_recent_historized_product_qty.off_txn == new_t

            assert (
                most_recent_historized_product_qty.pk
                == previous_most_recent_historized_product_qty.pk
            )
            assert (
                new_count_historized_records_of_qty
                == count_historized_records_of_product_qty
            )
            assert (
                ProductStockQuantity.objects.filter(
                    anchor__business_identifier="p0"
                ).exists()
                is False
            )
            # end this is ProductStockQuantity

    def test_create_or_update_if_different(self):
        t1 = Transaction.objects.create()

        brand_new = TProduct.objects.create(
            business_identifier="brand new product", transaction=t1
        )

        # regular value

        ## regular value -- create
        new_name = "brand new product"
        name, created, different = ProductName.objects.create_or_update_if_different(
            anchor=brand_new, new_value=new_name, txn_instance=t1
        )
        assert created is True
        assert name.value == new_name
        assert different is None
        assert name.transaction == t1

        ## regular value -- update if different
        t2 = Transaction.objects.create()
        new_name = "newer brand new product"

        name, created, different = ProductName.objects.create_or_update_if_different(
            anchor=brand_new, new_value=new_name, txn_instance=t2
        )
        assert created is False
        assert name.value == new_name
        assert different is True
        assert name.transaction == t2

        ## regular value -- don't update since same
        t3 = Transaction.objects.create()

        name, created, different = ProductName.objects.create_or_update_if_different(
            anchor=brand_new, new_value=new_name, txn_instance=t3
        )
        assert created is False
        assert name.value == new_name
        assert different is False
        assert name.transaction == t2

        # fk

        t4 = Transaction.objects.create()

        ## fk -- create
        biz = TBusiness(business_identifier="biz", transaction=t4)
        biz.save(transaction=t4)

        (
            seller,
            created,
            different,
        ) = ProductHasSeller.objects.create_or_update_if_different(
            anchor=brand_new, new_value=biz, txn_instance=t4
        )
        assert created is True
        assert seller.value == biz
        assert different is None
        assert seller.transaction == t4

        ## fk -- update if different
        t5 = Transaction.objects.create()
        new_biz = TBusiness(business_identifier="new_biz", transaction=t5)
        new_biz.save(transaction=t5)

        (
            seller,
            created,
            different,
        ) = ProductHasSeller.objects.create_or_update_if_different(
            anchor=brand_new, new_value=new_biz, txn_instance=t5
        )
        assert created is False
        assert seller.value == new_biz
        assert different is True
        assert seller.transaction == t5

        ## fk -- don't update since same
        t6 = Transaction.objects.create()

        (
            seller,
            created,
            different,
        ) = ProductHasSeller.objects.create_or_update_if_different(
            anchor=brand_new, new_value=new_biz, txn_instance=t6
        )
        assert created is False
        assert seller.value == new_biz
        assert different is False
        assert seller.transaction == t5
