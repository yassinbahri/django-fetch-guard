# Troubleshooting

## Strict mode says the model needs `FetchGuardModelMixin`

On Django 4.2–6.0, inherit from the mixin before `models.Model`:

```python
class Book(FetchGuardModelMixin, models.Model):
    ...
```

Adding the mixin does not require a migration. Django 6.1 uses its native
engine, but keeping the mixin makes code portable.

## `FieldFetchBlocked` is raised for a foreign key

Strict mode is reporting that the related object was not loaded. Add the
relation to the query plan:

```python
Book.objects.select_related("author").strict()
```

Use `select_related()` for forward foreign keys and one-to-one relations. Use
`prefetch_related()` for reverse and many-to-many collections:

```python
Author.objects.prefetch_related("books").strict()
```

## `fetch_peers()` performs more than two queries

Two queries describes one related path: one for the base objects and one for
the related batch. Multiple explicit prefetch paths may each require a query.
Nested serializers and many-to-many relationships can also add queries.

Inspect the actual workload with `django_assert_num_queries`, Django Debug
Toolbar, or `CaptureQueriesContext` before deciding the correct expectation.

## Behavior differs between Django 6.1 and older Django

Django 6.1 peer loading is on-demand. The compatibility engine eagerly
prefetches direct forward relations. For consistent behavior, name relations:

```python
Book.objects.fetch_peers("author")
```

Read the [compatibility guide](django-compatibility.md) before relying on
version-specific timing.

## A reverse or many-to-many query was not blocked

Related-manager operations such as `book.reviews.all()` are explicit queryset
operations, not implicit model-field fetches. Fetch guard does not block them.
Use `prefetch_related()` and query-count tests for these paths.

## The `fetch_guard` pytest fixture is unavailable

Install the test extra and ensure pytest plugin autoloading is enabled:

```console
python -m pip install "django-fetch-guard[test]"
python -m pytest
```

If the environment sets `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, load the plugin
explicitly:

```console
python -m pytest -p fetch_guard.pytest_plugin
```

## Django reports an invalid `FETCH_GUARD` setting

The setting must be a dictionary:

```python
FETCH_GUARD = {"DEFAULT_MODE": "raise"}
```

Run `python manage.py check --tag fetch_guard` for the exact validation error.

## Adding the package created no migration

That is expected. The manager and mixin alter Python behavior only and add no
database schema.

