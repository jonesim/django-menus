"""Which Bootstrap the menus render for, and where the templates for it live.

Menus ships one folder of templates per supported Bootstrap version:

    django_menus/templates/django_menus/bootstrap4/
    django_menus/templates/django_menus/bootstrap5/

``DJANGO_MENUS_TEMPLATE_PACK`` picks between them, defaulting to Bootstrap 4:

    DJANGO_MENUS_TEMPLATE_PACK = 'bootstrap5'

It may instead be a dotted path to a callable taking the request and returning a pack name,
for a project that has to serve both -- the example app uses that to put a version toggle in
its nav bar. A pack name never contains a dot, which is what tells the two apart.
"""
from django.conf import settings
from django.template.loader import select_template
from django.utils.module_loading import import_string

DEFAULT_PACK = 'bootstrap4'

# The one piece of Bootstrap naming that is not markup and so cannot live in the template
# folder: a tooltip's placement is a key in the attributes dict, and Bootstrap 5 prefixed
# its own data attributes with bs-. Everything else a pack varies is in its templates.
PACK_ATTRIBUTES = {
    'bootstrap4': {'placement': 'data-placement'},
    'bootstrap5': {'placement': 'data-bs-placement'},
}


def template_pack(request=None):
    """The pack name for this request, from the setting."""
    configured = getattr(settings, 'DJANGO_MENUS_TEMPLATE_PACK', DEFAULT_PACK)
    if callable(configured):
        return configured(request)
    if '.' in configured:
        return import_string(configured)(request)
    return configured


def pack_attribute(name, request=None):
    """A Bootstrap attribute name spelled for this request's pack."""
    pack = template_pack(request)
    return PACK_ATTRIBUTES.get(pack, PACK_ATTRIBUTES[DEFAULT_PACK])[name]


def pack_template(name, request=None):
    """Resolve a template name against the pack, letting a project override it.

    The flat path is tried first and the pack second, so a project that already overrides
    ``django_menus/main_menu.html`` in its own templates directory keeps that override --
    menus no longer ships anything at the flat path, so it only resolves if the project
    supplies it. Failing that, the pack's copy is used.
    """
    return select_template([f'django_menus/{name}', f'django_menus/{template_pack(request)}/{name}'])


def render_pack_template(name, context, request=None):
    return pack_template(name, request).render(context)
