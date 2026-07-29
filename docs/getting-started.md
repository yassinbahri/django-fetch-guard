# Getting started

## 1. Install

After the package is published:

```console
python -m pip install django-fetch-guard
```

Install the current development version directly from GitHub:

```console
python -m pip install "django-fetch-guard @ git+https://github.com/yassinbahri/django-fetch-guard.git"
```

For Django REST Framework support:

```console
python -m pip install "django-fetch-guard[drf]"
```

## 2. Add the model API

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

`FetchGuardModelMixin` is required for strict blocking on Django 4.2–6.0. On
Django 6.1, native fetch modes perform the blocking and the mixin stays inert.
Putting it on the model keeps the same code portable across all supported
Django versions.

No database migration is created by adding the mixin or manager.

## 3. Choose a policy

### Strict: make query plans explicit

```python
books = Book.objects.select_related("author").strict()

for book in books:
    print(book.author.name)
```

If `select_related("author")` is accidentally removed, accessing
`book.author` raises `fetch_guard.FieldFetchBlocked` instead of silently
running one query per book.

### Peers: batch related objects

```python
books = Book.objects.fetch_peers()

for book in books:
    print(book.author.name)
```

On Django 6.1, the first `author` access triggers one batch query for the peer
books. On Django 4.2–6.0, direct forward foreign keys and one-to-one relations
are prefetched when the queryset is evaluated.

Name relations when you want an identical explicit plan on every version:

```python
books = Book.objects.fetch_peers("author")
```

### Normal: use traditional Django behavior

```python
books = Book.objects.normal()
```

This is useful for code that intentionally permits lazy loading, even when the
manager default is strict.

## 4. Configure a project default

Adding `fetch_guard` to `INSTALLED_APPS` enables configuration checks:

```python
INSTALLED_APPS = [
    # ...
    "fetch_guard",
]

FETCH_GUARD = {
    "DEFAULT_MODE": "raise",
}
```

When `GuardedManager()` does not receive `default_mode`, it reads this setting:

```python
objects = GuardedManager()
```

Validate the configuration with:

```console
python manage.py check --tag fetch_guard
```

## 5. Guard an existing queryset

You do not need a guarded manager on every model:

```python
from fetch_guard import guard_queryset

queryset = guard_queryset(Book.objects.all(), "raise")
```

On Django 4.2–6.0, the model still needs `FetchGuardModelMixin` for strict
mode. `one` and `peers` work without it.

## Existing custom managers

Preserve custom queryset methods by building on `FetchGuardQuerySet`:

```python
from fetch_guard import FetchGuardQuerySet, GuardedManager


class BookQuerySet(FetchGuardQuerySet):
    def published(self):
        return self.filter(is_published=True)


BookManager = GuardedManager.from_queryset(BookQuerySet)


class Book(FetchGuardModelMixin, models.Model):
    objects = BookManager(default_mode="raise")
```

## Exceptions

Always import the portable exception from this package:

```python
from fetch_guard import FieldFetchBlocked

try:
    render_books()
except FieldFetchBlocked as exc:
    logger.exception("Unexpected ORM fetch: %s", exc)
```

It aliases Django's native exception on 6.1 and the compatibility exception on
older releases.
