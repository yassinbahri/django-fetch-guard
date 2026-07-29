# Contributing to django-fetch-guard

Contributions are welcome: bug reports, documentation corrections, tests,
compatibility work, and focused features all help.

## Before opening an issue

1. Search existing issues to avoid duplicates.
2. Check the [troubleshooting guide](docs/troubleshooting.md).
3. Reduce bugs to the smallest model and queryset that reproduces the problem.
4. Include Python, Django, database, and django-fetch-guard versions.

Use the repository's bug and feature templates so maintainers receive enough
information to respond without a long clarification round.

## Development setup

Prerequisites:

- Git.
- A supported Python version.
- A virtual environment. Docker is optional for cross-version testing.

Clone and create an environment:

```console
git clone https://github.com/yassinbahri/django-fetch-guard.git
cd django-fetch-guard
python -m venv .venv
```

Activate it and install the editable package:

```console
# Windows PowerShell
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

```console
# Linux or macOS
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

## Run the test suite

```console
python -m pytest
```

The suite contains unit tests, Django request-client tests, live HTTP server
tests, DRF policy tests, and exact query-count assertions. A successful run
should include all tests and subtests.

Run one file or one test while developing:

```console
python -m pytest tests/test_managers.py -vv
python -m pytest tests/test_managers.py::test_strict_blocks_unfetched_relation -vv
```

The GitHub Actions matrix is the source of truth for all supported combinations:

- Django 4.2 on Python 3.10.
- Django 5.2 on Python 3.12.
- Django 6.0 on Python 3.12.
- Django 6.1 on Python 3.14.

## Repository map

```text
src/fetch_guard/          Package implementation
src/fetch_guard/drf/      Optional DRF integration
tests/                    Unit and HTTP integration tests
docs/                     User documentation
.github/workflows/        Continuous integration
```

## Making a change

1. Create a branch from `main`.
2. Add or update tests before changing behavior.
3. Keep public APIs consistent across native and compatibility engines.
4. Update the API reference and README when user-facing behavior changes.
5. Add a concise entry under `Unreleased` in `CHANGELOG.md`.
6. Run the full test suite before opening a pull request.

Compatibility changes must cover both paths:

- Django 4.2–6.0 uses the compatibility engine.
- Django 6.1 uses native fetch modes.

Do not depend on private Django internals without documenting why the dependency
is necessary and testing every supported Django series.

## Test expectations

- Bug fixes need a regression test that fails before the fix.
- Query behavior should use exact query-count assertions.
- HTTP integration belongs in `tests/test_http_integration.py`.
- Optional DRF behavior belongs in `tests/test_drf.py`.
- Tests must not depend on execution order or external services.

## Pull-request checklist

- [ ] The change is focused and explained clearly.
- [ ] Tests pass locally.
- [ ] New behavior has tests.
- [ ] Public behavior is documented.
- [ ] `CHANGELOG.md` is updated when appropriate.
- [ ] No virtual environments, databases, credentials, or build artifacts are committed.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

