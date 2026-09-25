from django.core.exceptions import FieldDoesNotExist

from .diagnostics import capture_call_site, diagnostic_for_access
from .exceptions import FieldFetchBlocked, attach_fetch_diagnostic


def _blocked_fetch(instance, name, message):
    diagnostic = diagnostic_for_access(
        instance,
        name,
        call_site=capture_call_site(),
    )
    if diagnostic is not None:
        message = f"{message}\nSuggested fix: {diagnostic.suggestion}"
    return attach_fetch_diagnostic(FieldFetchBlocked(message), diagnostic)


class FetchGuardModelMixin:
    """Block unloaded field access for strict querysets on Django before 6.1.

    Put this mixin before ``django.db.models.Model`` in a model's base classes.
    It is inert unless an instance came from a legacy strict queryset.
    """

    def __getattribute__(self, name):
        if not name.startswith("_"):
            state = object.__getattribute__(self, "__dict__")
            if state.get("_fetch_guard_legacy_mode") == "raise":
                meta = object.__getattribute__(self, "_meta")
                try:
                    field = meta.get_field(name)
                except FieldDoesNotExist:
                    field = None

                if field is not None:
                    if name in self.get_deferred_fields():
                        raise _blocked_fetch(
                            self,
                            name,
                            f"Fetching deferred field {meta.label}.{name} was blocked.",
                        )
                    relation_fetch = field.is_relation and (
                        field.many_to_one or field.one_to_one
                    ) and name == field.name
                    if relation_fetch and not field.is_cached(self):
                        raise _blocked_fetch(
                            self,
                            name,
                            f"Fetching relation {meta.label}.{name} was blocked.",
                        )
        try:
            return super().__getattribute__(name)
        except FieldFetchBlocked as exc:
            if getattr(exc, "fetch_guard_diagnostic", None) is None:
                diagnostic = diagnostic_for_access(
                    self,
                    name,
                    call_site=capture_call_site(),
                )
                attach_fetch_diagnostic(exc, diagnostic)
                if diagnostic is not None:
                    exc.args = (f"{exc}\nSuggested fix: {diagnostic.suggestion}",)
            raise
