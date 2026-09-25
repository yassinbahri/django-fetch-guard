from dataclasses import dataclass
from enum import Enum
import sys

from django import get_version
from django.core.exceptions import FieldDoesNotExist


class FetchType(str, Enum):
    """Stable categories for an implicit model-field fetch."""

    DEFERRED_FIELD = "deferred_field"
    FORWARD_FOREIGN_KEY = "forward_foreign_key"
    FORWARD_ONE_TO_ONE = "forward_one_to_one"
    REVERSE_ONE_TO_ONE = "reverse_one_to_one"
    REVERSE_ONE_TO_MANY = "reverse_one_to_many"
    MANY_TO_MANY = "many_to_many"
    RELATION = "relation"


@dataclass(frozen=True, slots=True)
class FetchCallSite:
    """Application call site without source text, locals, or an absolute path."""

    module: str
    function: str
    line: int

    def __str__(self):
        return f"{self.module}.{self.function}:{self.line}"


@dataclass(frozen=True, slots=True)
class FetchDiagnostic:
    """Structured, serializable context for a blocked implicit fetch."""

    model: str
    field: str
    fetch_type: FetchType
    policy: str
    django_version: str
    suggestion: str
    call_site: FetchCallSite | None = None

    def as_dict(self):
        result = {
            "model": self.model,
            "field": self.field,
            "fetch_type": self.fetch_type.value,
            "policy": self.policy,
            "django_version": self.django_version,
            "suggestion": self.suggestion,
        }
        if self.call_site is not None:
            result["call_site"] = {
                "module": self.call_site.module,
                "function": self.call_site.function,
                "line": self.call_site.line,
            }
        return result

    def format(self):
        location = f"\nLocation: {self.call_site}" if self.call_site else ""
        return (
            f"Implicit database fetch blocked\n"
            f"Model: {self.model}\n"
            f"Field: {self.field}\n"
            f"Fetch type: {self.fetch_type.value}{location}\n"
            f"Suggested fix: {self.suggestion}"
        )


def capture_call_site():
    """Return the first non-Django, non-fetch-guard Python frame."""
    frame = sys._getframe(1)
    while frame is not None:
        module = frame.f_globals.get("__name__", "")
        if not module.startswith(("django.", "fetch_guard.")):
            return FetchCallSite(
                module=module or "<unknown>",
                function=frame.f_code.co_name,
                line=frame.f_lineno,
            )
        frame = frame.f_back
    return None


def _resolve_field(instance, name):
    try:
        return instance._meta.get_field(name)
    except FieldDoesNotExist:
        for field in instance._meta.get_fields():
            get_accessor_name = getattr(field, "get_accessor_name", None)
            if get_accessor_name is not None and get_accessor_name() == name:
                return field
    return None


def _classify_fetch(instance, name, field):
    if name in instance.get_deferred_fields() and not field.is_relation:
        return FetchType.DEFERRED_FIELD
    if field.auto_created:
        if field.one_to_one:
            return FetchType.REVERSE_ONE_TO_ONE
        if field.one_to_many:
            return FetchType.REVERSE_ONE_TO_MANY
        if field.many_to_many:
            return FetchType.MANY_TO_MANY
    if field.one_to_one:
        return FetchType.FORWARD_ONE_TO_ONE
    if field.many_to_one:
        return FetchType.FORWARD_FOREIGN_KEY
    if field.many_to_many:
        return FetchType.MANY_TO_MANY
    return FetchType.RELATION


def _suggestion(fetch_type, name):
    if fetch_type in {
        FetchType.FORWARD_FOREIGN_KEY,
        FetchType.FORWARD_ONE_TO_ONE,
        FetchType.REVERSE_ONE_TO_ONE,
    }:
        return f'queryset.select_related("{name}")'
    if fetch_type in {FetchType.REVERSE_ONE_TO_MANY, FetchType.MANY_TO_MANY}:
        return f'queryset.prefetch_related("{name}")'
    if fetch_type is FetchType.DEFERRED_FIELD:
        return f'include "{name}" in only(), or remove it from defer()'
    return f'explicitly preload "{name}" before applying strict mode'


def diagnostic_for_access(instance, name, *, policy="raise", call_site=None):
    """Build a diagnostic for a model attribute, or return ``None``."""
    field = _resolve_field(instance, name)
    if field is None:
        return None
    fetch_type = _classify_fetch(instance, name, field)
    return FetchDiagnostic(
        model=instance._meta.label,
        field=name,
        fetch_type=fetch_type,
        policy=policy,
        django_version=get_version(),
        suggestion=_suggestion(fetch_type, name),
        call_site=call_site,
    )
