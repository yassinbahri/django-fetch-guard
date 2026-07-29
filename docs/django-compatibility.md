# Django compatibility and limitations

## Supported versions

| Django | Python requirement from this package | Engine |
| --- | --- | --- |
| 6.1 | Python 3.12+ as required by Django | Native fetch modes |
| 6.0 | Python 3.12+ as required by Django | Compatibility engine |
| 5.2 | Python 3.10+ | Compatibility engine |
| 4.2 | Python 3.10+ | Compatibility engine |

The package metadata allows Python 3.10+ and Django `>=4.2,<6.2`. Django's own
Python-version requirements still apply.

## Behavior by engine

### Django 6.1

- `normal()` uses native `FETCH_ONE`.
- `fetch_peers()` uses native `FETCH_PEERS`.
- `strict()` uses native `RAISE`.
- Fetch policy propagates through related objects according to Django's rules.

### Django 4.2–6.0

- `normal()` removes a package strict policy and restores ordinary lazy loads.
- `fetch_peers()` prefetches direct forward `ForeignKey` and `OneToOneField`
  relations. Passing relation names uses exactly those prefetches.
- `strict()` marks returned model instances. `FetchGuardModelMixin` checks
  deferred scalar fields and forward/reverse one-to-one or forward foreign-key
  access before Django can issue an implicit query.

## Honest limitations

The compatibility engine is useful but cannot reproduce every Django 6.1
behavior:

- Automatic legacy peer fetching is eager, not on-demand.
- Automatic legacy peer fetching does not guess nested, reverse one-to-many,
  or many-to-many paths. Pass those paths explicitly or use
  `prefetch_related()`.
- Strict mode does not prohibit arbitrary SQL issued by application code.
- Calling a related manager such as `book.reviews.all()` is an explicit
  queryset operation and is not blocked.
- Custom properties that query the database cannot be identified as model
  field fetches.
- `values()` and `values_list()` return plain data, so legacy strict marking is
  intentionally skipped.

For maximum consistency between versions, name peer relations explicitly and
use strict mode with `select_related()`/`prefetch_related()` in critical code.

## Upgrade behavior

Applications can upgrade from Django 4.2–6.0 to 6.1 without changing the public
fetch-guard API. Once Django 6.1 is active, native behavior is selected at
import time. Keeping `FetchGuardModelMixin` is harmless and allows future
downgrades; removing it is optional if the application will remain on 6.1+.

