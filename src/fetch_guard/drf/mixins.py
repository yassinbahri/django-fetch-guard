from django.core.exceptions import ImproperlyConfigured

from fetch_guard.modes import guard_queryset


class FetchGuardMixin:
    """Apply a fetch mode to a DRF view's queryset, optionally per action."""

    fetch_guard_mode = "raise"
    fetch_guard = None

    def get_fetch_guard_mode(self):
        policy = self.fetch_guard
        if policy is None:
            return self.fetch_guard_mode
        if not isinstance(policy, dict):
            raise ImproperlyConfigured(
                f"{type(self).__name__}.fetch_guard must be a dictionary or None."
            )
        action = getattr(self, "action", None)
        if action in policy:
            return policy[action]
        return policy.get("default", self.fetch_guard_mode)

    def get_queryset(self):
        queryset = super().get_queryset()
        mode = self.get_fetch_guard_mode()
        if mode is None:
            return queryset
        try:
            return guard_queryset(queryset, mode)
        except (TypeError, ValueError) as exc:
            raise ImproperlyConfigured(
                f"Invalid fetch guard policy on {type(self).__name__}: {exc}"
            ) from exc

