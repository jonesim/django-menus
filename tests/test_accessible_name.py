"""aria-label for icon-only menu items, taken from the tooltip."""

from django.test import SimpleTestCase
from django_menus.menu import MenuItem, MenuItemDisplay


def attributes_of(**kwargs) -> str:
    """The attribute string an HREF item renders into its <a> (avoids url resolution)."""
    return str(MenuItem(url='#', link_type=MenuItem.HREF, **kwargs).attributes())


class AnIconOnlyItemIsNamedForAssistiveTechnology(SimpleTestCase):
    """Icon only: the tooltip becomes the aria-label."""

    def test_an_icon_with_a_tooltip_and_no_text_is_labelled(self):
        rendered = attributes_of(menu_display=MenuItemDisplay('', font_awesome='fa fa-plus', tooltip='Add'))

        self.assertIn('aria-label="Add"', rendered)

    def test_the_label_is_the_tooltip_the_sighted_reader_sees(self):
        rendered = attributes_of(menu_display=MenuItemDisplay('', font_awesome='fa fa-pencil', tooltip='Edit'))

        self.assertIn('title="Edit"', rendered)
        self.assertIn('aria-label="Edit"', rendered)

    def test_a_tooltip_on_the_item_rather_than_the_display_counts_too(self):
        rendered = attributes_of(menu_display=MenuItemDisplay('', font_awesome='fa fa-trash'), tooltip='Remove')

        self.assertIn('aria-label="Remove"', rendered)


class AnItemThatShowsWordsIsLeftAlone(SimpleTestCase):
    """aria-label would override the visible words, so none is added."""

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
        self.assertNotIn('aria-label', attributes_of(menu_display=MenuItemDisplay('', font_awesome='fa fa-plus')))

    def test_a_label_the_caller_passed_is_not_overwritten(self):
        rendered = attributes_of(
            menu_display=MenuItemDisplay('', font_awesome='fa fa-plus', tooltip='Add'),
            attributes={'aria-label': 'Add a door blank size'},
        )

        self.assertIn('aria-label="Add a door blank size"', rendered)
        self.assertNotIn('aria-label="Add"', rendered)


class TheRenderedNameIsUnchanged(SimpleTestCase):
    """The icon is not marked aria-hidden, so existing accessible names are unchanged."""

    def test_an_icon_and_words_still_render_both(self):
        display = MenuItemDisplay('Add', font_awesome='fa fa-plus')

        self.assertEqual(display.display(), '<i class="fa fa-plus"></i> Add')

    def test_the_icon_carries_no_aria_hidden(self):
        self.assertNotIn('aria-hidden', MenuItemDisplay('', font_awesome='fa fa-plus').display())
