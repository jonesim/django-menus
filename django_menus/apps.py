from django.apps import AppConfig
from django.core.signals import setting_changed


class DjangoMenusConfig(AppConfig):
    name = 'django_menus'

    def ready(self):
        # Registering the check and connecting the signal are the only things safe to do here -
        # scanning the URLConf or building a MenuItem this early would reverse() urls that are not
        # loaded yet.
        from . import checks  # noqa: F401  registers the system check
        from .menu.registry import clear_cache
        setting_changed.connect(clear_cache, dispatch_uid='django_menus.registry')
