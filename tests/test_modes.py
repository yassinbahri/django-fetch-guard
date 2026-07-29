import pytest

from fetch_guard import guard_queryset, resolve_fetch_mode
from fetch_guard.modes import HAS_NATIVE_FETCH_MODES, LegacyGuardedModelIterable
from tests.models import Book


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("one", "one"),
        ("normal", "one"),
        ("peers", "peers"),
        ("fetch-peers", "peers"),
        ("raise", "raise"),
        ("strict", "raise"),
    ],
)
def test_resolve_fetch_mode(name, expected):
    assert resolve_fetch_mode(name) is resolve_fetch_mode(expected)


def test_invalid_mode_has_clear_error():
    with pytest.raises(ValueError, match="Unknown fetch guard mode"):
        resolve_fetch_mode("surprise")


def test_guard_queryset_rejects_non_queryset():
    with pytest.raises(TypeError, match="requires a Django QuerySet"):
        guard_queryset([], "raise")


@pytest.mark.django_db
def test_guard_queryset_applies_native_mode():
    queryset = guard_queryset(Book.objects.all(), "raise")
    if HAS_NATIVE_FETCH_MODES:
        assert queryset._fetch_mode is resolve_fetch_mode("raise")
    else:
        assert queryset._iterable_class is LegacyGuardedModelIterable
