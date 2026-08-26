# Django admin integration

`django-fetch-guard` can make Django admin query plans explicit, but admin pages
also read model fields and relations for search, filters, ordering,
`list_display`, forms, widgets, and custom methods. Start with one model admin,
make its queryset complete, then enable strict mode.

## Changelists

Use `list_select_related` for ordinary foreign keys shown in `list_display`,
then return a strict queryset.

```python
from django.contrib import admin

from .models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["title", "author_name"]
    list_select_related = ["author"]

    def get_queryset(self, request):
        return super().get_queryset(request).strict()

    @admin.display(ordering="author__name", description="Author")
    def author_name(self, obj):
        return obj.author.name
```

This keeps the changelist explicit:

- `list_select_related = ["author"]` loads the relation.
- `.strict()` blocks later accidental lazy relation access.
- `author_name()` can use `obj.author.name` without another database query.

## Detail pages

For detail pages, preload relations used by readonly fields, custom form
widgets, or inline decisions.

```python
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    readonly_fields = ["author_name"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("author").strict()

    @admin.display(description="Author")
    def author_name(self, obj):
        return obj.author.name
```

## Peer fetching

Use `fetch_peers()` when you want batching instead of blocking. This is useful
while investigating a large admin page because it reduces common N+1 patterns
without forcing every relation to be listed immediately.

```python
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["title", "author_name"]

    def get_queryset(self, request):
        return super().get_queryset(request).fetch_peers("author")

    @admin.display(ordering="author__name", description="Author")
    def author_name(self, obj):
        return obj.author.name
```

On Django 4.2 through 6.0, pass relation names such as `"author"` to
`fetch_peers()` for portable batching. On Django 6.1, native fetch modes can
also batch unloaded direct relations on demand.

## Practical checklist

- Add `FetchGuardModelMixin` to models that must support strict mode on Django
  4.2 through 6.0.
- Prefer `list_select_related` for relations used in `list_display`.
- Use `select_related()` in `get_queryset()` for detail-page readonly fields.
- Use `prefetch_related()` for reverse and many-to-many relations.
- If strict mode blocks admin internals, make the relevant field explicit or
  use `fetch_peers()` while you narrow the queryset plan.
