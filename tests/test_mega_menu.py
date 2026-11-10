"""The megamenu: dropdown_template='mega' draws a dropdown as one column per HeaderItem."""
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from django_menus.checks import check_menu_registry
from django_menus.menu import DividerItem, HeaderItem, HtmlMenu, MenuItem, registry
from tests.utils import make_request, render_menu


def mega(request, *items, **kwargs):
    menu = HtmlMenu(request).add_items(MenuItem(menu_display='Mega', dropdown=items, dropdown_template='mega',
                                                **kwargs))
    html = render_menu(menu)
    return menu.menu_items[0].dropdown, html


def column_texts(dropdown):
    return [(header.text if header else None, [i.menu_display.text for i in items])
            for header, items in dropdown.columns()]


class MegaMenuTests(TestCase):

    def setUp(self):
        self.request = make_request()

    def test_a_column_per_header(self):
        dropdown, html = mega(self.request, HeaderItem('One'), 'about', HeaderItem('Two'), 'contact', 'home')
        self.assertEqual(column_texts(dropdown), [('One', ['About Us']), ('Two', ['Contact', 'Home'])])
        self.assertIn('class="dropdown-menu mega-menu"', html)
        self.assertEqual(html.count('class="mega-menu-column"'), 2)
        self.assertIn('<div class="dropdown-header mega-menu-header"><span>One</span></div>', html)

    def test_items_before_the_first_header_have_a_column_without_a_header(self):
        dropdown, html = mega(self.request, 'about', HeaderItem('Two'), 'contact')
        self.assertEqual(column_texts(dropdown), [(None, ['About Us']), ('Two', ['Contact'])])
        self.assertEqual(html.count('mega-menu-header'), 1)

    def test_dividers_are_dropped(self):
        dropdown, html = mega(self.request, HeaderItem('One'), 'about', DividerItem(), 'contact')
        self.assertEqual(column_texts(dropdown), [('One', ['About Us', 'Contact'])])
        self.assertNotIn('dropdown-divider', html)

    def test_a_header_with_nothing_visible_under_it_is_left_out(self):
        dropdown, html = mega(self.request, HeaderItem('Staff'), 'staff_only', HeaderItem('Public'), 'about')
        self.assertEqual(column_texts(dropdown), [('Public', ['About Us'])])
        self.assertNotIn('Staff', html)

    def test_a_hidden_header_column_shows_for_a_user_who_can_see_it(self):
        staff = User.objects.create_user('staff', is_staff=True)
        dropdown, _html = mega(make_request(user=staff), HeaderItem('Staff'), 'staff_only', HeaderItem('Public'),
                               'about')
        self.assertEqual([h for h, _ in column_texts(dropdown)], ['Staff', 'Public'])

    def test_icon_and_colour(self):
        _dropdown, html = mega(self.request, HeaderItem('Money', icon='fas fa-coins', colour='#21965b'), 'about')
        self.assertIn('class="mega-menu-column mega-menu-accent" style="--mega-menu-accent: #21965b"', html)
        self.assertIn('<span class="mega-menu-icon"><i class="fas fa-coins"></i></span><span>Money</span>', html)

    def test_colour_is_escaped(self):
        _dropdown, html = mega(self.request, HeaderItem('X', colour='red"><script>'), 'about')
        self.assertNotIn('<script>"', html)
        self.assertIn('red&quot;&gt;&lt;script&gt;', html)

    def test_positioned_by_the_menu_javascript(self):
        _dropdown, html = mega(self.request, HeaderItem('One'), 'about', placement='bottom-end')
        self.assertIn("dropdown_menu_function('ID1', 'bottom-end')", html)

    def test_tooltips_open_below_not_over_the_next_column(self):
        _dropdown, html = mega(self.request, HeaderItem('One'), MenuItem('about', tooltip='All about us'))
        self.assertIn('data-placement="bottom"', html)

    def test_header_without_text_starts_a_column_without_a_heading(self):
        dropdown, html = mega(self.request, HeaderItem('One'), 'about', HeaderItem(colour='#123456'), 'contact')
        self.assertEqual(column_texts(dropdown), [('One', ['About Us']), (None, ['Contact'])])
        self.assertEqual(html.count('mega-menu-header'), 1)
        self.assertIn('style="--mega-menu-accent: #123456"', html)

    def test_only_headers_visible_hides_the_parent(self):
        _dropdown, html = mega(self.request, HeaderItem('Staff'), 'staff_only')
        self.assertNotIn('mega-menu', html)
        self.assertNotIn('Mega', html)

    def test_color_is_accepted_for_colour(self):
        self.assertEqual(HeaderItem('X', color='#21965b').colour, '#21965b')

    def test_misspelt_option_raises(self):
        with self.assertRaises(TypeError):
            HeaderItem('X', colur='#21965b')

    def test_header_without_text_renders_nothing_in_a_plain_dropdown(self):
        self.assertEqual(HeaderItem(icon='fas fa-coins').render(), '')

    def test_icon_and_colour_leave_the_plain_dropdown_unchanged(self):
        header = HeaderItem('Record', icon='fas fa-coins', colour='#21965b')
        self.assertEqual(header.render(), '<div class="dropdown-header">Record</div>')


@override_settings(DJANGO_MENUS_SECTIONS={
    'settings': {}, 'support': {},
    'reports': {'title': 'Reports', 'mega': True, 'sort': 'order',
                'groups': [('sales', 'Sales', {'icon': 'fas fa-shopping-cart', 'colour': '#1d6fd6'}),
                           ('purchases', 'Purchases'), 'stock', ('company', 'Company')]}})
class RegistryMegaMenuTests(TestCase):

    def setUp(self):
        registry.clear_cache()

    def tearDown(self):
        registry.clear_cache()

    def test_mega_section_uses_the_mega_template(self):
        item = registry.menu_item('reports', make_request())
        self.assertEqual(item.dropdown.template, 'django_menus/mega_dropdown.html')

    def test_group_options_reach_the_header(self):
        headers = [i for i in registry.dropdown('reports', make_request()) if isinstance(i, HeaderItem)]
        sales = next(h for h in headers if h.text == 'Sales')
        self.assertEqual((sales.icon, sales.colour), ('fas fa-shopping-cart', '#1d6fd6'))
        purchases = next(h for h in headers if h.text == 'Purchases')
        self.assertEqual((purchases.icon, purchases.colour), (None, None))

    def test_a_group_without_a_header_gets_its_own_column(self):
        item = registry.menu_item('reports', make_request())
        HtmlMenu(make_request()).add_items(item).render()
        self.assertEqual([header.text for header, _items in item.dropdown.columns()],
                         ['Sales', 'Purchases', None])    # Company is staff-only
        self.assertEqual(column_texts(item.dropdown)[2], (None, ['Stock Valuation']))

    @override_settings(DJANGO_MENUS_SECTIONS={
        'settings': {}, 'support': {},
        'reports': {'mega': True, 'groups': [('sales', None, {'icon': 'fas fa-shopping-cart'}),
                                             'purchases', 'stock', 'company']}})
    def test_options_kept_without_header_text(self):
        registry.clear_cache()
        header = registry.dropdown('reports', make_request())[0]
        self.assertEqual((header.text, header.icon), (None, 'fas fa-shopping-cart'))


class GroupOptionValidationTests(TestCase):

    def setUp(self):
        registry.clear_cache()
        self.addCleanup(registry.clear_cache)

    def check(self, options):
        sections = {'settings': {}, 'support': {},
                    'reports': {'groups': [('sales', 'Sales', options), 'purchases', 'stock', 'company']}}
        with self.settings(DJANGO_MENUS_SECTIONS=sections):
            registry.clear_cache()
            messages = [m for m in check_menu_registry() if m.id == 'django_menus.E008']
            with self.assertRaises(ImproperlyConfigured):
                registry.dropdown('reports', make_request())
        return messages

    def test_options_that_are_not_a_dict(self):
        messages = self.check('fas fa-cart')
        self.assertTrue(messages)
        self.assertIn("'fas fa-cart'", messages[0].msg)

    def test_unknown_option(self):
        messages = self.check({'colur': '#fff'})
        self.assertTrue(messages)
        self.assertIn('colur', messages[0].msg)
