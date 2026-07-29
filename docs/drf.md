# Django REST Framework integration

Install the DRF extra:

```console
python -m pip install "django-fetch-guard[drf]"
```

Put `FetchGuardMixin` before the DRF view class so its `get_queryset()` method
runs:

```python
from fetch_guard.drf import FetchGuardMixin
from rest_framework.viewsets import ModelViewSet


class BookViewSet(FetchGuardMixin, ModelViewSet):
    queryset = Book.objects.select_related("author")
    serializer_class = BookSerializer
    fetch_guard_mode = "raise"
```

## Policies by action

```python
class BookViewSet(FetchGuardMixin, ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    fetch_guard = {
        "list": "peers",
        "retrieve": "raise",
        "default": "raise",
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "retrieve":
            queryset = queryset.select_related("author")
        return queryset
```

Resolution order is:

1. Exact action entry in `fetch_guard`.
2. The `default` entry.
3. `fetch_guard_mode`, whose default is `"raise"`.

Use `None` for an action that should remain unchanged:

```python
fetch_guard = {
    "list": "peers",
    "export": None,
}
```

An invalid mode or non-dictionary policy raises Django's
`ImproperlyConfigured` during queryset construction.

## Serializer guidance

Strict mode is most valuable when serializer fields traverse relations:

```python
class BookSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.name", read_only=True)
```

Pair that field with an explicit view queryset:

```python
queryset = Book.objects.select_related("author")
```

For nested to-many serializers, use `prefetch_related()` because related
manager queries are not blocked by fetch modes.

