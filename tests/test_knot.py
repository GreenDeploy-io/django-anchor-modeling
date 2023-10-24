import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from tests.orders.models import (
    OrderType,
    OrderTypeTextChoicesNoChoices,
    OrderTypeWithoutTextChoices,
)


@pytest.mark.django_db
class TestOrderTypeModel(TestCase):
    def test_ensure_choices_exist(self):
        assert OrderType.objects.count() == 0
        assert OrderType.TextChoices.choices == [
            ("REQUEST", "Request"),
            ("QUOTATION", "Quotation"),
            ("PURCHASE_ORDER", "Purchase Order"),
            ("ACCEPTANCE_PAPER", "Acceptance Paper"),
            ("INVOICE", "Invoice"),
        ]
        OrderType.objects.ensure_choices_exist()
        assert OrderType.objects.count() == len(OrderType.TextChoices.choices)

    # @override_settings(
    #     INSTALLED_APPS=settings.INSTALLED_APPS
    #     + ["django_anchor_modeling.apps.EnsureKnotChoicesExistConfig"]
    # )
    # def test_app_config_auto_turn_on_ensure(self):
    #     # don't even need to run ensure_choices_exist
    #     # contrast previous unit test above
    #     assert OrderType.objects.count() == len(OrderType.TextChoices.choices)

    def test_ensure_exception_raised_when_no_textchoices_set(self):
        """
        raise ImproperlyConfigured
        """
        with pytest.raises(ImproperlyConfigured):
            OrderTypeWithoutTextChoices.objects.ensure_choices_exist()

    def test_ensure_exception_raised_when_no_choices_set(self):
        """
        raise ImproperlyConfigured
        """
        with pytest.raises(ImproperlyConfigured):
            OrderTypeTextChoicesNoChoices.objects.ensure_choices_exist()
