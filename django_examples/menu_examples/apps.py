from show_src_code.apps import PypiAppConfig


class ModalConfig(PypiAppConfig):
    default = True
    name = 'menu_examples'
    pypi = 'django-tab-menus'
    urls = 'menu_examples.urls'
