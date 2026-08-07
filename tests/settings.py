SECRET_KEY = 'django-menus-tests'

DEBUG = False

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'ajax_helpers',
    'django_menus',
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'tests.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

STATIC_URL = '/static/'

USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# The registry sections used by the fixture views in tests/views.py
DJANGO_MENUS_SECTIONS = {
    'settings': {'title': 'Settings'},
    'support': {},
    'reports': {
        'title': 'Reports',
        'groups': ['sales', 'purchases', 'stock', ('company', 'Company')],
        'sort': 'order',
    },
}
