import pytest
from django.core.exceptions import ImproperlyConfigured

from fetch_guard import FieldFetchBlocked, get_fetch_diagnostic
from fetch_guard.drf import FetchGuardMixin
from tests.models import Author, Book


class QuerysetView:
    action = "list"

    def get_queryset(self):
        return Book.objects.all()


class StrictView(FetchGuardMixin, QuerysetView):
    fetch_guard = {"list": "raise", "default": "peers"}


class BookSerializer:
    pass


class SerializerView(StrictView):
    serializer_class = BookSerializer


class InvalidView(FetchGuardMixin, QuerysetView):
    fetch_guard = "raise"


@pytest.mark.django_db
def test_action_policy_is_applied():
    author = Author.objects.create(name="N. K. Jemisin")
    Book.objects.create(title="The Fifth Season", author=author)
    book = StrictView().get_queryset().first()
    with pytest.raises(FieldFetchBlocked):
        _ = book.author


@pytest.mark.django_db
def test_diagnostic_includes_drf_context():
    author = Author.objects.create(name="N. K. Jemisin")
    Book.objects.create(title="The Fifth Season", author=author)
    book = SerializerView().get_queryset().first()

    with pytest.raises(FieldFetchBlocked) as caught:
        _ = book.author

    context = get_fetch_diagnostic(caught.value).context
    assert context.view == f"{__name__}.SerializerView"
    assert context.action == "list"
    assert context.serializer == f"{__name__}.BookSerializer"


def test_invalid_policy_is_reported_as_improperly_configured():
    with pytest.raises(ImproperlyConfigured, match="must be a dictionary"):
        InvalidView().get_queryset()
