import pytest

from .modes import guard_queryset


class FetchGuardFixture:
    """Apply fetch policies in tests without mutating global state."""

    def __call__(self, queryset, mode="raise"):
        return guard_queryset(queryset, mode)

    def strict(self, queryset):
        return guard_queryset(queryset, "raise")

    def peers(self, queryset):
        return guard_queryset(queryset, "peers")

    def normal(self, queryset):
        return guard_queryset(queryset, "one")


@pytest.fixture
def fetch_guard():
    return FetchGuardFixture()

