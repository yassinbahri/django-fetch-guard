# Testing with django-fetch-guard

Install test dependencies:

```console
python -m pip install "django-fetch-guard[test]"
```

The installed package registers a `fetch_guard` pytest fixture automatically:

```python
import pytest
from fetch_guard import FieldFetchBlocked


@pytest.mark.django_db
def test_serializer_declares_author(fetch_guard):
    queryset = fetch_guard.strict(Book.objects.all())
    book = queryset.first()

    with pytest.raises(FieldFetchBlocked):
        serialize_book(book)
```

Test the corrected query plan:

```python
@pytest.mark.django_db
def test_serializer_has_no_lazy_fetch(fetch_guard, django_assert_num_queries):
    book = fetch_guard.strict(
        Book.objects.select_related("author")
    ).first()

    with django_assert_num_queries(0):
        assert serialize_book(book)["author"] == book.author.name
```

The fixture methods are:

- `fetch_guard.strict(queryset)`
- `fetch_guard.peers(queryset)`
- `fetch_guard.normal(queryset)`
- `fetch_guard(queryset, mode)`

The fixture transforms only the supplied queryset. It does not monkey-patch
Django globally, so tests can run concurrently without sharing policy state.

## Package test commands

```console
python -m pytest
```

The suite tests manager, queryset, DRF, system-check, and fixture behavior. Its
integration tests cover both Django's test client and `LiveServerTestCase`.
The latter starts an actual HTTP server on an ephemeral TCP port, sends network
requests, and verifies measured query counts:

| Endpoint | Expected queries for two books |
| --- | ---: |
| `/books/normal/` | 3 |
| `/books/peers/` | 2 |
| `/books/strict/` | 1 |
| `/books/strict-broken/` | blocked |
