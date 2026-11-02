"""Tooltip placement and badges on dropdown items."""
from django.test import SimpleTestCase, override_settings

from django_menus.menu import HtmlMenu, MenuItem, MenuItemBadge, MenuItemDisplay
from tests.utils import make_request, render_menu


def item(*args, **kwargs):
    return MenuItem('#', *args, link_type=MenuItem.HREF, **kwargs)


def in_dropdown(child):
    HtmlMenu(make_request()).add_items(item('Parent', dropdown=[child]))
    return child


class TooltipPlacementTests(SimpleTestCase):

    def test_top_level_tooltip_is_below(self):
        self.assertIn('data-placement="bottom"', item('Edit', tooltip='Edit it').attributes())

    def test_dropdown_tooltip_is_to_the_right(self):
        self.assertIn('data-placement="right"', in_dropdown(item('Edit', tooltip='Edit it')).attributes())

    def test_display_tooltip_follows_the_item(self):
        child = in_dropdown(item(MenuItemDisplay('Edit', tooltip='Edit it')))
        self.assertIn('data-placement="right"', child.attributes())

    def test_explicit_placement_wins(self):
        child = in_dropdown(item('Edit', tooltip='Edit it', tooltip_placement='left'))
        self.assertIn('data-placement="left"', child.attributes())

    @override_settings(CSS_FRAMEWORK='bootstrap5')
    def test_bootstrap5_prefix(self):
        self.assertIn('data-bs-placement="top"', item('Edit', tooltip='Edit it', tooltip_placement='top').attributes())


class DropdownBadgeTests(SimpleTestCase):

    def test_badge_renders_in_dropdown_item(self):
        menu = HtmlMenu(make_request()).add_items(
            item('Support', dropdown=[item('Release Notes', badge=MenuItemBadge(text='New', css_class='success'))]))
        self.assertIn('Release Notes&nbsp;<sup><span class="badge badge-pill badge-success">New</span></sup></a>',
                      render_menu(menu))
