from django.db import models

from django_anchor_modeling.models import (
    TransactionBackedAnchorNoBusinessId,
    TransactionBackedAnchorWithBusinessId,
    historize_model,
    transaction_backed_static_attribute,
)


@historize_model
class Grandparent(TransactionBackedAnchorWithBusinessId):
    pass


AbstractGrandparentName = transaction_backed_static_attribute(
    anchor_class=Grandparent,
    value_type=models.CharField(max_length=100),
    related_name="name",
)


@historize_model
class GrandparentName(AbstractGrandparentName):
    pass


@historize_model
class Parent(TransactionBackedAnchorNoBusinessId):
    pass


AbstractParentName = transaction_backed_static_attribute(
    anchor_class=Parent,
    value_type=models.CharField(max_length=100),
    related_name="name",
)


@historize_model
class ParentName(AbstractParentName):
    pass


AbstractParentParent = transaction_backed_static_attribute(
    anchor_class=Parent,
    value_type=models.ForeignKey(
        Grandparent, on_delete=models.DO_NOTHING, db_constraint=False
    ),
)


@historize_model
class ParentParent(AbstractParentParent):
    pass


@historize_model
class Child(TransactionBackedAnchorNoBusinessId):
    pass


AbstractChildName = transaction_backed_static_attribute(
    anchor_class=Child,
    value_type=models.CharField(max_length=100),
    related_name="name",
)


@historize_model
class ChildName(AbstractChildName):
    pass


AbstractChildParent = transaction_backed_static_attribute(
    anchor_class=Child,
    value_type=models.ForeignKey(
        Parent, on_delete=models.DO_NOTHING, db_constraint=False
    ),
)


@historize_model
class ChildParent(AbstractChildParent):
    pass


@historize_model
class Grandchild(TransactionBackedAnchorNoBusinessId):
    pass


AbstractGrandchildName = transaction_backed_static_attribute(
    anchor_class=Grandchild,
    value_type=models.CharField(max_length=100),
    related_name="name",
)


@historize_model
class GrandchildName(AbstractGrandchildName):
    pass


AbstractGrandchildParent = transaction_backed_static_attribute(
    anchor_class=Grandchild,
    value_type=models.ForeignKey(
        Child, on_delete=models.DO_NOTHING, db_constraint=False
    ),
)


@historize_model
class GrandchildParent(AbstractGrandchildParent):
    pass
