"""
Bootstrap 5 variant of the example project.

    python manage.py runserver --settings=django_examples.settings_bs5

Needs django-ajax-helpers >= 1.0.1 (0.0.x ignores CSS_FRAMEWORK; 1.0.0 breaks AJAX posts).
"""
from importlib.metadata import PackageNotFoundError, version
from importlib.util import find_spec

from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F401,F403

if find_spec('ajax_helpers.config') is None:
    raise ImproperlyConfigured('settings_bs5 needs django-ajax-helpers >= 1.0.1 (CSS_FRAMEWORK support)')
try:
    if version('django-ajax-helpers') == '1.0.0':
        raise ImproperlyConfigured('settings_bs5 needs django-ajax-helpers >= 1.0.1 (1.0.0 breaks AJAX posts)')
except PackageNotFoundError:
    pass

CSS_FRAMEWORK = 'bootstrap5'

# Separate database: this variant runs a newer Django than the Bootstrap 4 container sharing the same folder.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(BASE_DIR.joinpath('db_bs5.sqlite3')),
    }
}
