from django.core.exceptions import FieldDoesNotExist

from .exceptions import FieldFetchBlocked


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
                        raise FieldFetchBlocked(
                            f"Fetching deferred field {meta.label}.{name} was blocked."
                        )
                    relation_fetch = field.is_relation and (
                        field.many_to_one or field.one_to_one
                    ) and name == field.name
                    if relation_fetch and not field.is_cached(self):
                        raise FieldFetchBlocked(
                            f"Fetching relation {meta.label}.{name} was blocked."
                        )
        return super().__getattribute__(name)
