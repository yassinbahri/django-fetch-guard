import pytest

from fetch_guard import FieldFetchBlocked
from tests.models import Author, Book, StrictBook


@pytest.fixture
def books(db):
    first = Author.objects.create(name="Ursula K. Le Guin")
    second = Author.objects.create(name="Octavia E. Butler")
    Book.objects.create(title="A Wizard of Earthsea", author=first)
    Book.objects.create(title="Kindred", author=second)
    StrictBook.objects.create(title="The Dispossessed", author=first)


def test_fetch_peers_reduces_n_plus_one_to_two_queries(books, django_assert_num_queries):
    with django_assert_num_queries(2):
        result = list(Book.objects.fetch_peers().order_by("pk"))
        assert [book.author.name for book in result] == [
            "Ursula K. Le Guin",
            "Octavia E. Butler",
        ]


def test_strict_blocks_unfetched_relation(books):
    book = Book.objects.strict().first()
    with pytest.raises(FieldFetchBlocked):
        _ = book.author


def test_explicit_select_related_satisfies_strict_mode(books, django_assert_num_queries):
    book = Book.objects.select_related("author").strict().first()
    with django_assert_num_queries(0):
        assert book.author.name == "Ursula K. Le Guin"


def test_manager_default_mode_is_applied(books):
    book = StrictBook.objects.first()
    with pytest.raises(FieldFetchBlocked):
        _ = book.author


def test_normal_overrides_strict_manager_default(books):
    book = StrictBook.objects.normal().first()
    assert book.author.name == "Ursula K. Le Guin"


def test_peers_overrides_strict_manager_default(books, django_assert_num_queries):
    with django_assert_num_queries(2):
        result = list(StrictBook.objects.fetch_peers())
        assert result[0].author.name == "Ursula K. Le Guin"


def test_strict_allows_loaded_foreign_key_id(books, django_assert_num_queries):
    book = StrictBook.objects.first()
    with django_assert_num_queries(0):
        assert book.author_id is not None
