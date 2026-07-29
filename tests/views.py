from django.db import connection
from django.http import JsonResponse
from django.test.utils import CaptureQueriesContext

from fetch_guard import FieldFetchBlocked

from .models import Book


def _serialize(queryset):
    return [
        {"title": book.title, "author": book.author.name}
        for book in queryset
    ]


def _measured_response(policy, queryset):
    with CaptureQueriesContext(connection) as queries:
        books = _serialize(queryset)
    response = JsonResponse({"policy": policy, "books": books})
    response.headers["X-Query-Count"] = str(len(queries))
    return response


def normal_books(request):
    return _measured_response("normal", Book.objects.normal().order_by("pk"))


def peer_books(request):
    return _measured_response("peers", Book.objects.fetch_peers().order_by("pk"))


def strict_books(request):
    queryset = Book.objects.select_related("author").strict().order_by("pk")
    return _measured_response("strict", queryset)


def strict_broken_books(request):
    try:
        return _measured_response("strict-broken", Book.objects.strict().order_by("pk"))
    except FieldFetchBlocked as exc:
        return JsonResponse({"error": str(exc)}, status=409)

