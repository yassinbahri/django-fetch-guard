from django.apps import AppConfig


class FetchGuardConfig(AppConfig):
    name = "fetch_guard"
    verbose_name = "Django Fetch Guard"

    def ready(self):
        from . import checks  # noqa: F401

