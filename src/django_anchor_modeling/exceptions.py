from django.core.exceptions import ImproperlyConfigured, PermissionDenied


class UndeletableModelError(PermissionDenied):
    pass


class CustomTransactionExceptionWithCode(ImproperlyConfigured):
    code = None

    def __init__(self, message, *args, **kwargs):
        if self.code is not None:
            message = f"[{self.code}] {message}"
        super().__init__(message, *args, **kwargs)


class ActiveModelClassMustBeTransactionBackedError(CustomTransactionExceptionWithCode):
    code = "TE001"


class CannotReuseExistingTransactionError(CustomTransactionExceptionWithCode):
    code = "TE002"


class MissingTransactionInModelError(CustomTransactionExceptionWithCode):
    code = "TE003"


class SentinelTransactionCannotBeUsedError(CustomTransactionExceptionWithCode):
    code = "TE004"


class CustomTransactionBackedExceptionWithCode(PermissionDenied):
    code = None

    def __init__(self, message, *args, **kwargs):
        if self.code is not None:
            message = f"[{self.code}] {message}"
        super().__init__(message, *args, **kwargs)


class NotAnAnchorError(CustomTransactionBackedExceptionWithCode):
    code = "TBE001"
