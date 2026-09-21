"""Bootstrap-version class names for menu markup.

The framework comes from the ecosystem-wide ``CSS_FRAMEWORK`` setting, read through
``ajax_helpers.config.get_css_framework()`` so menus always agree with what
``{% lib_include %}`` loads::

    CSS_FRAMEWORK = 'bootstrap5'   # default 'bootstrap4'

Each framework is a small class of class-name tokens: :class:`Bootstrap4Classes`
holds the defaults and :class:`Bootstrap5Classes` overrides only what differs.
Templates receive the active instance as ``css`` (``{{ css.align_end }}``) and
Python-built markup calls :func:`css_classes` directly.
"""
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

try:
    from ajax_helpers.config import get_css_framework
except ImportError:  # the 0.0.x line has no config module
    def get_css_framework():
        return getattr(settings, 'CSS_FRAMEWORK', 'bootstrap4')


class Bootstrap4Classes:
    """Class-name tokens.  Defaults are Bootstrap 4; subclasses override what differs."""

    align_start = 'mr-auto'
    align_end = 'ml-auto'
    button_spacing = 'mr-1 mb-1'
    float_end = 'float-right'
    data_prefix = 'data-'

    @staticmethod
    def badge(colour):
        return f'badge badge-pill badge-{colour}'


class Bootstrap5Classes(Bootstrap4Classes):
    """Bootstrap 5: logical start/end spacing utilities, ``data-bs-*`` attributes
    and ``text-bg-*`` badge colours."""

    align_start = 'me-auto'
    align_end = 'ms-auto'
    button_spacing = 'me-1 mb-1'
    float_end = 'float-end'
    data_prefix = 'data-bs-'

    @staticmethod
    def badge(colour):
        return f'badge rounded-pill text-bg-{colour}'


FRAMEWORKS = {
    'bootstrap4': Bootstrap4Classes,
    'bootstrap5': Bootstrap5Classes,
}
_instances = {}


def css_classes():
    name = get_css_framework()
    if name not in _instances:
        framework_class = FRAMEWORKS.get(name)
        if framework_class is None:
            raise ImproperlyConfigured(
                f"CSS_FRAMEWORK={name!r} is not supported; choose one of {sorted(FRAMEWORKS)}")
        _instances[name] = framework_class()
    return _instances[name]

