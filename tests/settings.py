SECRET_KEY = "test-secret-key"
INSTALLED_APPS = ["django.contrib.contenttypes", "django.contrib.auth", "django_fly_replay"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
ROOT_URLCONF = "tests.urls"
