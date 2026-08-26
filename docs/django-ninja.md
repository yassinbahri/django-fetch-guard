# Django Ninja integration

Django Ninja serializes ORM objects after your view function returns. Apply the
fetch policy before returning the queryset or model instances so schema
serialization cannot hide accidental database access.

`django-fetch-guard` does not require Django Ninja. The examples below use only
the core queryset API, so the package remains lightweight for projects that use
DRF, plain Django views, or service-layer serialization.

## List endpoints

Use `fetch_peers()` when a response schema reads a direct relation for every
row.

```python
from ninja import Router, Schema

from .models import Book

router = Router()


class AuthorOut(Schema):
    name: str


class BookOut(Schema):
    title: str
    author: AuthorOut


@router.get("/books", response=list[BookOut])
def list_books(request):
    return Book.objects.fetch_peers("author").order_by("id")
```

For Django 4.2 through 6.0, passing `"author"` is important because the
compatibility engine needs to know which relations to batch. Django 6.1 can use
native on-demand peer fetching, but explicit relation names are still clearer
and portable.

## Detail endpoints

Use `strict()` once the queryset is complete. If the schema tries to read a
relation that was not loaded, `FieldFetchBlocked` is raised instead of silently
issuing another query.

```python
from django.shortcuts import get_object_or_404


@router.get("/books/{book_id}", response=BookOut)
def get_book(request, book_id: int):
    return get_object_or_404(
        Book.objects.select_related("author").strict(),
        pk=book_id,
    )
```

## Handling blocked fetches

Use the portable package exception if you want to convert strict-mode failures
into API errors during development.

```python
from fetch_guard import FieldFetchBlocked
from ninja.errors import HttpError


@router.get("/books/{book_id}", response=BookOut)
def get_book(request, book_id: int):
    try:
        return get_object_or_404(Book.objects.strict(), pk=book_id)
    except FieldFetchBlocked as exc:
        raise HttpError(500, f"Incomplete queryset plan: {exc}") from exc
```

In production, prefer fixing the queryset with `select_related()` or
`prefetch_related()` over catching the exception.

## Nested relations and data loaders

For nested to-many data, use Django's normal `prefetch_related()` or your
GraphQL/API data-loader layer. `django-fetch-guard` is intentionally focused on
making ORM fetch policy visible; it does not replace a data-loader architecture.

```python
@router.get("/authors", response=list[AuthorOut])
def list_authors(request):
    return Author.objects.prefetch_related("book_set").order_by("id")
```

## Testing the endpoint plan

The simplest test is to serialize the objects through the same code path your
schema uses and assert that strict mode either succeeds with a complete queryset
or raises when the plan is incomplete.

```python
import pytest

from fetch_guard import FieldFetchBlocked


@pytest.mark.django_db
def test_book_detail_queryset_is_complete():
    book = Book.objects.select_related("author").strict().get()
    assert book.author.name


@pytest.mark.django_db
def test_book_detail_queryset_blocks_hidden_fetches():
    book = Book.objects.strict().get()
    with pytest.raises(FieldFetchBlocked):
        book.author.name
```
