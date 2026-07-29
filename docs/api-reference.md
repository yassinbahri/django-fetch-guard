# API reference

The import package is `fetch_guard`; the distribution name is
`django-fetch-guard`.

## `GuardedManager`

```python
from fetch_guard import GuardedManager

objects = GuardedManager(default_mode="raise")
```

`default_mode` accepts a supported mode name or a native Django 6.1 fetch-mode
object. When omitted, the manager reads `FETCH_GUARD["DEFAULT_MODE"]`, which
defaults to `"raise"`.

The manager exposes all methods from `FetchGuardQuerySet`.

## `FetchGuardQuerySet`

### `with_fetch_guard(mode="raise", *, relations=())`

Return a cloned queryset using the requested policy.

```python
Book.objects.with_fetch_guard("peers", relations=("author",))
```

### `strict()`

Apply the strict/raise policy. Unloaded supported fields and relations raise
`FieldFetchBlocked` when accessed.

### `fetch_peers(*relations)`

Apply peer fetching. With relation names, those paths are prefetched explicitly:

```python
Book.objects.fetch_peers("author", "publisher")
```

Without names, Django 6.1 uses native on-demand peer fetching. Django 4.2–6.0
prefetches direct forward foreign-key and one-to-one relations.

### `fetch_one()` and `normal()`

Restore traditional one-instance-at-a-time lazy fetching. The methods are
aliases.

## `guard_queryset(queryset, mode="raise", *, relations=())`

Apply a policy to a queryset from an existing manager:

```python
from fetch_guard import guard_queryset

queryset = guard_queryset(Book.objects.published(), "raise")
```

The function returns a clone when the policy requires one. Treat the input
queryset as unchanged.

## `resolve_fetch_mode(mode)`

Validate and resolve a friendly name. Canonical names are:

- `one`
- `peers`
- `raise`

Accepted aliases are `normal`, `strict`, `fetch_one`, and `fetch_peers`.
Hyphens are normalized to underscores. Invalid strings raise `ValueError`; an
unsupported type raises `TypeError`.

## `FetchGuardModelMixin`

```python
from fetch_guard import FetchGuardModelMixin


class Book(FetchGuardModelMixin, models.Model):
    ...
```

The mixin enables compatibility strict mode on Django 4.2–6.0. Put it before
`models.Model`. It adds no fields, tables, or migrations and remains inert for
ordinary instances and native Django 6.1 policies.

## `FieldFetchBlocked`

Import this portable exception from `fetch_guard`:

```python
from fetch_guard import FieldFetchBlocked
```

It aliases Django's native exception on Django 6.1 and the package compatibility
exception on older Django versions.

## `FetchGuardMixin` for DRF

```python
from fetch_guard.drf import FetchGuardMixin
```

Public attributes and methods:

- `fetch_guard_mode`: single default policy; defaults to `"raise"`.
- `fetch_guard`: optional action-to-policy dictionary.
- `get_fetch_guard_mode()`: resolve the current action's policy.
- `get_queryset()`: apply the resolved policy after calling `super()`.

See the [DRF guide](drf.md) for complete examples.

## Settings and system checks

```python
FETCH_GUARD = {
    "DEFAULT_MODE": "raise",
}
```

When `fetch_guard` is installed, Django registers the `fetch_guard` check tag:

```console
python manage.py check --tag fetch_guard
```

Check IDs:

- `fetch_guard.E001`: `FETCH_GUARD` is not a dictionary.
- `fetch_guard.E002`: `DEFAULT_MODE` is invalid.

