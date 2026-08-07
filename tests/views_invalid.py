"""Views with deliberately broken menu_entry declarations, one per check id.

They live in their own module and URLConf so the valid fixtures in tests/views.py stay scannable.
"""
from django_menus.menu import MenuEntry
from tests.views import BaseView


class UnknownSection(BaseView):
    """E001"""
    menu_display = 'Unknown Section'
    menu_entry = MenuEntry('nope')


class UnknownGroup(BaseView):
    """E002"""
    menu_display = 'Unknown Group'
    menu_entry = MenuEntry('reports', 'nope')


class MissingGroup(BaseView):
    """E002 - a grouped section requires a group."""
    menu_display = 'Missing Group'
    menu_entry = MenuEntry('reports')


class Ambiguous(BaseView):
    """E003 - registered under two url names with no url_name on the entry."""
    menu_display = 'Ambiguous'
    menu_entry = MenuEntry('settings')


class UnknownUrlName(BaseView):
    """E004"""
    menu_display = 'Unknown Url Name'
    menu_entry = MenuEntry('settings', url_name='not_a_url')


class MissingUrlArgs(BaseView):
    """E005 - lives under an include() that captures <int:pk>."""
    menu_display = 'Missing Url Args'
    menu_entry = MenuEntry('settings')


class NotAnEntry(BaseView):
    """E006"""
    menu_display = 'Not An Entry'
    menu_entry = {'section': 'settings'}


class NoDisplay(BaseView):
    """W001 - no menu_display anywhere, so the url name gets capitalised."""
    menu_entry = MenuEntry('settings')


class ButtonDefaultClash(BaseView):
    """W002"""
    menu_display = 'Clashing Button'
    menu_entry = MenuEntry('settings')
