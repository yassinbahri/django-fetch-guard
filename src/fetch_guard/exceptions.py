from django.core import exceptions as django_exceptions


class LegacyFieldFetchBlocked(django_exceptions.FieldError):
    """Raised when a legacy strict policy blocks an implicit database fetch."""


FieldFetchBlocked = getattr(
    django_exceptions,
    "FieldFetchBlocked",
    LegacyFieldFetchBlocked,
)


def attach_fetch_diagnostic(exception, diagnostic):
    """Attach structured context while preserving the active exception type."""
    exception.fetch_guard_diagnostic = diagnostic
    return exception


def get_fetch_diagnostic(exception):
    """Return Fetch Guard context from a blocked-fetch exception, if present."""
    return getattr(exception, "fetch_guard_diagnostic", None)
