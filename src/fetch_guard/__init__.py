"""Public API for django-fetch-guard."""

from importlib.metadata import PackageNotFoundError, version

from .managers import FetchGuardQuerySet, GuardedManager
from .modes import guard_queryset, resolve_fetch_mode
from .exceptions import FieldFetchBlocked, get_fetch_diagnostic
from .models import FetchGuardModelMixin
from .diagnostics import FetchCallSite, FetchDiagnostic, FetchType

try:
    __version__ = version("django-fetch-guard")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0+unknown"

__all__ = [
    "FetchGuardQuerySet",
    "FetchGuardModelMixin",
    "FieldFetchBlocked",
    "FetchCallSite",
    "FetchDiagnostic",
    "FetchType",
    "GuardedManager",
    "get_fetch_diagnostic",
    "guard_queryset",
    "resolve_fetch_mode",
]
