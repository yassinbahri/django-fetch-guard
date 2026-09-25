# Actionable diagnostics

Strict mode raises `fetch_guard.FieldFetchBlocked` when application code tries
to load data that the queryset did not explicitly prepare. Models using
`FetchGuardModelMixin` enrich that exception with a `FetchDiagnostic` object.

```python
from fetch_guard import FieldFetchBlocked, get_fetch_diagnostic

book = Book.objects.strict().first()

try:
    print(book.author.name)
except FieldFetchBlocked as exc:
    diagnostic = get_fetch_diagnostic(exc)
    print(diagnostic.format())
```

Example output:

```text
Implicit database fetch blocked
Model: library.Book
Field: author
Fetch type: forward_foreign_key
Location: library.serializers.get_author:24
Suggested fix: queryset.select_related("author")
```

## Structured output

`diagnostic.as_dict()` returns JSON-serializable values suitable for test
failures and structured logs:

```python
{
    "model": "library.Book",
    "field": "author",
    "fetch_type": "forward_foreign_key",
    "policy": "raise",
    "django_version": "6.1",
    "suggestion": 'queryset.select_related("author")',
    "call_site": {
        "module": "library.serializers",
        "function": "get_author",
        "line": 24,
    },
}
```

Call-site capture deliberately excludes source lines, local variables, and
absolute file paths. This keeps the diagnostic useful without copying request
data or deployment paths into logs.

## Fetch categories

Diagnostics distinguish these access patterns:

- `forward_foreign_key`
- `forward_one_to_one`
- `reverse_one_to_one`
- `reverse_one_to_many`
- `many_to_many`
- `deferred_field`
- `relation` as a safe fallback for an unclassified relation

Forward single-object relations suggest `select_related()`. Collection
relations suggest `prefetch_related()`. Deferred scalar fields explain how to
adjust `only()` or `defer()`.

## Django REST Framework context

`FetchGuardMixin` adds the qualified view class, action, and configured
serializer class when available:

```python
diagnostic = get_fetch_diagnostic(exc)
print(diagnostic.context.view)
print(diagnostic.context.action)
print(diagnostic.context.serializer)
```

All context values are names, not serializer data or request contents.

## Compatibility

- Django 6.1 keeps Django's native `FieldFetchBlocked` exception type and adds
  the diagnostic to it.
- Django 4.2 through 6.0 uses the package's portable exception and attaches the
  same diagnostic shape.
- `get_fetch_diagnostic()` returns `None` when an exception cannot be enriched,
  such as when native mode is used on a model without `FetchGuardModelMixin`.
