from types import new_class

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.validators import RegexValidator
from django.db import models
from django.db.utils import IntegrityError

from .fields import BusinessIdentifierField
from .managers import (
    CompositeKeyManager,
    FromModelManager,
    HistorizedAttributeManager,
    PrepareFilterManager,
    ZeroUpdateStrategyManager,
    add_method_to_manager,
    create_prepare_filter_manager,
)


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides selfupdating
    ``created`` and ``modified`` fields.
    """

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PersonStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    ``created_by`` and ``modified_by`` fields.
    """

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        editable=False,
        related_name="created_%(app_label)s_%(class)s",
        related_query_name="query_created_%(app_label)s_%(class)ss",
        on_delete=models.CASCADE,
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        editable=False,
        related_name="last_edited_%(app_label)s_%(class)s",
        related_query_name="query_last_edited_%(app_label)s_%(class)ss",
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True

    @property
    def activity_actor_attr(self):
        return self.modified_by or self.created_by


class CreatedModel(models.Model):
    """
    An abstract base class model that provides selfupdating
    ``created`` field ONLY
    """

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class UndeletableModel(models.Model):
    """
    An abstract base class model that disallows delete
    probably needs another that disallows delete depending on conditions
    """

    def delete(self):
        pass

    class Meta:
        abstract = True


class ZeroUpdateStrategyModel(models.Model):
    """
    An abstract base class model that provides a zero update strategy for saving instances.

    Attributes:
        objects (ZeroUpdateStrategyManager): The manager instance for the model.

    Meta:
        abstract (bool): Specifies that this model is an abstract base class.

    Methods:
        save: Overrides the save method to apply the zero update strategy.

    Args:
        self: The model instance.
        *args: Additional positional arguments.
        **kwargs: Additional keyword arguments.
    """

    objects = ZeroUpdateStrategyManager()
    filters = PrepareFilterManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
        Saves the model instance to the database.

        If 'avoid_recursion' attribute is present, it calls the superclass's save method
        and removes the attribute.

        If the instance already has a primary key and the 'created_via_manager'
        attribute is not present, it deletes the existing instance and creates a new one
        with the same field values.

        Otherwise, it calls the superclass's save method.

        Args:
            *args: Additional positional arguments to pass to the superclass's save method.
            **kwargs: Additional keyword arguments to pass to the superclass's save method.

        Returns:
            None
        """
        if hasattr(self, "avoid_recursion") and self.avoid_recursion:
            super().save(*args, **kwargs)
            delattr(self, "avoid_recursion")
        elif self.pk is not None and (
            not hasattr(self, "created_via_manager") or not self.created_via_manager
        ):
            field_names = [field.name for field in self._meta.get_fields()]
            filtered_dict = {k: v for k, v in self.__dict__.items() if k in field_names}
            type(self).objects.delete_and_create(pk=self.pk, **filtered_dict)
        else:
            super().save(*args, **kwargs)


class CharFieldForCompositeKey(models.Model):
    """
    An abstract base class for a CharField used as a composite key in Django models.

    Attributes:
        id (CharField): The primary key field.

    Meta:
        abstract (bool): Indicates that this model is abstract and cannot be instantiated.
        composite_key_fields (tuple): The fields that make up the composite key.

    Example:
        ```python
        class MyModel(CharFieldForCompositeKey):

            field1 = models.CharField(max_length=255)
            field2 = models.CharField(max_length=255)

            composite_key_fields = ('field1', 'field2')
        ```
    """

    composite_key_fields = ()
    id = models.CharField(
        max_length=255,
        primary_key=True,
        validators=[
            RegexValidator(
                regex=r"^[0-9a-zA-Z_.-]+$",
                message="ID must be alphanumeric, underscores, hyphens, and dots.",
            )
        ],
    )

    class Meta:
        abstract = True


class FromModel(ZeroUpdateStrategyModel):
    """
    An abstract base class model that provides fields for storing datetime information.

    It sets datetime fields based on Jon Skeet's advice on datetime storage
    at https://codeblog.jonskeet
    .uk/2019/03/27/storing-utc-is-not-a-silver-bullet/
    while conforming to anchor modeling's use of from_date.

    Works for anchor modeling's `attribute`, `tie`, and `knotted` models.

    This FromModel alone will not make a model "historized".

    Please see the documentation for `HistorizedAttribute` for more information.

    Attributes:
        from_epoch (IntegerField): An IntegerField that stores the epoch time.
        from_utc_start (DateTimeField): A DateTimeField that stores the UTC start time.
        from_local_start (DateTimeField): A DateTimeField that stores local start time.
        from_timezone_id (CharField): A CharField that stores the timezone ID.
        from_timezone_rules (CharField): A CharField that stores the timezone rules.

        disallowed_exception (Exception): Exception raised when create record via save.

    Example:
        from_epoch = 1625904000
        from_utc_start = "2021-07-10T08:00:00Z"
        from_local_start = "2021-07-10T09:00:00"
        from_timezone_id = "Europe/Amsterdam"
        from_timezone_rules = "2020c"


    Meta:
        abstract (bool): Specifies that this model is an abstract base class.

    Usage:
        ```
        class MyConcreteModel(FromModel, OtherAbstractModel):
            objects = OtherModelManager()
            from_objects = FromModelManager() # strongly recommended

            class Meta:
                abstract = False
        ```

        Do NOT use `save` directly for creating new records.
        You will trigger `FromCannotCreateRecordViaSave` exception.

        Using `save` to update is fine.

        Use any of the following instead:
         - `MyConcreteModel.from_objects.create`
         - `MyConcreteModel.from_objects.create_with_timezone`
         - `MyConcreteModel.from_objects.timezone_create`
         - `MyConcreteModel.from_objects.user_create`
    """

    from_epoch = models.IntegerField(editable=False)
    from_utc_start = models.DateTimeField(editable=False)
    from_local_start = models.DateTimeField(editable=False)
    from_timezone_id = models.CharField(max_length=50, editable=False)
    from_timezone_rules = models.CharField(max_length=20, editable=False)

    from_objects = FromModelManager()  # strongly recommended

    class Meta:
        abstract = True


def historized_attribute(anchor_class, value_type, related_name="%(class)s_related"):
    """
    A factory function that generates an abstract base class model for historized attributes.

    Args:
        anchor_class: The class to which the historized attribute is anchored.
        value_type: The type of the historized attribute value.
        related_name (str, optional): The related name for the anchor field. Defaults to "%(class)s_related".

    Returns:
        HistorizedAttribute: An abstract base class model for historized attributes.

    """

    class HistorizedAttribute(CharFieldForCompositeKey, FromModel):
        """
        An abstract base class model for historized attributes.

        Attributes:
            id (CharField): A CharField that represents the ID of the historized attribute.
            anchor (ForeignKey): A ForeignKey to the anchor class.
            value (value_type): A field that represents the value of the historized attribute.
            objects (HistorizedAttributeManager): The manager instance for the model.

        Meta:
            abstract (bool): Specifies that this model is an abstract base class.

        """

        anchor = models.ForeignKey(
            anchor_class, on_delete=models.CASCADE, related_name=related_name
        )
        value = value_type

        objects = HistorizedAttributeManager()

        class Meta:
            abstract = True

    return HistorizedAttribute


def static_attribute(anchor_class, value_type, related_name="%(class)s_related"):
    """
    A factory function that generates a model for static attributes.

    Args:
        anchor_class: The class to which the static attribute is anchored.
        value_type: The type of the static attribute value.
        related_name (str, optional): The related name for the anchor field. Defaults to "%(class)s_related".

    Returns:
        StaticAttribute: A model for static attributes.

    """

    class StaticAttribute(ZeroUpdateStrategyModel):
        """
        A model for static attributes.

        This also works for ForeignKey as attributes

        Attributes:
            anchor (OneToOneField): A OneToOneField to the anchor class as primary key.
            value (value_type): A field representing the value of the static attribute.
            objects (ZeroUpdateStrategyManager): The manager instance for the model.

        Meta:
            abstract (bool): Specifies that this model is an abstract base class.

        """

        anchor = models.OneToOneField(
            anchor_class,
            on_delete=models.CASCADE,
            related_name=related_name,
            primary_key=True,
        )
        value = value_type

        objects = ZeroUpdateStrategyManager()

        class Meta:
            abstract = True

    # This block is inside static_attribute but outside StaticAttribute
    if isinstance(value_type, models.ForeignKey):
        # Dynamically set the manager method on the anchor class
        # so can more easily get_by_parent_related_name
        if hasattr(anchor_class, "filters"):
            manager_instance = getattr(anchor_class, "filters")
            add_method_to_manager(manager_instance.__class__, related_name)
        else:
            # create_custom_manager should be modified to accommodate this logic
            custom_manager = create_prepare_filter_manager(related_name)
            anchor_class.add_to_class("filters", custom_manager)

    return StaticAttribute


def is_a(super_class_anchor, business_identifier_on=True):
    """
    A factory function that generates a subtype model under an anchor
    which is a super class

    Args:
        super_class_anchor: The class to which this model is subtype to.
        business_identifier_on(boolean): If true, add business_identifier

    Returns:
        IsA: A model for subtype.

    """
    # Retrieve original manager from super_class_anchor
    original_manager = getattr(super_class_anchor, "objects", models.Manager)

    # Dynamically create a composite manager that combines the two managers
    CompositeManager = new_class(
        "CompositeManager", (original_manager.__class__, ZeroUpdateStrategyManager)
    )

    class IsA(ZeroUpdateStrategyModel):
        """
        A model for subtype. Which is like a StaticTie

        Attributes:
            super_class (OneToOneField): A OneToOneField to the anchor class as primary key.
            business_identifier (CharField): A field representing the record
            objects (ZeroUpdateStrategyManager): The manager instance for the model.

        Meta:
            abstract (bool): Specifies that this model is an abstract base class.

        """

        super_class = models.OneToOneField(
            super_class_anchor,
            on_delete=models.CASCADE,
            related_name="%(class)s",
            primary_key=True,
        )
        if business_identifier_on:
            business_identifier = BusinessIdentifierField(unique=True)

        objects = CompositeManager()

        class Meta:
            abstract = True

    return IsA


class StaticTie(CharFieldForCompositeKey, ZeroUpdateStrategyModel):
    objects = CompositeKeyManager()

    class Meta:
        abstract = True


class HistorizedTie(CharFieldForCompositeKey, FromModel):
    """
    An abstract base class for a historized tie model that uses a composite key
    and supports historization.

    Attributes:
        objects (CompositeKeyManager): The manager for the model.

    Meta:
        abstract (bool): Indicates that this model is abstract
            and cannot be instantiated.

    Example:
        ```python
        class MyHistorizedTie(HistorizedTie):

            field1 = models.CharField(max_length=255)
            field2 = models.CharField(max_length=255)

            composite_key_fields = ('field1', 'field2', 'from_epoch')
        ```
    """

    objects = CompositeKeyManager()

    class Meta:
        abstract = True


class AnchorWithBusinessId(ZeroUpdateStrategyModel):
    business_identifier = BusinessIdentifierField(unique=True)

    class Meta:
        abstract = True


class AnchorNoBusinessId(ZeroUpdateStrategyModel):
    class Meta:
        abstract = True


class KnotManager(models.Manager):
    def ensure_valid_keys_exist(self):
        model_cls = self.model
        model_name = model_cls.__name__
        valid_keys = getattr(model_cls, "VALID_KEYS", None)

        if not valid_keys:
            raise ImproperlyConfigured(
                f"'VALID_KEYS' must be defined and non-empty for {model_name}"
            )

        for key in valid_keys:
            try:
                _, created = model_cls.objects.get_or_create(pk=key)
                if created:
                    print(f"Created {model_name} with pk {key}")
                else:
                    print(f"{model_name} with pk {key} already exists")
            except IntegrityError:
                print(f"Could not create {model_name} with pk {key}. IntegrityError.")
                # re-raise the exception
                raise


class Knot(UndeletableModel):
    id = models.CharField(max_length=255, primary_key=True)
    is_active = models.BooleanField(default=True)

    objects = KnotManager()

    class Meta:
        abstract = True
