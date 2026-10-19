"""What a menu item renders into its tag.

The first tests in this package. They cover ``MenuItem.attributes`` -- and specifically the
accessible name of an item shown as an icon with no words, which is the only thing a screen
reader has to go on and used to be the icon font's private use codepoint.
"""

from django.test import SimpleTestCase
from django_menus.menu import MenuItem, MenuItemDisplay


def attributes_of(**kwargs) -> str:
    """The attribute string an item renders into its ``<a>``.

    ``link_type=MenuItem.HREF`` throughout: these tests are about the attributes, and a url name
    would send the item looking for a urlconf that has nothing to do with what is being asked.
    """
    return str(MenuItem(url='#', link_type=MenuItem.HREF, **kwargs).attributes())


class AnIconOnlyItemIsNamedForAssistiveTechnology(SimpleTestCase):
    """An item with an icon and no words: the tooltip is the only wording it has, so it is also
    the accessible name. Without this the name is whatever the font renders in ``::before`` --
    for Font Awesome a private use codepoint, announced as nothing a reader can act on."""

    def test_an_icon_with_a_tooltip_and_no_text_is_labelled(self):
        rendered = attributes_of(menu_display=MenuItemDisplay('', font_awesome='fa fa-plus', tooltip='Add'))

        self.assertIn('aria-label="Add"', rendered)

    def test_the_label_is_the_tooltip_the_sighted_reader_sees(self):
        """Not a second wording to keep in step -- the same string reaches both."""
        rendered = attributes_of(menu_display=MenuItemDisplay('', font_awesome='fa fa-pencil', tooltip='Edit'))

        self.assertIn('title="Edit"', rendered)
        self.assertIn('aria-label="Edit"', rendered)

    def test_a_tooltip_on_the_item_rather_than_the_display_counts_too(self):
        """``MenuItem(tooltip=…)`` and ``MenuItemDisplay(tooltip=…)`` both end up as ``title``."""
        rendered = attributes_of(menu_display=MenuItemDisplay('', font_awesome='fa fa-trash'), tooltip='Remove')

        self.assertIn('aria-label="Remove"', rendered)


class AnItemThatShowsWordsIsLeftAlone(SimpleTestCase):
    """``aria-label`` overrides the visible label, so putting one on an item that already shows
    words makes what is announced differ from what is on screen wherever the tooltip says
    something else -- which is what a tooltip is usually for."""

    def test_words_and_a_tooltip_get_no_label(self):
        rendered = attributes_of(
            menu_display=MenuItemDisplay('Add', font_awesome='fa fa-plus', tooltip='Add a new one')
        )

        self.assertIn('title="Add a new one"', rendered)
        self.assertNotIn('aria-label', rendered)

    def test_words_alone_get_no_label(self):
        self.assertNotIn('aria-label', attributes_of(menu_display=MenuItemDisplay('Add')))


class NothingIsInvented(SimpleTestCase):
    def test_an_icon_with_no_tooltip_is_not_given_a_name(self):
        """There is no wording to use. Naming it after the icon class would be worse than silence."""
        self.assertNotIn('aria-label', attributes_of(menu_display=MenuItemDisplay('', font_awesome='fa fa-plus')))

    def test_a_label_the_caller_passed_is_not_overwritten(self):
        rendered = attributes_of(
            menu_display=MenuItemDisplay('', font_awesome='fa fa-plus', tooltip='Add'),
            attributes={'aria-label': 'Add a door blank size'},
        )

        self.assertIn('aria-label="Add a door blank size"', rendered)
        self.assertNotIn('aria-label="Add"', rendered)


class TheRenderedNameIsUnchanged(SimpleTestCase):
    """The icon is deliberately not marked ``aria-hidden``: that would drop the glyph from every
    labelled item's accessible name too, which is a breaking change for callers selecting on the
    name rather than a fix for anyone reading the page."""

    def test_an_icon_and_words_still_render_both(self):
        display = MenuItemDisplay('Add', font_awesome='fa fa-plus')

        self.assertEqual(display.display(), '<i class="fa fa-plus"></i> Add')

    def test_the_icon_carries_no_aria_hidden(self):
        self.assertNotIn('aria-hidden', MenuItemDisplay('', font_awesome='fa fa-plus').display())
