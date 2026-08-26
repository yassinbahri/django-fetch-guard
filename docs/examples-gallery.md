# Hidden fetch examples gallery

This gallery shows the same failure pattern across common Django call sites:
an object is loaded without a fetch plan, then a related field is accessed later.
The fixed versions make the plan visible at the boundary where the object is
created.

The examples use only Django and the APIs provided by `django-fetch-guard`.
They apply unchanged to Django 4.2 through 6.0. Django 6.1 additionally has
native fetch modes, but explicit relation names remain the most portable and
readable option.

## 1. Plain service function

### Hidden fetch

```python
def book_labels():
    return [f"{book.title} — {book.author.name}" for book in Book.objects.all()]
```

### Fixed plan

```python
def book_labels():
    books = Book.objects.select_related("author").strict()
    return [f"{book.title} — {book.author.name}" for book in books]
```

`select_related()` makes the join explicit, while `strict()` turns a missed
relation into a visible `FieldFetchBlocked` error instead of another query.

## 2. Django template rendering

### Hidden fetch

```python
def book_list(request):
    return render(request, "books/list.html", {"books": Book.objects.all()})
```

```django
{% for book in books %}
  <li>{{ book.title }} — {{ book.author.name }}</li>
{% endfor %}
```

### Fixed plan

```python
def book_list(request):
    books = Book.objects.select_related("author").strict()
    return render(request, "books/list.html", {"books": books})
```

The template can stay simple because its relation access is now backed by the
view's explicit queryset plan.

## 3. DRF serializer field with `source`

### Hidden fetch

```python
class BookSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.name", read_only=True)

    class Meta:
        model = Book
        fields = ["title", "author_name"]


class BookViewSet(ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
```

### Fixed plan

```python
class BookViewSet(FetchGuardMixin, ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    fetch_guard = {"list": "peers", "retrieve": "raise", "default": "raise"}

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "retrieve":
            queryset = queryset.select_related("author")
        return queryset
```

For a list endpoint, `fetch_peers("author")` can batch direct relations. For a
detail endpoint, `select_related("author").strict()` is a useful hard contract.

## 4. Django Ninja response schema

### Hidden fetch

```python
@router.get("/books", response=list[BookOut])
def list_books(request):
    return Book.objects.all()
```

Ninja serializes the returned objects after the view exits, so the hidden query
is easy to miss during review.

### Fixed plan

```python
@router.get("/books", response=list[BookOut])
def list_books(request):
    return Book.objects.fetch_peers("author").order_by("id")
```

Use `select_related("author").strict()` for a detail response when the
relation must already be loaded and any incomplete plan should fail.

## 5. Django admin `list_display` method

### Hidden fetch

```python
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["title", "author_name"]

    @admin.display(description="Author")
    def author_name(self, obj):
        return obj.author.name
```

### Fixed plan

```python
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

`list_select_related` documents the admin relation dependency, and `strict()`
protects the changelist from future accidental lazy access.

## Version notes

| Django version | Recommended approach | Native fetch modes |
| --- | --- | --- |
| 4.2–6.0 | Name direct relations in `select_related()` or `fetch_peers()` | No |
| 6.1 | Explicit relation names remain recommended for clarity | Yes |

The examples intentionally avoid optional dependencies. Install the DRF or
Django Ninja integration only when the application already uses that framework.
