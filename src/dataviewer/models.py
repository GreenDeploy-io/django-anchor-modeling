from django.db import models

from django_anchor_modeling.fields import BusinessIdentifierField


class BusinessToDataFieldMapAbstract(models.Model):
    id = BusinessIdentifierField(primary_key=True)
    description = models.TextField()
    map = models.JSONField(default=dict)

    class Meta:
        abstract = True
