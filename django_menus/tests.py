"""What a menu item renders into its tag.

The first tests in this package. They cover ``MenuItem.attributes`` -- and specifically the
accessible name of an item shown as an icon with no words, which is the only thing a screen
reader has to go on and used to be the icon font's private use codepoint.
"""

from django.test import SimpleTestCase
from django.utils.html import escape
from django.utils.safestring import mark_safe
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


class ALabelIsTextUnlessItSaysOtherwise(SimpleTestCase):
    """``display()`` escapes a label that is not marked safe.

    It used to ``mark_safe`` whatever it was given, so an item whose label came from a value --
    a project name, a file name, a report's name -- wrote that value into the page as markup.
    A label that is markup on purpose says so where it is made, and keeps working.
    """

    PAYLOAD = '<img src=x onerror=alert(1)>'

    def test_a_label_holding_markup_is_escaped(self):
        self.assertEqual(MenuItemDisplay(self.PAYLOAD).display(), '&lt;img src=x onerror=alert(1)&gt;')

    def test_a_label_holding_markup_is_escaped_beside_an_icon_too(self):
        """The icon branch is a second renderer, and the one a menu item usually takes."""
        rendered = MenuItemDisplay(self.PAYLOAD, font_awesome='fa fa-plus').display()

        self.assertNotIn('<img', rendered)
        self.assertIn('<i class="fa fa-plus"></i>', rendered)

    def test_a_label_marked_safe_is_still_markup(self):
        """``mark_safe``/``format_html``/a rendered template: the caller's own markup goes through."""
        display = MenuItemDisplay(mark_safe('<i class="fa fa-lock"></i> Disable'))

        self.assertEqual(display.display(), '<i class="fa fa-lock"></i> Disable')

    def test_a_label_already_escaped_is_not_escaped_twice(self):
        """Callers escaped their own labels while this marked everything safe. They still work."""
        self.assertEqual(MenuItemDisplay(escape(self.PAYLOAD)).display(), '&lt;img src=x onerror=alert(1)&gt;')

    def test_the_icon_class_cannot_end_its_attribute(self):
        rendered = MenuItemDisplay('Add', font_awesome='fa" onmouseover="alert(1)').display()

        self.assertNotIn('onmouseover="', rendered)

    def test_a_label_of_none_still_reads_as_none(self):
        """Unchanged: a display with no text showed ``None`` before and shows it now."""
        self.assertEqual(MenuItemDisplay(None).display(), 'None')


class AnAttributeValueIsTextToo(SimpleTestCase):
    """``attributes()`` writes each value inside double quotes, and marked them all safe.

    A tooltip is the one that holds text somebody typed, so a quote in it closed ``title=""`` and
    whatever followed was read as further attributes.
    """

    def test_a_quote_in_a_tooltip_cannot_start_another_attribute(self):
        rendered = attributes_of(menu_display=MenuItemDisplay('Edit', tooltip='Bo" onmouseover="alert(1)'))

        self.assertNotIn('onmouseover="', rendered)
        self.assertIn('&quot;', rendered)

    def test_an_ordinary_tooltip_is_unchanged(self):
        self.assertIn('title="Edit"', attributes_of(menu_display=MenuItemDisplay('Edit', tooltip='Edit')))

    def test_a_tooltip_already_escaped_is_not_escaped_twice(self):
        rendered = attributes_of(menu_display=MenuItemDisplay('Edit', tooltip=escape('Bo"b')))

        self.assertIn('title="Bo&quot;b"', rendered)
        self.assertNotIn('&amp;quot;', rendered)
