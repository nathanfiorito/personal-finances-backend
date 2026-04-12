class DomainError(Exception):
    """Base class for all domain-level errors."""


class ExpenseNotFoundError(DomainError):
    pass


class CategoryNotFoundError(DomainError):
    pass


class DuplicateExpenseError(DomainError):
    pass


class CategoryAlreadyExistsError(DomainError):
    pass
