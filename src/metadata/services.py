from django.db import transaction

from .models import DataChange, DataChangeReason


def create_change_with_reason(reason: str):
    """
    Create DataChange with the given reason.

    Args:
        reason (str): The reason for the data change.

    Returns:
        DataChange: The created data change.

    Raises:
        ValueError: If the reason is an empty string.
    """

    if not reason:
        raise ValueError("Reason cannot be an empty string")

    with transaction.atomic():
        change = DataChange.objects.create()
        DataChangeReason.objects.create(anchor=change, value=reason)
        return change
