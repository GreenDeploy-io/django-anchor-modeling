from django.db import models

from django_anchor_modeling.models import (
    AnchorNoBusinessId,
    AnchorWithBusinessId,
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
    related_name="products",
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
