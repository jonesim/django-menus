"""System checks for the menu registry.

These run on ``manage.py check``, ``runserver`` and most CI, and report every problem at once.
The registry also raises ``ImproperlyConfigured`` when it scans, because checks can be skipped and
a mistyped section would otherwise make a menu entry silently disappear.
"""
from django.core.checks import Error, Tags, Warning, register

from .menu import registry


@register(Tags.urls)
def check_menu_registry(app_configs=None, **kwargs):
    messages = []
    for error in registry.validate():
        message_class = Error if error.is_error else Warning
        messages.append(message_class(error.message, hint=error.hint, obj=error.obj,
                                      id=f'django_menus.{error.code}'))
    return messages
