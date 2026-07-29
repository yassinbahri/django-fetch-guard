from django.core import exceptions as django_exceptions


class LegacyFieldFetchBlocked(django_exceptions.FieldError):
    """Raised when a legacy strict policy blocks an implicit database fetch."""


FieldFetchBlocked = getattr(
    django_exceptions,
    "FieldFetchBlocked",
    LegacyFieldFetchBlocked,
)
