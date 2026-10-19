"""DJANGO_MENUS_ESCAPE_ATTRIBUTES, DJANGO_MENUS_ESCAPE_LABELS and DJANGO_MENUS_BLOCK_EVENT_ATTRIBUTES."""
from django.test import SimpleTestCase, override_settings
from django.utils.safestring import mark_safe

from django_menus.menu import HeaderItem, HtmlMenu, MenuItem, MenuItemBadge, MenuItemDisplay
from tests.utils import make_request, render_menu


def item(*args, **kwargs):
    return MenuItem('#', *args, link_type=MenuItem.HREF, **kwargs)


class EscapeAttributesTests(SimpleTestCase):
    """On by default."""

    def test_quote_in_tooltip_is_escaped(self):
        self.assertIn('title="5&quot; pipe"', item('Pipe', tooltip='5" pipe').attributes())

    def test_value_marked_safe_is_not_escaped_again(self):
        attributes = item('Report', attributes={'title': mark_safe('R&amp;D')}).attributes()
        self.assertIn('title="R&amp;D"', attributes)

    def test_malformed_name_is_dropped(self):
        attributes = item('X', attributes={'x onmouseover': 'alert(1)', 'data-id': '1'}).attributes()
        self.assertNotIn('onmouseover', attributes)
        self.assertIn('data-id="1"', attributes)

    def test_event_attributes_are_kept(self):
        self.assertIn('onclick="go()"', item('X', attributes={'onclick': 'go()'}).attributes())

    @override_settings(DJANGO_MENUS_ESCAPE_ATTRIBUTES=False)
    def test_off_writes_values_as_given(self):
        attributes = item('X', tooltip='5" pipe', attributes={'x y': '1'}).attributes()
        self.assertIn('title="5" pipe"', attributes)
        self.assertIn('x y="1"', attributes)


@override_settings(DJANGO_MENUS_BLOCK_EVENT_ATTRIBUTES=True)
class BlockEventAttributesTests(SimpleTestCase):

    def test_event_attributes_are_dropped(self):
        attributes = item('X', attributes={'onclick': 'go()', 'OnMouseOver': 'go()', 'data-on': '1'}).attributes()
        self.assertNotIn('onclick', attributes)
        self.assertNotIn('OnMouseOver', attributes)
        self.assertIn('data-on="1"', attributes)


class EscapeLabelsTests(SimpleTestCase):
    """Off by default."""

    def test_off_leaves_html_labels_alone(self):
        self.assertEqual(item('<b>Bold</b>').name, '<b>Bold</b>')

    @override_settings(DJANGO_MENUS_ESCAPE_LABELS=True)
    def test_on_escapes_labels(self):
        self.assertEqual(item('<b>Bold</b>').name, '&lt;b&gt;Bold&lt;/b&gt;')
        self.assertEqual(item('R&D', font_awesome='fas fa-flask').name, '<i class="fas fa-flask"></i> R&amp;D')

    @override_settings(DJANGO_MENUS_ESCAPE_LABELS=True)
    def test_safe_labels_are_not_escaped(self):
        self.assertEqual(item('<b>Bold</b>', safe=True).name, '<b>Bold</b>')
        self.assertEqual(item(mark_safe('<b>Bold</b>')).name, '<b>Bold</b>')
        self.assertEqual(item(MenuItemDisplay('<b>Bold</b>', safe=True)).name, '<b>Bold</b>')

    @override_settings(DJANGO_MENUS_ESCAPE_LABELS=True)
    def test_button_defaults_still_match(self):
        menu = HtmlMenu(make_request(), 'button_group',
                        button_defaults={'R&D': MenuItemDisplay('Research', 'fas fa-flask')}).add_items(item('R&D'))
        self.assertIn('<i class="fas fa-flask"></i> Research', render_menu(menu))


class HeaderAndBadgeTests(SimpleTestCase):

    def test_off_leaves_html_alone(self):
        self.assertEqual(HeaderItem('<b>Head</b>').render(), '<div class="dropdown-header"><b>Head</b></div>')
        self.assertIn('>R&D</span>', MenuItemBadge(text='R&D', css_class='info').badge_html())

    @override_settings(DJANGO_MENUS_ESCAPE_LABELS=True)
    def test_on_escapes_header_and_badge(self):
        self.assertEqual(HeaderItem('<b>Head</b>').render(), '<div class="dropdown-header">&lt;b&gt;Head&lt;/b&gt;</div>')
        self.assertIn('>R&amp;D</span>', MenuItemBadge(text='R&D', css_class='info').badge_html())

    @override_settings(DJANGO_MENUS_ESCAPE_LABELS=True)
    def test_safe_header_and_badge(self):
        self.assertEqual(HeaderItem('<b>Head</b>', safe=True).render(), '<div class="dropdown-header"><b>Head</b></div>')
        self.assertIn('><i>1</i></span>', MenuItemBadge(text=mark_safe('<i>1</i>'), css_class='info').badge_html())
        self.assertIn('><i>1</i></span>', MenuItemBadge(text='<i>1</i>', css_class='info', safe=True).badge_html())
