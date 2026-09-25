# Changelog

All notable changes will be documented here. The format follows Keep a
Changelog, and releases use semantic versioning.

## Unreleased

### Added

- Added structured diagnostics for blocked relation and deferred-field fetches,
  including safe call-site data and preload suggestions.
- Added Django REST Framework view, action, and serializer context to fetch
  diagnostics.

### Fixed

- Fixed Django 6.1 native mode detection to use the released
  `FETCH_RAISE` constant instead of falling back to the compatibility engine.

## 0.1.2 - 2026-09-04

### Added

- Added async ORM integration coverage for all fetch policies.

## 0.1.1 - 2026-08-26

### Added

- Added copy-paste Django admin integration guidance.
- Added Django Ninja integration guidance without adding a required Ninja
  dependency.
- Added tests for the documented admin and Ninja queryset patterns.

## 0.1.0 - 2026-07-29

### Added

- Cross-version fetch policies for Django 4.2 through 6.1.
- Native Django 6.1 `FETCH_ONE`, `FETCH_PEERS`, and `RAISE` integration.
- Compatibility peer prefetching and strict blocking for Django 4.2–6.0.
- Guarded queryset and manager helpers.
- Per-action Django REST Framework policies.
- Pytest fixture and Django system checks.
- Django client and live-server integration tests with measured query counts.
