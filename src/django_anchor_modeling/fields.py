from django.core.validators import RegexValidator
from django.db import models


class BusinessIdentifierField(models.CharField):
    default_validators = [
        RegexValidator(
            regex=r"^[1-9a-zA-Z_.-]+$",
            message="Business ID must be alphanumeric, dots, hyphens, and underscores only.",
        )
    ]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 255)
        super().__init__(*args, **kwargs)


class OneSentenceDescriptionField(models.TextField):
    """
    This field is used to store the description of a business event.
    """

    default_validators = [
        RegexValidator(
            regex=r"^[A-Za-z][^\.:\?!]*[\.:?!]$",
            message="This field should contain only one sentence.",
        )
    ]
