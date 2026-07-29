from django.db import models

from fetch_guard import FetchGuardModelMixin, GuardedManager


class Author(models.Model):
    name = models.CharField(max_length=100)


class Book(FetchGuardModelMixin, models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    objects = GuardedManager(default_mode="one")


class StrictBook(FetchGuardModelMixin, models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    objects = GuardedManager(default_mode="raise")
