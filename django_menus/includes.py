from importlib.metadata import PackageNotFoundError

from ajax_helpers.html_include import SourceBase, pip_version

try:
    version = pip_version('django-tab-menus')
except PackageNotFoundError:
    version = 'local'


class DjangoMenus(SourceBase):
    static_path = 'django_menus/'
    filename = 'django_menus'
    js_path = ''
    css_path = ''


class DefaultInclude(DjangoMenus):
    pass
