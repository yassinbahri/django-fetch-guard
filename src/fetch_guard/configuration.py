from django.conf import settings


DEFAULTS = {"DEFAULT_MODE": "raise"}


def get_fetch_guard_setting(name):
    configured = getattr(settings, "FETCH_GUARD", {})
    if not isinstance(configured, dict):
        return DEFAULTS[name]
    return configured.get(name, DEFAULTS[name])

