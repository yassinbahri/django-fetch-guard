# Django admin integration

Django admin changelists and detail pages often touch model fields and
relations indirectly through `list_display`, filters, search fields, form
widgets, and `readonly_fields`. When you enable strict fetch policies, make the
admin queryset explicit about everything the page will read.

## Minimal model

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

`FetchGuardModelMixin` keeps strict blocking portable on Django 4.2 through
6.0. It is inert on Django 6.1 when native fetch modes perform the blocking.

## Changelist with an explicit strict queryset

Use `list_select_related` for relations that the changelist always displays,
then return a strict queryset from `get_queryset()`.

```python
from django.contrib import admin

from .models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author")
    list_select_related = ("author",)

    def get_queryset(self, request):
        return super().get_queryset(request).strict()
```

With that plan, the admin can render `book.author` without performing one lazy
query per row. If `list_select_related` is removed later, strict mode blocks the
unplanned relation access instead of silently adding an N+1 query pattern.

The same queryset pattern is covered by
`tests/test_managers.py::test_explicit_select_related_satisfies_strict_mode`.

## Detail pages and readonly fields

Detail pages can also access relations through `readonly_fields`, custom form
fields, or display methods. Include those relations in the queryset before
calling `strict()`.

```python
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    readonly_fields = ("author_name",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("author").strict()

    @admin.display(description="Author")
    def author_name(self, obj):
        return obj.author.name
```

## Peer fetching when admin access is conditional

Use `fetch_peers()` when the admin may or may not touch a relation, but you
still want the first relation access to batch across the queryset.

```python
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author")

    def get_queryset(self, request):
        return super().get_queryset(request).fetch_peers("author")
```

Naming the relation keeps the behavior explicit and consistent across supported
Django versions.

## When admin may fetch more than expected

Admin code can read fields outside the obvious `list_display` path. Check these
places before switching a model admin to strict mode:

- `list_display` methods and properties
- `readonly_fields`
- `search_fields`
- `list_filter`
- custom form fields and widgets
- custom `get_object()`, `get_form()`, or `get_readonly_fields()` logic

If a field or relation is legitimately needed, load it in `get_queryset()`.
If lazy loading is intentional for a specific admin view, use `.normal()` for
that queryset instead of strict mode.
