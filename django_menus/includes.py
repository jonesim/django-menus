from ajax_helpers.html_include import SourceBase, pip_version


version = pip_version('django-tab-menus')


class DjangoMenus(SourceBase):
    static_path = 'django_menus/'
    # Floating UI 1.8.0 (vendored UMD builds) positions dropdowns; core must load before dom.
    js_filename = ['floating-ui.core.umd.min.js', 'floating-ui.dom.umd.min.js', 'django_menus.js']
    css_filename = 'django_menus.css'
    js_path = ''
    css_path = ''


class DefaultInclude(DjangoMenus):
    pass
