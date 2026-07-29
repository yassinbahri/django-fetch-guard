SECRET_KEY = "fetch-guard-tests"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "fetch_guard",
    "tests",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
ALLOWED_HOSTS = ["localhost", "testserver"]
ROOT_URLCONF = "tests.urls"
STATIC_URL = "/static/"
USE_TZ = True
