from contextlib import contextmanager
from unittest import mock

import pytest
from django.db.backends.utils import CursorWrapper
from django.test import TransactionTestCase

from fetch_guard import FieldFetchBlocked
from tests.models import Author, Book


@contextmanager
def count_async_queries():
    """Count SQL across the worker thread used by Django's async ORM."""
    queries = []
    original_execute = CursorWrapper.execute

    def counting_execute(cursor, sql, params=None):
        queries.append(sql)
        return original_execute(cursor, sql, params)

    with mock.patch.object(CursorWrapper, "execute", counting_execute):
        yield queries


class AsyncQuerySetTests(TransactionTestCase):
    async def test_strict_aget_allows_preloaded_relation(self):
        author = await Author.objects.acreate(name="N. K. Jemisin")
        book = await Book.objects.acreate(title="The Fifth Season", author=author)

        loaded = await Book.objects.select_related("author").strict().aget(pk=book.pk)

        assert loaded.author.name == "N. K. Jemisin"

    async def test_strict_aget_blocks_unloaded_relation(self):
        author = await Author.objects.acreate(name="James Baldwin")
        book = await Book.objects.acreate(title="Giovanni's Room", author=author)

        loaded = await Book.objects.strict().aget(pk=book.pk)

        with pytest.raises(FieldFetchBlocked):
            _ = loaded.author

    async def test_fetch_peers_async_iteration_uses_two_queries(self):
        first = await Author.objects.acreate(name="Ursula K. Le Guin")
        second = await Author.objects.acreate(name="Octavia E. Butler")
        await Book.objects.acreate(title="A Wizard of Earthsea", author=first)
        await Book.objects.acreate(title="Kindred", author=second)

        with count_async_queries() as queries:
            books = [
                book async for book in Book.objects.fetch_peers("author").order_by("pk")
            ]
            names = [book.author.name for book in books]

        assert names == ["Ursula K. Le Guin", "Octavia E. Butler"]
        assert len(queries) == 2
