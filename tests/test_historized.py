import pytest
from django.apps import apps
from django.db import transaction as db_transaction
from django.test import TestCase

from django_anchor_modeling.models import Transaction
from tests.orders.models.transaction_backed_models import ProductWithNoHistory

HistorizedTProduct = apps.get_model("orders", "HistorizedTProduct")
HistorizedProductName = apps.get_model("orders", "HistorizedProductName")
HistorizedProductDescription = apps.get_model("orders", "HistorizedProductDescription")
HistorizedProductStockQuantity = apps.get_model(
    "orders", "HistorizedProductStockQuantity"
)


@pytest.mark.django_db
class TestHistorizedModel(TestCase):
    """
    total got 10 use cases:
    1. model->create->save
    """

    def test_create_got_transaction_backed_no_history_without_error(self):
        with db_transaction.atomic():
            t = Transaction.objects.create()
            ProductWithNoHistory.objects.create(
                business_identifier="pnh1", transaction=t
            )
