import contextlib

import pytz
from django.conf import settings
from django.core.exceptions import (
    FieldDoesNotExist,
    FieldError,
    ImproperlyConfigured,
    ValidationError,
)
from django.db import IntegrityError, models, transaction
from django.db.models.constants import LOOKUP_SEP
from django.db.models.utils import resolve_callables
from django.utils import timezone


class ZeroUpdateStrategyManager(models.Manager):
    """
    A manager class that provides a zero update strategy for model instances.
    """

    def delete_and_create(self, pk=None, anchor=None, **kwargs):
        """
        Deletes the given instance from the database and creates a new instance with the
        provided keyword arguments.

        Args:
            pk: The primary key of the instance to delete. Used for regular models.
            anchor: The related object for OneToOneField primary key.
                    This serves as the unique identifier. Used for models
                    with OneToOneField as primary key.
            **kwargs: The keyword arguments used to create the new instance.

        Returns:
            Model: The newly created instance.
        """

        # Validate the input based on whether the model uses OneToOneField as a PK
        if isinstance(self.model._meta.pk, models.OneToOneField):
            if anchor is None:
                error_text = (
                    "anchor must be provided for models "
                    "with OneToOneField as primary key."
                )
                raise ValueError(error_text)
        elif pk is None:
            raise ValueError("pk must be provided for regular models.")

        with transaction.atomic():
            # Delete the existing instance
            if isinstance(self.model._meta.pk, models.OneToOneField):
                self.filter(pk=anchor.pk).delete()
            else:
                self.filter(pk=pk).delete()

            # Prepare the kwargs for creating a new instance
            if isinstance(self.model._meta.pk, models.OneToOneField):
                kwargs[self.model._meta.pk.name] = anchor
            else:
                kwargs["pk"] = pk

            new_instance = self.model(**kwargs)
            new_instance.avoid_recursion = True
            new_instance.save()

        return new_instance

    def create(self, **kwargs):
        """
        Creates a new instance of the model with the given keyword arguments,
        sets the 'created_via_manager' and 'avoid_recursion' attributes to True,
        saves the instance to the database, and returns the instance.

        Args:
            **kwargs: The keyword arguments used to create the instance.

        Returns:
            Model: The created instance.
        """

        instance = self.model(**kwargs)
        instance.created_via_manager = True
        instance.avoid_recursion = True  # prevent recursion in save
        instance.save()
        instance.created_via_manager = False
        instance.avoid_recursion = False  # prevent recursion in save
        return instance

    def _extract_model_params(self, defaults, **kwargs):
        """
        Replicated from Django 4.2.6 at
        https://github.com/django/django/blob/c22017bd1dddb5b57d8a179e6378ef0c8d7f5eeb/django/db/models/query.py#L981
        Prepare `params` for creating a model instance based on the given
        kwargs; for use by get_or_create().
        """
        defaults = defaults or {}
        params = {k: v for k, v in kwargs.items() if LOOKUP_SEP not in k}
        params |= defaults
        property_names = self.model._meta._property_names
        invalid_params = []
        for param in params:
            try:
                self.model._meta.get_field(param)
            except FieldDoesNotExist:
                # It's okay to use a model's property if it has a setter.
                if not (param in property_names and getattr(self.model, param).fset):
                    invalid_params.append(param)
        if invalid_params:
            raise FieldError(
                "Invalid field name(s) for model %s: '%s'."
                % (
                    self.model._meta.object_name,
                    "', '".join(sorted(invalid_params)),
                )
            )
        return params

    def get_or_create(self, defaults=None, **kwargs):
        """
        Replicated from Django 4.2.6 at
        https://github.com/django/django/blob/c22017bd1dddb5b57d8a179e6378ef0c8d7f5eeb/django/db/models/query.py#L906
        Look up an object with the given kwargs, creating one if necessary.
        Return a tuple of (object, created), where created is a boolean
        specifying whether an object was created.
        """
        try:
            return self.get(**kwargs), False
        except self.model.DoesNotExist:
            params = self._extract_model_params(defaults, **kwargs)
            # Try to create an object using passed params.
            try:
                with transaction.atomic(using=self.db):
                    params = dict(resolve_callables(params))
                    return self.create(**params), True
            except IntegrityError:
                with contextlib.suppress(self.model.DoesNotExist):
                    return self.get(**kwargs), False
                raise

    def update_or_create(self, *args, **kwargs):
        """
        Raises a NotImplementedError with a message indicating that update_or_create is not
        allowed in ZeroUpdateStrategyManager.

        Raises:
            NotImplementedError: Raised when update_or_create is called in
            ZeroUpdateStrategyManager.

        Example:
            ```python
            manager = ZeroUpdateStrategyManager()
            try:
                manager.update_or_create()
            except NotImplementedError as e:
                print(str(e))  # Output: update_or_create is not allowed in ZeroUpdateStrategyManager
            ```
        """

        raise NotImplementedError(
            "update_or_create is not allowed in ZeroUpdateStrategyManager"
        )

    def bulk_create(self, *args, **kwargs):
        """
        Raises a NotImplementedError with a message indicating that bulk_create is not
        allowed in ZeroUpdateStrategyManager.

        Raises:
            NotImplementedError: Raised when bulk_create is called in
            ZeroUpdateStrategyManager.

        Example:
            ```python
            manager = ZeroUpdateStrategyManager()
            try:
                manager.bulk_create()
            except NotImplementedError as e:
                print(str(e))  # Output: bulk_create is not allowed in ZeroUpdateStrategyManager
            ```
        """

        raise NotImplementedError(
            "bulk_create is not allowed in ZeroUpdateStrategyManager"
        )

    def bulk_update(self, *args, **kwargs):
        """
        Raises a NotImplementedError with a message indicating that bulk_update is not
        allowed in ZeroUpdateStrategyManager.

        Raises:
            NotImplementedError: Raised when bulk_update is called in
            ZeroUpdateStrategyManager.

        Example:
            ```python
            manager = ZeroUpdateStrategyManager()
            try:
                manager.bulk_update()
            except NotImplementedError as e:
                print(str(e))  # Output: bulk_update is not allowed in ZeroUpdateStrategyManager
            ```
        """

        raise NotImplementedError(
            "bulk_update is not allowed in ZeroUpdateStrategyManager"
        )

    def update(self, *args, **kwargs):
        """
        Raises a NotImplementedError with a message indicating that update is not
        allowed in ZeroUpdateStrategyManager.

        Raises:
            NotImplementedError: Raised when update is called in
            ZeroUpdateStrategyManager.

        Example:
            ```python
            manager = ZeroUpdateStrategyManager()
            try:
                manager.update()
            except NotImplementedError as e:
                # Output: update is not allowed in ZeroUpdateStrategyManager
                print(str(e))
            ```
        """
        raise NotImplementedError("update is not allowed in ZeroUpdateStrategyManager")


class CompositeKeyManager(ZeroUpdateStrategyManager):
    """
    A manager class for models that use a composite key.

    Attributes:
        check_for_from_epoch (bool): Indicates whether to check for the presence of
        'from_epoch' in the composite key fields.
        Defaults to False.

    """

    check_for_from_epoch = False

    def create_composite_key(self, instance):
        """
        Creates a composite key for given instance based on
        composite_key_fields option defined in its model class.

        The order follows the order in which the fields are defined in
        composite_key_fields option.

        Args:
            self: The manager instance.
            instance: The instance for which to create the composite key.

        Returns:
            str: Composite key generated from the foreign key values of the instance.

        """
        composite_key_fields_option = instance.composite_key_fields

        if not composite_key_fields_option:
            raise ImproperlyConfigured(
                f"{instance._meta.model_name} must define composite_key_fields."
            )

        # Handle the different ways composite_key_fields can be defined
        if isinstance(composite_key_fields_option, (list, tuple)):
            composite_key_fields_fields = composite_key_fields_option
        else:
            composite_key_fields_fields = []

        if not composite_key_fields_fields:
            raise ImproperlyConfigured(
                f"composite_key_fields in {instance._meta.model_name} cannot be empty"
            )

        if (
            self.check_for_from_epoch
            and "from_epoch" not in composite_key_fields_fields
        ):
            error_message = (
                f"composite_key_fields in {instance._meta.model_name} must contain"
                " 'from_epoch'"
                " because {instance._meta.model_name} is a historized model."
            )
            raise ImproperlyConfigured(error_message)

        foreign_keys = [
            field
            for field in composite_key_fields_fields
            if isinstance(instance._meta.get_field(field), models.ForeignKey)
        ]

        composite_key_parts = []
        for fk in foreign_keys:
            fk_value = getattr(instance, f"{fk}_id", None)
            if fk_value is not None:
                composite_key_parts.append(str(fk_value))

        return ".".join(composite_key_parts)

    def create(self, **kwargs):
        """
        Creates a new instance of the model with the given keyword arguments, assigns a composite key to the instance, saves it to the database, and returns the instance.

        Args:
            **kwargs: The keyword arguments used to create the instance.

        Returns:
            Model: The created instance.

        Example:
            ```python
            manager = MyModelManager()
            instance = manager.create(field1='value1', field2='value2')
            print(instance.id)  # Output: <composite key value>
            ```
        """
        try:
            with transaction.atomic():
                instance = self.model(**kwargs)
                instance.id = self.create_composite_key(instance)
                return super().create(**kwargs)
        except IntegrityError as e:
            if "unique constraint" in str(e).lower() and "id" in str(e).lower():
                raise ValidationError(
                    f"A record with the composite key {instance.id} already exists."
                ) from e
            raise  # Re-raise the original exception if it wasn't due to id uniqueness


class FromModelManager(ZeroUpdateStrategyManager):
    """
    A manager class for any model that inherits FromModel
    """

    def timezone_create(self, tz, **kwargs):
        """
        Creates a new instance with the given timezone, anchor, and value.

        Args:
            tz: The timezone for the instance.
            anchor: The anchor for the instance.
            value: The value for the instance.
            **kwargs: Additional attributes for the instance.

        Returns:
            The newly created instance.
        """
        return self.create_with_timezone(pytz.timezone(tz), **kwargs)

    def create_with_timezone(self, tz, **kwargs):
        """
        Creates a new instance with the given timezone, and additional attributes.

        Args:
            tz: The timezone for the instance.
            **kwargs: Additional attributes for the instance.

        Returns:
            The newly created instance.
        """
        kwargs |= {
            "from_epoch": int(timezone.now().timestamp()),
            "from_utc_start": timezone.now().strftime("%Y-%m-%dT%H:%M:%S%z"),
            "from_local_start": timezone.now()
            .astimezone(tz)
            .strftime("%Y-%m-%dT%H:%M:%S"),
            "from_timezone_id": str(tz),
            "from_timezone_rules": pytz.OLSON_VERSION,
        }
        return super().create(**kwargs)

    def create(self, **kwargs):
        """
        Creates a new instance with the given additional attributes.
        The instance is created with the default timezone.

        Args:
            **kwargs: Additional attributes for the instance.

        Returns:
            The newly created instance.
        """
        default_tz = pytz.timezone(settings.TIME_ZONE)
        return self.create_with_timezone(default_tz, **kwargs)


class HistorizedAttributeManager(ZeroUpdateStrategyManager):
    """
    A manager class for HistorizedAttribute model
    """

    def timezone_create(self, tz, anchor, value, **kwargs):
        """
        Creates a new instance with the given timezone, anchor, and value.

        Args:
            tz: The timezone for the instance.
            anchor: The anchor for the instance.
            value: The value for the instance.
            **kwargs: Additional attributes for the instance.

        Returns:
            The newly created instance.
        """
        return self.create_with_timezone_and_anchor(
            pytz.timezone(tz), anchor, value, **kwargs
        )

    def create_with_timezone_and_anchor(self, tz, anchor, value, **kwargs):
        """
        Creates a new instance with the given timezone, anchor, value.
        Note that the primary key is a composite of anchor and timestamp.

        Args:
            tz: The timezone for the instance.
            anchor: The anchor for the instance.
            value: The value for the instance.
            **kwargs: Additional attributes for the instance.

        Returns:
            The newly created instance.
        """
        current_time = timezone.now()
        from_epoch = int(current_time.timestamp())
        local_time = current_time.astimezone(tz)

        kwargs |= {
            "id": f"{str(anchor.id)}.{from_epoch}",
            "anchor": anchor,
            "value": value,
            "from_epoch": from_epoch,
            "from_utc_start": current_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "from_local_start": local_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "from_timezone_id": str(tz),
            "from_timezone_rules": pytz.OLSON_VERSION,
        }
        return super().create(**kwargs)

    def create(self, anchor, value, **kwargs):
        """
        Creates a new instance with the given anchor, value, and additional attributes.
        The instance is created with the default timezone.

        Args:
            anchor: The anchor for the instance.
            value: The value for the instance.
            **kwargs: Additional attributes for the instance.

        Returns:
            The newly created instance.
        """
        default_tz = pytz.timezone(settings.TIME_ZONE)
        return self.create_with_timezone_and_anchor(default_tz, anchor, value, **kwargs)


class HistorizedTieManager(FromModelManager, CompositeKeyManager):
    """
    A manager class for the HistorizedTie model that combines the functionality of
    FromModelManager and CompositeKeyManager.

    """

    check_for_from_epoch = True
