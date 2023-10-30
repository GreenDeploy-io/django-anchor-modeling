from django.db import models

from django_anchor_modeling.models import (
    TransactionBackedAnchorWithBusinessId,
    historize_model,
    transaction_backed_static_attribute,
)


@historize_model
class TProduct(TransactionBackedAnchorWithBusinessId):
    pass


AbstractProductName = transaction_backed_static_attribute(
    anchor_class=TProduct,
    value_type=models.CharField(max_length=100),
    related_name="name",
)


@historize_model
class ProductName(AbstractProductName):
    pass


AbstractProductDescription = transaction_backed_static_attribute(
    anchor_class=TProduct,
    value_type=models.TextField(),
    related_name="description",
)


@historize_model
class ProductDescription(AbstractProductDescription):
    pass


AbstractProductStockQuantity = transaction_backed_static_attribute(
    anchor_class=TProduct,
    value_type=models.IntegerField(max_length=8),
    related_name="stock_quantity",
)


@historize_model
class ProductStockQuantity(AbstractProductStockQuantity):
    pass


class ProductWithNoHistory(TransactionBackedAnchorWithBusinessId):
    pass
