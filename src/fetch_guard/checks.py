from django.conf import settings
from django.core.checks import Error, register

from .modes import resolve_fetch_mode


FETCH_GUARD_TAG = "fetch_guard"


@register(FETCH_GUARD_TAG)
def check_fetch_guard_settings(app_configs, **kwargs):
    configured = getattr(settings, "FETCH_GUARD", {})

    if not isinstance(configured, dict):
        return [Error("FETCH_GUARD must be a dictionary.", id="fetch_guard.E001")]

    if "DEFAULT_MODE" not in configured:
        return []

    try:
        resolve_fetch_mode(configured["DEFAULT_MODE"])
    except (TypeError, ValueError) as exc:
        return [
            Error(
                str(exc),
                hint="Use 'one', 'peers', or 'raise'.",
                id="fetch_guard.E002",
            )
        ]
    return []

