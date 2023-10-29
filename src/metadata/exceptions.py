from django.core.exceptions import PermissionDenied


class ActiveModelClassMustBeTransactionBackedError(PermissionDenied):
    pass
