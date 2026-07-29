<p align="center">
  <img src="https://raw.githubusercontent.com/yassinbahri/django-fetch-guard/main/docs/assets/hero.png" alt="A shield transforms many scattered database query paths into two controlled paths" width="100%">
</p>

<h1 align="center">django-fetch-guard</h1>

<p align="center">
  <strong>Make accidental ORM queries impossible—or batch them automatically.</strong>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white"></a>
  <a href="https://github.com/yassinbahri/django-fetch-guard/blob/main/docs/django-compatibility.md"><img alt="Django 4.2–6.1" src="https://img.shields.io/badge/Django-4.2%E2%80%936.1-0C4B33?logo=django&logoColor=white"></a>
  <a href="https://github.com/yassinbahri/django-fetch-guard/blob/main/LICENSE"><img alt="License MIT" src="https://img.shields.io/badge/License-MIT-35c978"></a>
  <a href="https://github.com/yassinbahri/django-fetch-guard/blob/main/CHANGELOG.md"><img alt="Status alpha" src="https://img.shields.io/badge/Status-alpha-f0b45d"></a>
</p>

`django-fetch-guard` gives Django querysets an explicit fetch policy. Use
`peers` to collapse common N+1 patterns into batched queries, or use `strict`
to fail immediately when code touches a field or relation that was not loaded
intentionally.

It uses Django 6.1's native fetch modes when available and provides a carefully
scoped compatibility engine for Django 4.2 through 6.0.

<p align="center">
  <img src="https://raw.githubusercontent.com/yassinbahri/django-fetch-guard/main/docs/assets/fetch-modes.svg" alt="Normal mode performs one plus N queries, peers performs two, and strict uses one explicit query or blocks the access" width="100%">
</p>

## Why this exists

This innocent loop can perform 101 queries for 100 books:

```python
books = Book.objects.all()  # 1 query

for book in books:
    print(book.author.name)  # N more queries
```

Fetch guard lets the queryset state its contract:

```python
# Batch related authors: usually 2 queries in total.
books = Book.objects.fetch_peers()

# Or require an explicit plan: 1 joined query, no hidden fetching allowed.
books = Book.objects.select_related("author").strict()
```

That contract follows the queryset into serializers, views, templates, and
service functions instead of relying on every caller to remember a query-count
assertion.

## Compatibility

| Django version | `fetch_peers()` | `strict()` |
| --- | --- | --- |
| 6.1 | Native on-demand `FETCH_PEERS` | Native `RAISE` mode |
| 4.2–6.0 | Prefetch direct or named relations | Compatibility model mixin |

The public API is the same across supported versions. See the
[compatibility guide](docs/django-compatibility.md) for exact differences and
honest limitations.

## Installation

After the first release is published:

```console
python -m pip install django-fetch-guard
```

For Django REST Framework integration:

```console
python -m pip install "django-fetch-guard[drf]"
```

Install the current development version directly from GitHub:

```console
python -m pip install "django-fetch-guard @ git+https://github.com/yassinbahri/django-fetch-guard.git"
```

Contributors should use the editable setup in [CONTRIBUTING.md](CONTRIBUTING.md).

## Five-minute setup

### 1. Add the mixin and manager

```python
from django.db import models
from fetch_guard import FetchGuardModelMixin, GuardedManager


class Author(models.Model):
    name = models.CharField(max_length=100)


class Book(FetchGuardModelMixin, models.Model):
    title = models.CharField(max_length=150)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    objects = GuardedManager(default_mode="raise")
```

The mixin is needed only by the Django 4.2–6.0 strict compatibility engine, but
keeping it makes the model portable. It adds no database fields and requires no
migration.

### 2. Choose a mode

```python
Book.objects.strict()       # Block an unloaded field or relation.
Book.objects.fetch_peers()  # Batch missing direct relations.
Book.objects.normal()       # Restore traditional lazy loading.
```

Use explicit relations for consistent eager behavior on every version:

```python
Book.objects.fetch_peers("author")
```

### 3. Make strict querysets complete

```python
books = Book.objects.select_related("author").strict()

for book in books:
    print(book.author.name)  # Already loaded; no extra query.
```

Without `select_related("author")`, the relation access raises the portable
exception:

```python
from fetch_guard import FieldFetchBlocked
```

Import this package exception rather than Django's exception directly. It maps
to Django's native class on 6.1 and the compatibility class on older versions.

## Project-wide defaults and checks

Add the application when you want settings validation:

```python
INSTALLED_APPS = [
    # ...
    "fetch_guard",
]

FETCH_GUARD = {
    "DEFAULT_MODE": "raise",
}
```

Then the manager can inherit the project setting:

```python
objects = GuardedManager()
```

Validate it with:

```console
python manage.py check --tag fetch_guard
```

## Guard any queryset

An existing manager can remain unchanged:

```python
from fetch_guard import guard_queryset

books = guard_queryset(Book.objects.filter(is_published=True), "raise")
```

For custom manager/queryset composition, see the
[getting-started guide](docs/getting-started.md#existing-custom-managers).

## Django REST Framework

```python
from fetch_guard.drf import FetchGuardMixin
from rest_framework.viewsets import ModelViewSet


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

Read the [DRF guide](docs/drf.md) for resolution order, opt-outs, nested
serializers, and queryset planning.

## Pytest

The package registers a focused fixture:

```python
import pytest
from fetch_guard import FieldFetchBlocked


@pytest.mark.django_db
def test_book_serializer(fetch_guard):
    book = fetch_guard.strict(Book.objects.all()).first()

    with pytest.raises(FieldFetchBlocked):
        serialize_book(book)
```

The fixture affects only the queryset passed to it; it does not monkey-patch
Django globally. See the [testing guide](docs/testing.md).

## Verified integration behavior

The test suite includes a minimal Django application and real HTTP server
coverage. It measures the same serialization path under every policy:

| Policy | Queries for two books | Result |
| --- | ---: | --- |
| Normal | 3 | Demonstrates N+1 |
| Peers | 2 | Authors loaded in one batch |
| Strict with `select_related()` | 1 | Explicit query plan succeeds |
| Strict without related loading | — | Fetch is blocked |

Run all unit and integration tests with:

```console
python -m pip install -e ".[test]"
python -m pytest
```

## Documentation

- [Getting started and core API](docs/getting-started.md)
- [API reference](docs/api-reference.md)
- [Django compatibility and limitations](docs/django-compatibility.md)
- [Django REST Framework](docs/drf.md)
- [Testing](docs/testing.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Contributing](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Changelog](CHANGELOG.md)

## Current status

`0.1.0a1` is an alpha. The core API, legacy compatibility engine, DRF mixin,
pytest fixture, system check, and cross-version CI matrix are implemented. The
tests include Django's request client and a live HTTP server.
Rich call-site diagnostics and production audit sampling are planned for later
releases.

## License

MIT
