"""Core way to access configuration"""
from typing import Any, Dict, List

from django.conf import settings
from django.db import models
from django.utils.module_loading import import_string

from django_anchor_modeling import constants


def field() -> "Field":
    """The default configuration for all fields in event models.

    Returns:
        The pghistory `Field` class
    """
    field = getattr(settings, "HISTORIZED_FIELD", Field())
    assert isinstance(field, Field)
    return field


def related_field() -> "RelatedField":
    """The default configuration for related fields in event models.

    Returns:
        The pghistory `RelatedField` class
    """
    related_field = getattr(settings, "HISTORIZED_RELATED_FIELD", RelatedField())
    assert isinstance(related_field, RelatedField)
    return related_field


def foreign_key_field() -> "ForeignKey":
    """The default configuration for foreign keys in event models.

    Returns:
        The pghistory `ForeignKey` class
    """
    foreign_key_field = getattr(settings, "HISTORIZED_FOREIGN_KEY_FIELD", ForeignKey())
    assert isinstance(foreign_key_field, ForeignKey)
    return foreign_key_field


def exclude_field_kwargs() -> Dict["Field", List[str]]:
    """
    Provide a mapping of field classes to a list of keyword args to ignore
    when instantiating the field on the event model.

    For example, a field may not allow `unique` as a keyword argument.
    If so, set `settings.PGHISTORY_EXCLUDE_FIELD_KWARGS = {"field.FieldClass": ["unique"]}`

    Returns:
        The mapping of field classes to kwargs
    """
    exclude_field_kwargs = getattr(settings, "PGHISTORY_EXCLUDE_FIELD_KWARGS", {})
    assert isinstance(exclude_field_kwargs, dict)
    for val in exclude_field_kwargs.values():
        assert isinstance(val, (list, tuple))

    # Import strings
    exclude_field_kwargs = {
        import_string(key) if isinstance(key, str) else key: value
        for key, value in exclude_field_kwargs.items()
    }

    return exclude_field_kwargs


def _get_kwargs(vals):
    return {
        key: val
        for key, val in vals.items()
        if key not in ("self", "kwargs", "__class__") and val is not constants.UNSET
    }


class Field:
    """Configuration for fields.

    The default values for the attributes ensure that
    event models don't have unnecessary uniqueness constraints
    carried over from the tracked model.

    Attributes:
        primary_key (bool, default=False): True if a primary key
        unique (bool, default=False): True if unique
        blank (bool): True if blank
        null (bool): True if null
        db_index (bool): True if indexed
        editable (bool): True if editable
        unique_for_date (bool): True if unique for date
        unique_for_month (bool): True if unique for the month
        unique_for_year (bool): True if unique for the year
    """

    def __init__(
        self,
        *,
        primary_key: bool = constants.UNSET,
        unique: bool = constants.UNSET,
        blank: bool = constants.UNSET,
        null: bool = constants.UNSET,
        db_index: bool = constants.UNSET,
        editable: bool = constants.UNSET,
        unique_for_date: bool = constants.UNSET,
        unique_for_month: bool = constants.UNSET,
        unique_for_year: bool = constants.UNSET,
    ):
        self._kwargs = _get_kwargs(locals())
        self._finalized = False

    @property
    def kwargs(self):
        return {
            key: val
            for key, val in {**self.get_default_kwargs(), **self._kwargs}.items()
            if val is not constants.DEFAULT
        }

    def get_default_kwargs(self):
        return {
            **Field(
                primary_key=False,
                unique=False,
                db_index=False,
                unique_for_date=None,
                unique_for_month=None,
                unique_for_year=None,
            )._kwargs,
            **field()._kwargs,
        }


class RelatedField(Field):
    """Configuration for related fields.

    By default, related names are stripped to avoid
    unnecessary clashes.

    Note that all arguments from `Field` can also be supplied.

    Attributes:
        related_name (str, default="+"): The related_name to use
        related_query_name (str, default="+"): The related_query_name
            to use
    """

    def __init__(
        self,
        *,
        related_name: str = constants.UNSET,
        related_query_name: str = constants.UNSET,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._kwargs.update(_get_kwargs(locals()))

    def get_default_kwargs(self):
        return {
            **super().get_default_kwargs(),
            **RelatedField(related_name="+", related_query_name="+")._kwargs,
            **related_field()._kwargs,
        }


class ForeignKey(RelatedField):
    """Configuration for foreign keys.

    Arguments for `RelatedField` and `Field` can also be supplied.
    Note that db_index is overridden to `True` for all foreign keys

    Attributes:
        on_delete (default=models.DO_NOTHING): Django's on_delete property
        db_constraint (bool, default=False): True to use a datbase constraint
            for the foreign key
    """

    def __init__(
        self,
        *,
        on_delete: Any = constants.UNSET,
        db_constraint: bool = constants.UNSET,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._kwargs.update(_get_kwargs(locals()))

    def get_default_kwargs(self):
        return {
            **super().get_default_kwargs(),
            **ForeignKey(
                on_delete=models.DO_NOTHING, db_index=True, db_constraint=False
            )._kwargs,
            **foreign_key_field()._kwargs,
        }
