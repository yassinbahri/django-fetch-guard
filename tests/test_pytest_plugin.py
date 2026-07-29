import pytest

from fetch_guard import FieldFetchBlocked
from tests.models import Author, Book


@pytest.mark.django_db
def test_fetch_guard_fixture(fetch_guard):
    author = Author.objects.create(name="James Baldwin")
    Book.objects.create(title="Giovanni's Room", author=author)
    book = fetch_guard.strict(Book.objects.all()).first()
    with pytest.raises(FieldFetchBlocked):
        _ = book.author
