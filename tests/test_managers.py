import pytest

from fetch_guard import FieldFetchBlocked, FetchType, get_fetch_diagnostic
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
    with pytest.raises(FieldFetchBlocked) as caught:
        _ = book.author

    diagnostic = get_fetch_diagnostic(caught.value)
    assert diagnostic.model == "tests.Book"
    assert diagnostic.field == "author"
    assert diagnostic.fetch_type is FetchType.FORWARD_FOREIGN_KEY
    assert diagnostic.suggestion == 'queryset.select_related("author")'
    assert diagnostic.call_site.module == __name__
    assert "Suggested fix" in str(caught.value)


def test_strict_diagnoses_deferred_field(books):
    book = Book.objects.only("id").strict().first()

    with pytest.raises(FieldFetchBlocked) as caught:
        _ = book.title

    diagnostic = get_fetch_diagnostic(caught.value)
    assert diagnostic.field == "title"
    assert diagnostic.fetch_type is FetchType.DEFERRED_FIELD
    assert "only()" in diagnostic.suggestion


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


def test_admin_documented_strict_queryset_pattern(books, django_assert_num_queries):
    book = Book.objects.select_related("author").strict().get(
        title="A Wizard of Earthsea"
    )

    with django_assert_num_queries(0):
        assert book.author.name == "Ursula K. Le Guin"


def test_ninja_documented_fetch_peers_queryset_pattern(
    books, django_assert_num_queries
):
    with django_assert_num_queries(2):
        payload = [
            {"title": book.title, "author": {"name": book.author.name}}
            for book in Book.objects.fetch_peers("author").order_by("pk")
        ]

    assert payload == [
        {"title": "A Wizard of Earthsea", "author": {"name": "Ursula K. Le Guin"}},
        {"title": "Kindred", "author": {"name": "Octavia E. Butler"}},
    ]
