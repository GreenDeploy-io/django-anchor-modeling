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

    # in the form of "app_label.model_class_name"
    main_model_class = models.CharField(max_length=255, null=True)
