from enum import Enum

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models.query import ModelIterable

from .models import FetchGuardModelMixin


class LegacyFetchMode(Enum):
    ONE = "one"
    PEERS = "peers"
    RAISE = "raise"


NATIVE_RAISE_MODE = getattr(models, "FETCH_RAISE", None) or getattr(
    models, "RAISE", None
)
HAS_NATIVE_FETCH_MODES = (
    hasattr(models, "FETCH_ONE")
    and hasattr(models, "FETCH_PEERS")
    and NATIVE_RAISE_MODE is not None
)


def _mode(name):
    if HAS_NATIVE_FETCH_MODES:
        if name == "RAISE":
            return NATIVE_RAISE_MODE
        return getattr(models, f"FETCH_{name}")
    return LegacyFetchMode[name]


MODE_ALIASES = {
    "one": "ONE",
    "normal": "ONE",
    "fetch_one": "ONE",
    "peers": "PEERS",
    "fetch_peers": "PEERS",
    "raise": "RAISE",
    "strict": "RAISE",
}

CANONICAL_MODE_NAMES = ("one", "peers", "raise")


def resolve_fetch_mode(mode):
    """Resolve a friendly name to the active Django-version fetch mode."""
    if isinstance(mode, str):
        normalized = mode.strip().lower().replace("-", "_")
        try:
            return _mode(MODE_ALIASES[normalized])
        except KeyError as exc:
            choices = ", ".join(CANONICAL_MODE_NAMES)
            raise ValueError(
                f"Unknown fetch guard mode {mode!r}. Expected one of: {choices}."
            ) from exc

    native_modes = tuple(
        mode
        for mode in (
            getattr(models, "FETCH_ONE", None),
            getattr(models, "FETCH_PEERS", None),
            NATIVE_RAISE_MODE,
        )
        if mode is not None
    )
    if mode in native_modes or isinstance(mode, LegacyFetchMode):
        return mode

    raise TypeError("Fetch guard mode must be a supported string or Django fetch mode.")


class LegacyGuardedModelIterable(ModelIterable):
    def __iter__(self):
        for instance in super().__iter__():
            instance.__dict__["_fetch_guard_legacy_mode"] = "raise"
            context = getattr(self.queryset.query, "_fetch_guard_context", None)
            if context is not None:
                instance.__dict__["_fetch_guard_context"] = context
            yield instance


class DiagnosticModelIterable(ModelIterable):
    def __iter__(self):
        for instance in super().__iter__():
            context = getattr(self.queryset.query, "_fetch_guard_context", None)
            if context is not None:
                instance.__dict__["_fetch_guard_context"] = context
            yield instance


def _legacy_peer_relations(queryset, relations):
    if relations:
        return relations
    return tuple(
        field.name
        for field in queryset.model._meta.get_fields()
        if field.concrete
        and field.is_relation
        and (field.many_to_one or field.one_to_one)
    )


def _legacy_guard_queryset(queryset, mode, relations):
    if mode is LegacyFetchMode.ONE:
        if queryset._iterable_class is LegacyGuardedModelIterable:
            clone = queryset._chain()
            clone._iterable_class = ModelIterable
            return clone
        return queryset
    if mode is LegacyFetchMode.PEERS:
        if queryset._iterable_class is LegacyGuardedModelIterable:
            queryset = queryset._chain()
            queryset._iterable_class = ModelIterable
        peer_relations = _legacy_peer_relations(queryset, relations)
        if not peer_relations:
            return queryset
        return queryset.prefetch_related(*peer_relations)
    if queryset._fields is not None:
        # values() and values_list() return plain data, so they cannot trigger
        # lazy model-field access after evaluation.
        return queryset
    if not issubclass(queryset.model, FetchGuardModelMixin):
        raise ImproperlyConfigured(
            "Strict mode on Django 4.2-6.0 requires FetchGuardModelMixin "
            "before django.db.models.Model in the model's base classes."
        )
    clone = queryset._chain()
    clone._iterable_class = LegacyGuardedModelIterable
    return clone


def guard_queryset(queryset, mode="raise", *, relations=()):
    """Return *queryset* configured with a cross-version fetch policy."""
    if not isinstance(queryset, models.QuerySet):
        raise TypeError("guard_queryset() requires a Django QuerySet.")
    resolved = resolve_fetch_mode(mode)
    if HAS_NATIVE_FETCH_MODES:
        guarded = queryset.fetch_mode(resolved)
        if relations and resolved is models.FETCH_PEERS:
            return guarded.prefetch_related(*relations)
        return guarded
    return _legacy_guard_queryset(queryset, resolved, relations)


def with_diagnostic_context(queryset, context):
    """Return a queryset that adds framework context to model instances."""
    if not isinstance(queryset, models.QuerySet):
        raise TypeError("with_diagnostic_context() requires a Django QuerySet.")
    if queryset._fields is not None:
        return queryset
    clone = queryset._chain()
    clone.query._fetch_guard_context = context
    if clone._iterable_class is ModelIterable:
        clone._iterable_class = DiagnosticModelIterable
    return clone
