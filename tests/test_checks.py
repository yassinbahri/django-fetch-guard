from django.test import override_settings

from fetch_guard.checks import check_fetch_guard_settings


@override_settings(FETCH_GUARD="raise")
def test_settings_must_be_dictionary():
    errors = check_fetch_guard_settings(None)
    assert [error.id for error in errors] == ["fetch_guard.E001"]


@override_settings(FETCH_GUARD={"DEFAULT_MODE": "invalid"})
def test_default_mode_must_be_valid():
    errors = check_fetch_guard_settings(None)
    assert [error.id for error in errors] == ["fetch_guard.E002"]


@override_settings(FETCH_GUARD={"DEFAULT_MODE": "peers"})
def test_valid_settings_pass():
    assert check_fetch_guard_settings(None) == []

