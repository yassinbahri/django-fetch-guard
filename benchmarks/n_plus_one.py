import os
import sys
from pathlib import Path
from time import perf_counter

import django
from django.db import connection
from django.test.utils import CaptureQueriesContext


ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
django.setup()

from tests.models import Author, Book, StrictBook


def setup_database():
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Author)
        schema_editor.create_model(Book)
        schema_editor.create_model(StrictBook)


def reset_database():
    StrictBook.objects.all().delete()
    Book.objects.all().delete()
    Author.objects.all().delete()


def create_dataset(row_count):
    authors = [
        Author(name=f"Author {index}")
        for index in range(row_count)
    ]
    Author.objects.bulk_create(authors)

    authors = list(Author.objects.all())

    Book.objects.bulk_create(
        [
            Book(title=f"Book {index}", author=author)
            for index, author in enumerate(authors)
        ]
    )


def benchmark_normal():
    with CaptureQueriesContext(connection) as queries:
        start = perf_counter()

        books = list(Book.objects.all())

        for book in books:
            _ = book.author.name

        elapsed = perf_counter() - start

    return len(queries), elapsed


def benchmark_fetch_peers():
    with CaptureQueriesContext(connection) as queries:
        start = perf_counter()

        books = list(Book.objects.fetch_peers("author"))

        for book in books:
            _ = book.author.name

        elapsed = perf_counter() - start

    return len(queries), elapsed


def benchmark_select_related():
    with CaptureQueriesContext(connection) as queries:
        start = perf_counter()

        books = list(Book.objects.select_related("author").strict())

        for book in books:
            _ = book.author.name

        elapsed = perf_counter() - start

    return len(queries), elapsed


def main():
    setup_database()

    for row_count in (10, 100, 1000):
        reset_database()
        create_dataset(row_count)

        normal_queries, normal_time = benchmark_normal()
        fetch_queries, fetch_time = benchmark_fetch_peers()
        select_queries, select_time = benchmark_select_related()

        print(f"\nRows: {row_count}")
        print(
            f"Normal FK access:         "
            f"{normal_queries} queries, {normal_time:.6f}s"
        )
        print(
            f"fetch_peers('author'):    "
            f"{fetch_queries} queries, {fetch_time:.6f}s"
        )
        print(
            f"select_related + strict: "
            f"{select_queries} queries, {select_time:.6f}s"
        )


if __name__ == "__main__":
    main()