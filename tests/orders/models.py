from django.db import models

from django_anchor_modeling.models import (
    AnchorNoBusinessId,
    AnchorWithBusinessId,
    Knot,
    StaticTie,
    ZeroUpdateStrategyModel,
    static_attribute,
)


class RegularThreeNFModelUsingZeUS(ZeroUpdateStrategyModel):
    name = models.CharField(max_length=100)


class Business(AnchorNoBusinessId):
    pass


class Product(AnchorWithBusinessId):
    pass


StaticAttributeForProductSeller = static_attribute(
    anchor_class=Product,
    value_type=models.ForeignKey(Business, on_delete=models.CASCADE),
    related_name="parent_seller",
)


class ProductSeller(StaticAttributeForProductSeller):
    pass


class BusinessBuyProductTie(StaticTie):
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="buys"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="bought_by"
    )
    composite_key_fields = ("business", "product")


class Order(AnchorWithBusinessId):
    pass


class OrderLineItem(AnchorNoBusinessId):
    pass


StaticAttributeForOrderLineItemOrder = static_attribute(
    anchor_class=OrderLineItem,
    value_type=models.ForeignKey(Order, on_delete=models.CASCADE),
    related_name="line_items",
)


class OrderLineItemOrder(StaticAttributeForOrderLineItemOrder):
    pass


StaticAttributeForOrderLineItemProduct = static_attribute(
    anchor_class=OrderLineItem,
    value_type=models.ForeignKey(Product, on_delete=models.CASCADE),
    related_name="line_items",
)


class OrderLineItemProduct(StaticAttributeForOrderLineItemProduct):
    pass


class OrderType(Knot):
    class TextChoices(models.TextChoices):
        REQUEST = "REQUEST", "Request"
        QUOTATION = "QUOTATION", "Quotation"
        PURCHASE_ORDER = "PURCHASE_ORDER", "Purchase Order"
        ACCEPTANCE_PAPER = "ACCEPTANCE_PAPER", "Acceptance Paper"
        INVOICE = "INVOICE", "Invoice"


class OrderTypeWithoutTextChoices(Knot):
    pass


class OrderTypeTextChoicesNoChoices(Knot):
    class TextChoices(models.TextChoices):
        pass


class ProductIsUnderWhatType(Knot):
    class TextChoices(models.TextChoices):
        ORDERS__ORDER = "ORDERS__ORDER", "Order"
        ORDERS__ORDER_LINE_ITEM = "ORDERS__ORDER_LINE_ITEM", "Order Line Item"


class ProductIsUnderWhat(StaticTie):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="is_under"
    )
    under_what_id = models.PositiveIntegerField()
    under_what_type = models.CharField(
        max_length=100, choices=ProductIsUnderWhatType.TextChoices.choices
    )
    composite_key_fields = ("product", "under_what_id", "under_what_type")
