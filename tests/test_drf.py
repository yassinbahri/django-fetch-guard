import pytest
from django.core.exceptions import ImproperlyConfigured

from fetch_guard import FieldFetchBlocked
from fetch_guard.drf import FetchGuardMixin
from tests.models import Author, Book


class QuerysetView:
    action = "list"

    def get_queryset(self):
        return Book.objects.all()


class StrictView(FetchGuardMixin, QuerysetView):
    fetch_guard = {"list": "raise", "default": "peers"}


class InvalidView(FetchGuardMixin, QuerysetView):
    fetch_guard = "raise"


@pytest.mark.django_db
def test_action_policy_is_applied():
    author = Author.objects.create(name="N. K. Jemisin")
    Book.objects.create(title="The Fifth Season", author=author)
    book = StrictView().get_queryset().first()
    with pytest.raises(FieldFetchBlocked):
        _ = book.author


def test_invalid_policy_is_reported_as_improperly_configured():
    with pytest.raises(ImproperlyConfigured, match="must be a dictionary"):
        InvalidView().get_queryset()
