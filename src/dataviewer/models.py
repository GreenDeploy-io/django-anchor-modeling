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


class BusinessToQueryMap(CreatedModel):
    id = BusinessIdentifierField(primary_key=True)
    description = models.TextField()
    # in the form of "app_label.model_class_name"
    main_model_class = models.CharField(max_length=255)
    # e.g. the related names of the main model
    # ["quotation", "po_type", "description"]
    # ["parent", "parent__grandparent","parent__grandparent__greatgrandparent"]
    # ancestors of the main_model_class in one to one or many to one way
    # where main_model_class is the one
    select_related = models.JSONField(default=list)
    # descendants of main_model_class where it's one to many or many to many
    # [
    #     {
    #         "prefetch_field": "parent_set",
    #         "model": "myapp.Parent",
    #         "nested_prefetch": [
    #             {
    #                 "prefetch_field": "child_set",
    #                 "model": "myapp.Child",
    #                 "nested_prefetch": [
    #                     {
    #                         "prefetch_field": "grandchild_set",
    #                         "model": "myapp.Grandchild"
    #                     }
    #                 ]
    #             }
    #         ]
    #     }
    # ]
    prefetch_related = models.JSONField(default=list)
    # e.g. the fields in the related models
    # ["id", "quotation__value", "description__value"]
    only = models.JSONField(default=list)
    # field processors
    # where the key is the business level name of the field
    # and the value is a function that takes in the value of the field
    # {
    #     "quotation": {
    #         "field": "quotation",
    #         "condition": "hasattr",
    #         "attribute": "quotation",
    #         "sub_field": "value.display_quotation_number"
    #     },
    #     "another_field": {
    #         "field": "another_field",
    #         "condition": "hasattr",
    #         "attribute": "related_attribute",
    #         "sub_field": "value.some_other_property"
    #     }
    # }
    field_processors = models.JSONField(default=dict)
