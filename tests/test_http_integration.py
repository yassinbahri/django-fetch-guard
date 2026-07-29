import json
from urllib.error import HTTPError
from urllib.request import urlopen

from django.test import LiveServerTestCase, TestCase

from tests.models import Author, Book


class BookDataMixin:
    def create_books(self):
        le_guin = Author.objects.create(name="Ursula K. Le Guin")
        butler = Author.objects.create(name="Octavia E. Butler")
        Book.objects.create(title="A Wizard of Earthsea", author=le_guin)
        Book.objects.create(title="Kindred", author=butler)


class FetchPolicyClientTests(BookDataMixin, TestCase):
    def setUp(self):
        self.create_books()

    def test_measured_query_counts(self):
        expectations = {
            "/books/normal/": "3",
            "/books/peers/": "2",
            "/books/strict/": "1",
        }
        for path, query_count in expectations.items():
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers["X-Query-Count"], query_count)

    def test_strict_violation_is_blocked(self):
        response = self.client.get("/books/strict-broken/")
        self.assertEqual(response.status_code, 409)
        self.assertIn("author", response.json()["error"])


class FetchPolicyLiveServerTests(BookDataMixin, LiveServerTestCase):
    def setUp(self):
        self.create_books()

    def request(self, path):
        with urlopen(f"{self.live_server_url}{path}", timeout=5) as response:
            return response.status, dict(response.headers), json.load(response)

    def test_real_http_query_counts(self):
        expectations = {
            "/books/normal/": "3",
            "/books/peers/": "2",
            "/books/strict/": "1",
        }
        for path, query_count in expectations.items():
            with self.subTest(path=path):
                status, headers, payload = self.request(path)
                self.assertEqual(status, 200)
                self.assertEqual(headers["X-Query-Count"], query_count)
                self.assertEqual(len(payload["books"]), 2)

    def test_real_http_strict_violation(self):
        with self.assertRaises(HTTPError) as caught:
            urlopen(f"{self.live_server_url}/books/strict-broken/", timeout=5)
        self.assertEqual(caught.exception.code, 409)
        self.assertIn("author", json.load(caught.exception)["error"])

