from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from icontract import ViolationError


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


# Custom exception class for a specific type of contract violation
class TransactionTypeError(ViolationError):
    """
    use this exception to indicate that a transaction is not Transation type
    and inside an icontract require clause

    Example:
    >>> @require(
    >>>  lambda transaction=None: transaction is None or isinstance(transaction, Transaction),
    >>>  description="'transaction' in kwargs must be an instance of 'Transaction'.",
    >>>  error=TransactionTypeError  # Use your custom exception here
    >>> )
    >>> def save_project_fas(
    >>>   *,
    >>>   project: Union[Project, int],
    >>>   fas: Union[Fas, int],
    >>>   transaction: Union[Transaction, None] = None,
    >>>   **kwargs
    >>> ):
    """

    pass
