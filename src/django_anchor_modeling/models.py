from types import new_class
from typing import List, Union

import icontract
from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.core.validators import RegexValidator
from django.db import models
from django.db import transaction as db_transaction
from django.db.utils import IntegrityError

from .exceptions import (
    CannotReuseExistingTransactionError,
    MissingTransactionInModelError,
    NotAnAnchorError,
    SentinelTransactionCannotBeUsedError,
    UndeletableModelError,
)
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


class UndeletableModelManager(models.Manager):
    def delete(self, *args, **kwargs):
        qs = self.all()
        for obj in qs:
            if not obj.can_be_deleted():
                raise UndeletableModelError(
                    "Some objects cannot be deleted due to conditions."
                )
        super().delete(*args, **kwargs)


class UndeletableModel(models.Model):
    """
    An abstract base class model that disallows delete
    probably needs another that disallows delete depending on conditions
    """

    objects = UndeletableModelManager()

    class Meta:
        abstract = True

    def can_be_deleted(self):
        """
        Override this method in subclass to set custom delete conditions.
        If not overridden, it will return False, making the instance undeletable.
        """
        return False

    def delete(self, *args, **kwargs):
        raise UndeletableModelError("This model instance cannot be deleted.")


# How to use Undeletable
# Usage
# try:
#     # Attempting to delete using manager
#     UndeletableModel.objects.delete()
# except UndeletableModelError as e:
#     print(f"An exception occurred: {str(e)}")

# try:
#     # Attempting to delete using instance
#     my_instance = UndeletableModel()
#     my_instance.delete()
# except UndeletableModelError as e:
#     print(f"An exception occurred: {str(e)}")

# need computedfields
# class ConditionalUndeletableModelManager(UndeletableModelManager):
#     def delete(self, *args, **kwargs):
#         if self.filter(is_deletable=False).exists():
#             raise UndeletableModelError("Some objects cannot be deleted due to conditions.")
#         super().delete(*args, **kwargs)

# class ConditionalUndeletableModel(ComputedFieldsModel, UndeletableModel):
#     some_field = models.BooleanField(default=False)  # Example field

#     @computed(models.BooleanField(default=False), depends=['some_field'])
#     def is_deletable(self):
#         return self.some_field  # Replace with your actual computation logic

#     objects = ConditionalUndeletableModelManager()

#     class Meta:
#         abstract = True

#     def delete(self, *args, **kwargs):
#         if not self.is_deletable:
#             raise UndeletableModelError("This model instance cannot be deleted due to conditions.")
#         super().delete(*args, **kwargs)


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


# What is Sentinel value?
# It's a dummy value that's used to represent a out of band value. Like NULL.
# See https://en.wikipedia.org/wiki/Sentinel_value for more details
# Here, it's used to represent a NULL Transaction because we don't allow
# NULL values for the foreignkey Transaction field in TransactionBackedModel
SENTINEL_NULL_TRANSACTION_ID = getattr(settings, "SENTINEL_NULL_TRANSACTION_ID", 1)


class Transaction(CreatedModel, UndeletableModel):
    @classmethod
    def get_sentinel(cls):
        return cls.objects.get_or_create(pk=SENTINEL_NULL_TRANSACTION_ID)[0]


class TransactionBackedManager(models.Manager):
    def get_queryset(self):
        return TransactionBackedQuerySet(self.model, using=self._db)


class TransactionBackedQuerySet(models.QuerySet):
    def required_transaction_check(self, transaction: Union[int, "Transaction"] = None):
        if not transaction:
            raise MissingTransactionInModelError(
                "A transaction must be provided for update."
            )

        transaction_id = (
            transaction.id if isinstance(transaction, models.Model) else transaction
        )

        self.model.shared_required_transaction_check(transaction_id)

        return transaction_id

    def update(self, *args, transaction: Union[int, "Transaction"] = None, **kwargs):
        transaction_id = self.required_transaction_check(transaction)

        if self.filter(transaction_id=transaction_id).exists():
            raise CannotReuseExistingTransactionError(
                "New Transaction must be provided for update."
            )

        # Step 1: Get the corresponding historized model
        historized_model = get_historized_model_for(self.model)
        historized_records_queryset = None

        if historized_model:
            # Step 2: Extract primary keys and existing transaction_ids from the active records
            if active_record_data := self.values_list("pk", "transaction_id"):
                # Step 3: Get the corresponding historized records
                historized_records_queryset = historized_model.objects.filter(
                    original__in=[record[0] for record in active_record_data],
                    on_txn__in=[record[1] for record in active_record_data],
                    off_txn=Transaction.get_sentinel(),
                )

        with db_transaction.atomic():
            # Perform the update regardless if historized_model or historized_records is None
            kwargs["transaction_id"] = transaction_id
            super(TransactionBackedQuerySet, self).update(*args, **kwargs)

            # Step 4: Update the historized records
            if historized_records_queryset:
                # Update existing historized records' off_txn to the current transaction
                historized_records_queryset.update(off_txn_id=transaction_id)

                # Fetch the updated active records
                updated_active_records = self.values()

                # Create a list to hold the new historized instances
                new_historized_records = []

                for updated_record in updated_active_records:
                    # updated_record is dict
                    the_active_pk = updated_record.get(
                        "pk", updated_record.get("id", updated_record.get("anchor_id"))
                    )

                    new_historized_instance = historized_model(
                        on_txn_id=transaction_id,
                        off_txn=Transaction.get_sentinel(),
                        original_id=the_active_pk,
                    )

                    for field, value in updated_record.items():
                        if field in [
                            "transaction_id",
                            "id",
                            "pk",
                            "transaction",
                        ]:  # Skip transaction_id as we set it explicitly
                            continue

                        setattr(new_historized_instance, field, value)

                    new_historized_records.append(new_historized_instance)

                # Perform bulk insertion
                historized_model.objects.bulk_create(new_historized_records)

    def delete(self, *args, transaction: Union[int, "Transaction"], **kwargs):
        transaction_id = self.required_transaction_check(transaction)

        # Step 1: Get the corresponding historized model
        historized_model = get_historized_model_for(self.model)
        historized_records_queryset = None

        if historized_model:
            # Step 2: Extract primary keys and existing transaction_ids from the active records
            if active_record_data := self.values_list("pk", "transaction_id"):
                all_the_original_pks = [record[0] for record in active_record_data]
                # Step 3: Get the corresponding historized records
                historized_records_queryset = historized_model.objects.filter(
                    original__in=all_the_original_pks,
                    on_txn__in=[record[1] for record in active_record_data],
                    off_txn=Transaction.get_sentinel(),
                )

        with db_transaction.atomic():
            # Perform the delete regardless if historized_model or historized_records is None
            super(TransactionBackedQuerySet, self).delete(*args, **kwargs)

            # Step 4: Update the historized records
            if historized_records_queryset:
                # Update existing historized records' off_txn to the current transaction
                historized_records_queryset.update(off_txn_id=transaction_id)

            # Step 5: propagate the delete down to attributes
            if self.model.is_anchor is True:
                attribute_classes = self.model.get_attribute_classes()
                for _, related_class in attribute_classes.items():
                    related_class.objects.filter(pk__in=all_the_original_pks).delete(
                        transaction=transaction_id
                    )

    def bulk_create(
        self,
        objs: List[models.Model],
        batch_size=None,
        transaction: Union[int, "Transaction"] = None,
    ):
        """
        ensures the transaction is supplied
        """
        transaction_id = self.required_transaction_check(transaction)

        # Ensure transaction is set in all objects
        for obj in objs:
            obj.transaction_id = transaction_id

        super(TransactionBackedQuerySet, self).bulk_create(objs, batch_size=batch_size)

    def bulk_update(
        self,
        objs,
        fields,
        batch_size=None,
        transaction: Union[int, "Transaction"] = None,
    ):
        """
        the logic is exactly the same as bulk_create
        except it also checks that the transaction_id is not repeated in existing objects
        """
        transaction_id = self.required_transaction_check(transaction)

        obj_ids = [obj.pk for obj in objs]

        if self.filter(pk__in=obj_ids, transaction_id=transaction_id).exists():
            raise CannotReuseExistingTransactionError(
                "New Transaction must be provided for bulk updates."
            )

        for obj in objs:
            obj.transaction_id = transaction_id

        super(TransactionBackedQuerySet, self).bulk_update(
            objs, fields + ["transaction_id"], batch_size=batch_size
        )


def get_historized_model_for(model_or_instance):
    # Identify the target model class
    if isinstance(model_or_instance, type):
        target_model_class = model_or_instance
    else:
        target_model_class = model_or_instance.__class__

    # Retrieve the name of the historized model from the target model's class attribute
    historized_model_name = getattr(target_model_class, "historized_model_name", None)

    if historized_model_name is None:
        return None

    # Use Django's app registry to get the actual historized model class
    return apps.get_model(historized_model_name)

    # content_type = ContentType.objects.get_for_model(model)
    # cache_key = f"historized_model_for_{content_type.app_label}_{content_type.model}"

    # # Try to get the historized model from cache
    # historized_model = cache.get(cache_key)

    # if historized_model is not None:
    #     return historized_model

    # # If it's not in the cache, look it up (replace this with your logic)
    # try:
    #     mapping = HistorizedModelMap.objects.get(active_model=content_type)
    #     historized_model = mapping.historized_model.model_class()
    # except HistorizedModelMap.DoesNotExist:
    #     historized_model = None  # or some default

    # # Store the looked-up value in cache
    # cache.set(cache_key, historized_model)

    # return historized_model


@db_transaction.atomic
def update_historized_on_save(instance, sender=None, *args, **kwargs):
    sender = sender or instance.__class__  # Infer sender from instance if not provided
    # Get the corresponding historized model
    historized_model = get_historized_model_for(sender)

    if historized_model is not None:
        # Update existing historized records with the latest transaction
        historized_model.objects.filter(
            original=instance, off_txn=Transaction.get_sentinel()
        ).update(off_txn=instance.transaction)

        # Create a new historized instance
        historized_instance = historized_model(
            on_txn=instance.transaction, original=instance
        )

        # Copy fields from the original instance to the historized instance
        for field in sender._meta.fields:
            if field.name not in [
                "id",
                "transaction",
            ]:  # Exclude id and transaction fields
                setattr(historized_instance, field.name, getattr(instance, field.name))

        # Save the new historized instance
        historized_instance.save()


@db_transaction.atomic
@icontract.require(
    lambda transaction, pk: transaction is not None and pk is not None,
    "Transaction and pk must not be None",
)
def update_historized_on_delete(
    sender=None, pk=None, transaction=None, *args, **kwargs
):
    # Get the corresponding historized model
    historized_model = get_historized_model_for(sender)

    if historized_model is not None:
        # Update existing historized records with the latest transaction
        historized_model.objects.filter(
            original_id=pk, off_txn=Transaction.get_sentinel()
        ).update(off_txn=transaction)


class TransactionBackedModel(models.Model):
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET(Transaction.get_sentinel),
        default=Transaction.get_sentinel,
    )
    objects = TransactionBackedManager()

    # will be determined as True or False by the inherited classf
    is_anchor = None
    is_attribute = None

    class Meta:
        abstract = True

    def save(self, *args, transaction: Union[int, "Transaction"] = None, **kwargs):
        if transaction:
            if isinstance(transaction, int):
                try:
                    transaction = Transaction.objects.get(pk=transaction)
                except Transaction.DoesNotExist as e:
                    raise Transaction.DoesNotExist from e
            self.transaction = transaction

        self.check_transaction()
        super(TransactionBackedModel, self).save(*args, **kwargs)
        update_historized_on_save(self)

    def delete(self, *args, transaction: Union[int, "Transaction"] = None, **kwargs):
        """
        override typical model.delete method
        """
        if transaction:
            if isinstance(transaction, int):
                try:
                    transaction = Transaction.objects.get(pk=transaction)
                except Transaction.DoesNotExist as e:
                    raise Transaction.DoesNotExist from e
            self.transaction = transaction

        self.check_transaction()
        pk_before_delete = self.pk
        transaction_before_delete = self.transaction
        super(TransactionBackedModel, self).delete(*args, **kwargs)
        update_historized_on_delete(
            sender=self.__class__,
            pk=pk_before_delete,
            transaction=transaction_before_delete,
        )
        if self.is_anchor is True and hasattr(
            self, "delete_attributes_on_anchor_delete"
        ):
            self.delete_attributes_on_anchor_delete(pk=pk_before_delete)

    @staticmethod
    def shared_required_transaction_check(transaction):
        """
        static method to share the logic in model instance method and queryset method
        """
        if not transaction:
            raise MissingTransactionInModelError("A transaction must be provided.")

        transaction_id = transaction
        if isinstance(transaction, Transaction):
            transaction_id = transaction.id

        if transaction_id == SENTINEL_NULL_TRANSACTION_ID:
            raise SentinelTransactionCannotBeUsedError(
                "You cannot use a Sentinel NULL Transaction."
            )

    def required_transaction_check(self, transaction: Union[int, "Transaction"] = None):
        """
        ensure that a valid transaction is set
        """
        if transaction is None:
            transaction = getattr(
                self, "transaction", getattr(self, "transaction_id", None)
            )

        self.shared_required_transaction_check(transaction)

    def check_transaction(self):
        self.required_transaction_check(self.transaction)
        if self.pk:  # Check if this is an update and not a new object
            model_class = type(self)
            try:
                original = model_class.objects.get(pk=self.pk)
            except model_class.DoesNotExist:
                # most probably an Attribute created for first time because of
                # the OneToOneField as pk
                return

            # Priority for checking the transaction object
            if self.transaction and self.transaction == original.transaction:
                raise CannotReuseExistingTransactionError(
                    "New Transaction must be provided for updates or deletes."
                )

            # Fallback to checking the transaction_id if transaction object is not available
            elif self.transaction_id and self.transaction_id == original.transaction_id:
                raise CannotReuseExistingTransactionError(
                    "New Transaction ID must be provided for updates or deletes."
                )


class HistorizedModelMap(models.Model):
    active_model = models.OneToOneField(
        ContentType, related_name="historized_map_active", on_delete=models.CASCADE
    )
    historized_model = models.ForeignKey(
        ContentType, related_name="historized_map_historized", on_delete=models.CASCADE
    )

    @classmethod
    def register(cls, active_model, historized_model):
        active_content_type = ContentType.objects.get_for_model(active_model)
        historized_content_type = ContentType.objects.get_for_model(historized_model)
        cls.objects.get_or_create(
            active_model=active_content_type, historized_model=historized_content_type
        )


def should_skip_field_to_be_shadowed(field, active_model_class):
    """
    Determines whether a field should be skipped based on certain conditions.

    Parameters:
        field: The field object.
        active_model_class: The active model class.
        Transaction: The Transaction model class.

    Returns:
        bool: True if the field should be skipped, False otherwise.
    """
    # Condition 1: Skip the primary key
    if field.name == active_model_class._meta.pk.name:
        return True

    # Condition 2: Skip if the field is a ForeignKey and its target model is Transaction
    if isinstance(field, models.ForeignKey) and field.related_model == Transaction:
        return True

    return False


import copy


def _generate_history_field(original_model, field):
    if isinstance(field, models.AutoField):
        return models.IntegerField()
    elif isinstance(field, models.BigAutoField):
        return models.BigIntegerField()
    elif not field.concrete:
        return field

    # Deep copy the field to avoid altering the original
    field = copy.deepcopy(field)

    # Check if the field is a ForeignKey
    if isinstance(field, models.ForeignKey):
        if related_name := getattr(field, "_related_name", None):
            field._related_name = f"historized_{related_name}"
        if related_query_name := getattr(field, "_related_query_name", None):
            field._related_query_name = f"historized_{related_query_name}"

    getattr(field, "swappable", None)
    field.swappable = False
    return field


def create_historized_model(original_model):
    model_name = f"Historized{original_model.__name__}"
    app_label = original_model._meta.app_label
    app = apps.app_configs[app_label]
    models_module = f"{app.module.__name__}.models"

    # Additional attributes and metadata could be defined here
    additional_attrs = {}
    additional_meta = {"abstract": False}

    # Create a new ForeignKey field that relates to the original model
    # will neer be deleted
    original_foreign_key = models.ForeignKey(
        original_model,
        on_delete=models.DO_NOTHING,
        related_name="versions",
        db_constraint=False,
    )

    exclude = [
        "id",
        "transaction",
        "transaction_id",
        "pk",
        "anchor",
        # "business_identifier",
    ]

    # Generate fields dynamically, excluding the specified ones
    # CANNOT use _meta.fields_map as it will cause Models aren't loaded yet error
    # USE _meta.fields instead
    generated_fields = {
        field.name: _generate_history_field(original_model, field)
        for field in original_model._meta.fields
        if field.name not in exclude
    }

    class_attrs = {
        "__module__": models_module,
        "Meta": type(
            "Meta", (), {"abstract": False, "app_label": app_label, **additional_meta}
        ),
        "original": original_foreign_key,  # New ForeignKey field
        "original_model": original_model,  # The class attribute for original_model
        **generated_fields,
        **additional_attrs,
    }

    # Create the new model class dynamically
    return type(model_name, (Historized,), class_attrs)


from django.db import models


class Historized(models.Model):
    # Your fields here
    on_txn = models.ForeignKey(
        Transaction,
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        default=Transaction.get_sentinel,
        related_name="created_%(app_label)s_%(class)ss",
        related_query_name="that_created_%(app_label)s_%(class)ss",
    )
    off_txn = models.ForeignKey(
        Transaction,
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        default=Transaction.get_sentinel,
        related_name="deactivated_%(app_label)s_%(class)ss",
        related_query_name="that_deactivated_%(app_label)s_%(class)ss",
    )

    class Meta:
        abstract = True

    @classmethod
    def historized_setup(cls):
        # Your setup logic here for the Historized model
        if cls._meta.abstract:
            return

        # original_class = cls

        # class_name = f"Historized{original_class.__name__}"
        # app_label = original_class._meta.app_label

        # # Create Meta class dynamically
        # class Meta:
        #     abstract = False

        # # Define new attributes
        # attrs = {
        #     "Meta": Meta,
        #     "__module__": original_class.__module__,
        #     "id": models.BigAutoField(primary_key=True),
        #     # Add fields from the original model class, skipping 'id' and 'transaction'
        #     **{
        #         f.name: f
        #         for f in original_class._meta.fields
        #         if f.name not in ["id", "transaction"]
        #     },
        #     "original": models.ForeignKey(
        #         original_class,
        #         on_delete=models.DO_NOTHING,
        #         db_constraints=False,
        #         related_name="versions",
        #     ),
        # }

        # # Create the new model class
        # new_model = type(class_name, (original_class, Historized), attrs)

        # # Register this new model with Django's app registry
        # apps.register_model(app_label, new_model)


def historize_model(*args, **kwargs):
    """
    decorator applied to Django model class to historize it
    as in create another Django model class with `Historized` prepended to the
    same class name and have it inherit the Historized abstract class
    """

    def _model_wrapper(model_class):
        """

        1. Calls create_historized_model: It calls create_historized_model with the model class and the parameters that were passed to track. This effectively creates a new, associated event tracking model for model_class.
        2. Returns model_class: After setting up the event tracking, it returns the original model class unchanged.
        """
        historized_model = create_historized_model(model_class)

        model_class.historized_model_name = (
            f"{historized_model._meta.app_label}.{historized_model.__name__}"
        )

        return model_class

    # If it's being used without arguments, args[0] will be the model class itself
    return _model_wrapper(args[0]) if args else _model_wrapper


class TransactionBackedAnchorNoBusinessId(TransactionBackedModel):
    is_anchor = True
    is_attribute = False

    class Meta:
        abstract = True

    @classmethod
    def get_attribute_classes(cls):
        """
        Only meant for Anchor class
        """
        if cls.is_anchor is not True:
            return {}

        related_classes = {}

        for relation in cls._meta.get_fields():
            if (
                isinstance(relation, models.OneToOneRel)
                and relation.remote_field.primary_key
                and getattr(relation.remote_field.model, "is_attribute", False)
            ):
                related_model = relation.related_model
                related_name = relation.get_accessor_name()
                related_classes[related_name] = related_model

        return related_classes

    def get_attributes(self, pk):
        """
        Only meant for Anchor class
        """
        if self.is_anchor is not True:
            return {}

        if not pk:
            pk = self.pk

        related_instances = {}
        for relation in type(self)._meta.get_fields():
            if (
                isinstance(relation, models.OneToOneRel)
                and relation.remote_field.primary_key
                and getattr(relation.remote_field.related_model, "is_attribute", False)
            ):
                related_model = relation.related_model
                related_name = (
                    relation.get_accessor_name()
                )  # Use the accessor name (related_name or default)
                try:
                    related_instance = related_model.objects.get(anchor_id=pk)
                    related_instances[related_name] = related_instance
                except related_model.DoesNotExist:
                    continue

    @icontract.require(lambda pk: pk is not None, "pk must not be None")
    def delete_attributes_on_anchor_delete(self, pk=None):
        if self.is_anchor is not True:
            raise NotAnAnchorError("This method is not allowed if not an Anchor class")
        attributes = self.get_attributes(pk)
        for _, related_instance in attributes.items():
            related_instance.delete(transaction=self.transaction)


class TransactionBackedAnchorWithBusinessId(TransactionBackedAnchorNoBusinessId):
    business_identifier = BusinessIdentifierField(unique=True)

    class Meta:
        abstract = True


class KnotManager(models.Manager):
    def ensure_choices_exist(self):
        model_cls = self.model
        model_name = model_cls.__name__
        textchoices_inner_class = getattr(model_cls, "TextChoices", None)
        if textchoices_inner_class is None:
            raise ImproperlyConfigured(
                f"Need to define TextChoices inner class for {model_name}"
            )
        choices = getattr(textchoices_inner_class, "choices", {})

        if not choices:
            raise ImproperlyConfigured(
                "Need to define at least one choice using ALL_CAPS class attribute ",
                f"for {model_name}.TextChoices",
            )

        for value, label in choices:
            try:
                _, created = model_cls.objects.get_or_create(pk=value, label=label)
                if created:
                    print(f"Created {model_name} with pk {value}, label {label}")
                else:
                    print(f"{model_name} with pk {value}, label {label} already exists")
            except IntegrityError:
                print(f"Could not create {model_name} with pk {value}. IntegrityError.")
                # re-raise the exception
                raise


class Knot(UndeletableModel):
    """
    ref https://docs.djangoproject.com/en/4.2/ref/models/fields/#enumeration-types
    """

    id = models.CharField(max_length=255, primary_key=True)
    label = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class TextChoices(models.TextChoices):
        pass

    objects = KnotManager()

    class Meta:
        abstract = True


def transaction_backed_static_attribute(
    anchor_class, value_type, related_name="%(class)s_related"
):
    """
    A factory function that generates a model for static attributes.

    Args:
        anchor_class: The class to which the static attribute is anchored.
        value_type: The type of the static attribute value.
        related_name (str, optional): The related name for the anchor field. Defaults to "%(class)s_related".

    Returns:
        StaticAttribute: A model for static attributes.

    """

    class TransactionBackedStaticAttribute(TransactionBackedModel):
        """
        A model for static attributes.

        This also works for ForeignKey as attributes

        Attributes:
            anchor (OneToOneField): A OneToOneField to the anchor class as primary key.
            value (value_type): A field representing the value of the static attribute.
            objects (TransactionBackedManager): The manager instance for the model.

        Meta:
            abstract (bool): Specifies that this model is an abstract base class.

        """

        is_anchor = False
        is_attribute = True

        # the on_delete is set to DO_NOTHING
        # because we want fine grained control over the deletion of anchor
        # as we want to update all the impacted attributes and their historized with the same
        # transaction
        anchor = models.OneToOneField(
            anchor_class,
            on_delete=models.DO_NOTHING,
            related_name=related_name,
            primary_key=True,
        )
        value = value_type

        objects = TransactionBackedManager()

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

    return TransactionBackedStaticAttribute


# Example usage
# from django.db import models

# class MyActiveModel(TransactionBackedModel):
#     name = models.CharField(max_length=100)
#     age = models.IntegerField()

# # Generate the abstract historized model
# AbstractForThisHistorized = historized_model(MyActiveModel)

# # Create the concrete historized model
# class HistorizedMyModel(AbstractForThisHistorized):
#     # You can add additional fields or methods here if needed
#     pass


# Now, HistorizedMyModel is an abstract model that "shadows" MyActiveModel.

# then need to register so that can connect the save and delete model methods
# HistorizedModelMap.register(MyActiveModel, HistorizedMyActiveModel)


# LimitedGFK (seldom GFK is really unlimited)
# need to inherit StaticTie
# then allow a limited generic_foreign_key (is_under_what_id, under_what_type as the Knot value)
# allow the Knot class to setup the limited choices
# create custom filter like static_attribute as well

# LimitedGFK is really OneGenericOneSpecificTie
# Specific is foreignkey so will ahve related_name
# this will auto create the Specific.filters.get_by_related_name(Union[Generic1, Generic2, Generic3])
# but the Generic1, Generic2, Generic3 will not have related_name so need a map
# this will auto create the Generic1.filters.get_by_related_name(Specific)
# this will auto create the Generic2.filters.get_by_related_name(Specific)
# this will auto create the Generic3.filters.get_by_related_name(Specific)

# ModelUnionKnot extends Knot to allow a union of models. once the UNION is set, auto fill up the Textchoices


# Undeletable as separate attribute


# from computedfields.models import ComputedFieldsModel, computed

# def anchor_is_deletable(anchor_class, related_name="%(class)s_is_deletable"):
#     class AnchorIsDeletable(ComputedFieldsModel, ZeroUpdateStrategyModel):
#         anchor = models.OneToOneField(
#             anchor_class,
#             on_delete=models.CASCADE,
#             related_name=related_name,
#             primary_key=True,
#         )
#         value = models.BooleanField(default=False)


#         @computed(models.BooleanField(default=False), depends=['anchor.related_attribute.value'])
#         def is_deletable(self):
#             return self.anchor.related_attribute.value  # Replace with your actual computation logic


#         objects = ZeroUpdateStrategyManager()

#         class Meta:
#             abstract = True

#     return AnchorIsDeletable
