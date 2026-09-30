"""The least Django needs to run ``django_menus``' own tests.

    django-admin test django_menus --settings=django_menus.test_settings --pythonpath=.

The examples project is not used: its app pulls in ``show_src_code`` and the rest of the demo
stack, none of which the library's own tests have anything to do with. Nothing here touches a
database -- the tests are ``SimpleTestCase`` -- but Django wants ``DATABASES`` to exist.
"""

SECRET_KEY = 'django-menus-tests'
DEBUG = False
USE_TZ = True

#: A menu item resolves its url on the way in, so there has to be a urlconf even when every test
#: hands it a bare href. This module is its own: an empty one resolves nothing, which is the
#: answer these tests want.
ROOT_URLCONF = 'django_menus.test_settings'
urlpatterns = []

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django_menus',
]

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {'context_processors': []},
    }
]
