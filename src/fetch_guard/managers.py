from django.db import models

from .configuration import get_fetch_guard_setting
from .modes import guard_queryset


class FetchGuardQuerySet(models.QuerySet):
    """A QuerySet with named helpers for Django's native fetch modes."""

    def with_fetch_guard(self, mode="raise", *, relations=()):
        return guard_queryset(self, mode, relations=relations)

    def strict(self):
        return self.with_fetch_guard("raise")

    def fetch_peers(self, *relations):
        return self.with_fetch_guard("peers", relations=relations)

    def fetch_one(self):
        return self.with_fetch_guard("one")

    def normal(self):
        return self.fetch_one()


_GuardedManagerBase = models.Manager.from_queryset(FetchGuardQuerySet)


class GuardedManager(_GuardedManagerBase):
    """Manager that applies a fetch policy to every base queryset."""

    def __init__(self, *args, default_mode=None, **kwargs):
        self.default_mode = default_mode
        super().__init__(*args, **kwargs)

    def get_default_mode(self):
        if self.default_mode is not None:
            return self.default_mode
        return get_fetch_guard_setting("DEFAULT_MODE")

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.with_fetch_guard(self.get_default_mode())
