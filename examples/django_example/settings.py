# examples/django_example/settings.py
SECRET_KEY = "example"
INSTALLED_APPS = ["app"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
