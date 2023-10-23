from django.db import models

from django_anchor_modeling.fields import BusinessIdentifierField
from django_anchor_modeling.models import CreatedModel


class BusinessToDataFieldMapAbstract(models.Model):
    id = BusinessIdentifierField(primary_key=True)
    description = models.TextField()
    map = models.JSONField(default=dict)

    class Meta:
        abstract = True


class BusinessToDataFieldMap(CreatedModel):
    id = BusinessIdentifierField(primary_key=True)
    description = models.TextField()
    map = models.JSONField(default=dict)
    metadata = models.ForeignKey(
        "metadata.DataChange", on_delete=models.SET_NULL, null=True
    )
