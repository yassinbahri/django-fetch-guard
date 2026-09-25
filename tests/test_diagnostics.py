from fetch_guard import (
    FetchCallSite,
    FetchDiagnostic,
    FetchFrameworkContext,
    FetchType,
)
from fetch_guard.diagnostics import diagnostic_for_access
from tests.models import Book


def test_fetch_diagnostic_is_serializable():
    diagnostic = FetchDiagnostic(
        model="library.Book",
        field="author",
        fetch_type=FetchType.FORWARD_FOREIGN_KEY,
        policy="raise",
        django_version="6.1",
        suggestion='queryset.select_related("author")',
        call_site=FetchCallSite("library.serializers", "get_author", 24),
        context=FetchFrameworkContext(
            view="library.views.BookViewSet",
            action="list",
            serializer="library.serializers.BookSerializer",
        ),
    )

    assert diagnostic.as_dict() == {
        "model": "library.Book",
        "field": "author",
        "fetch_type": "forward_foreign_key",
        "policy": "raise",
        "django_version": "6.1",
        "suggestion": 'queryset.select_related("author")',
        "call_site": {
            "module": "library.serializers",
            "function": "get_author",
            "line": 24,
        },
        "context": {
            "view": "library.views.BookViewSet",
            "action": "list",
            "serializer": "library.serializers.BookSerializer",
        },
    }


def test_forward_foreign_key_suggests_select_related():
    diagnostic = diagnostic_for_access(Book(), "author")

    assert diagnostic.fetch_type is FetchType.FORWARD_FOREIGN_KEY
    assert diagnostic.model == "tests.Book"
    assert diagnostic.suggestion == 'queryset.select_related("author")'


def test_deferred_field_explains_only_and_defer():
    book = Book(title="The Left Hand of Darkness")
    book.__dict__.pop("title")

    diagnostic = diagnostic_for_access(book, "title")

    assert diagnostic.fetch_type is FetchType.DEFERRED_FIELD
    assert diagnostic.suggestion == 'include "title" in only(), or remove it from defer()'


def test_unknown_attribute_has_no_diagnostic():
    assert diagnostic_for_access(Book(), "not_a_field") is None
