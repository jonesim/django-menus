"""Shared helpers for the django_menus test suite."""
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import resolve


def menu_ids(menu):
    """Every generated menu id in a rendered menu tree, outermost first."""
    ids = [menu.id] if menu.id else []
    for item in menu.menu_items:
        dropdown = getattr(item, 'dropdown', None)
        if dropdown is not None:
            ids += menu_ids(dropdown)
    return ids


def render_menu(menu):
    """Render a menu with its randomly generated ids replaced by stable placeholders."""
    html = str(menu.render())
    for index, menu_id in enumerate(menu_ids(menu)):
        html = html.replace(menu_id, f'ID{index}')
    return html


def make_request(path='/home/', user=None, resolve_path=True):
    request = RequestFactory().get(path)
    request.user = user if user is not None else AnonymousUser()
    if resolve_path:
        request.resolver_match = resolve(path)
    return request
