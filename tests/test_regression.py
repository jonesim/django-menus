"""Baseline for the existing public API.

Every documented ``add_items`` form and every menu template is pinned to its exact rendered
output.  The menu registry is purely additive, so any diff here is a regression.
"""
from django.test import TestCase

from django_menus.menu import (AjaxButtonMenuItem, DividerItem, HeaderItem, HtmlMenu, HtmlMenuItem,
                               MenuItem)
from tests.utils import make_request, render_menu
from tests.views import HomeView

NAV = '<ul class="navbar-nav mr-auto">'
LI = '<li  class="nav-item" style="position: relative" >'


def nav(*links):
    return NAV + ''.join(f'{LI}<a class="nav-link {c}" href="{h}"><span>{t}</span></a></li>'
                         for c, h, t in links) + '</ul>'


class AddItemsTests(TestCase):
    """The shorthand forms accepted by HtmlMenu.add_items."""

    def setUp(self):
        self.request = make_request()

    def test_string_shorthand(self):
        menu = HtmlMenu(self.request).add_items('home', 'about', 'contact')
        self.assertEqual(render_menu(menu), nav(
            ('active ', '/home/', 'Home'),
            ('', '/about/', 'About Us'),
            ('', '/contact/', '<i class="fas fa-envelope"></i> Contact'),
        ))

    def test_tuple_shorthand(self):
        menu = HtmlMenu(self.request).add_items(
            ('about', 'About Us'),
            ('contact', 'Contact', {'css_classes': 'btn-primary'}),
        )
        self.assertEqual(render_menu(menu), nav(
            ('', '/about/', 'About Us'),
            ('btn-primary', '/contact/', 'Contact'),
        ))

    def test_tuple_with_link_type(self):
        menu = HtmlMenu(self.request).add_items(('about', 'About Us', MenuItem.AJAX_GET_URL_NAME))
        self.assertEqual(render_menu(menu), nav(
            ('', "javascript: ajax_helpers.get_content('/about/')", 'About Us'),
        ))

    def test_menu_item_instances(self):
        menu = HtmlMenu(self.request).add_items(
            MenuItem('about', 'About Us', font_awesome='fas fa-info', tooltip='All about us'),
            MenuItem('contact', link_type=MenuItem.AJAX_GET_URL_NAME),
        )
        self.assertEqual(render_menu(menu), nav(
            ('', '/about/', '<i class="fas fa-info"></i> About Us'),
            ('', "javascript: ajax_helpers.get_content('/contact/')",
             '<i class="fas fa-envelope"></i> Contact'),
        ))

    def test_html_menu_item(self):
        menu = HtmlMenu(self.request).add_items(HtmlMenuItem(html='<span class="navbar-text">v2.1</span>'))
        self.assertEqual(render_menu(menu), NAV + '<span class="navbar-text">v2.1</span></ul>')

    def test_ajax_button_menu_item(self):
        menu = HtmlMenu(self.request).add_items(AjaxButtonMenuItem('refresh', 'Refresh'))
        self.assertEqual(render_menu(menu), nav(
            ('', "javascript:ajax_helpers.post_json({'data': {'button': 'refresh'}})", 'Refresh'),
        ))

    def test_view_instance(self):
        view = HomeView()
        view.request = make_request('/home/')
        view.menu_display = 'Home Instance'
        menu = HtmlMenu(self.request).add_items(view)
        self.assertEqual(render_menu(menu), nav(('active ', '/home/', 'Home Instance')))


class UrlResolutionTests(TestCase):
    """URL argument and namespace handling."""

    def setUp(self):
        self.request = make_request()

    def test_comma_url_args(self):
        menu = HtmlMenu(self.request).add_items(MenuItem('month_report,3', 'March'))
        self.assertEqual(render_menu(menu), nav(('', '/month/3/', 'March')))

    def test_explicit_url_args(self):
        menu = HtmlMenu(self.request).add_items(MenuItem('month_report', 'March', url_args=[3]))
        self.assertEqual(render_menu(menu), nav(('', '/month/3/', 'March')))

    def test_namespaced_url_name(self):
        menu = HtmlMenu(self.request).add_items('phone_numbers:phone_numbers')
        self.assertEqual(render_menu(menu), nav(('', '/phones/list/', 'Phone Numbers')))

    def test_menu_display_falls_back_to_capitalised_url_name(self):
        menu = HtmlMenu(self.request).add_items('home')
        self.assertEqual(render_menu(menu), nav(('active ', '/home/', 'Home')))


class VisibilityTests(TestCase):

    def test_view_permission_hides_item(self):
        menu = HtmlMenu(make_request()).add_items('home', 'staff_only')
        self.assertEqual(render_menu(menu), nav(('active ', '/home/', 'Home')))

    def test_empty_menu_renders_nothing(self):
        menu = HtmlMenu(make_request()).add_items('staff_only')
        self.assertEqual(render_menu(menu), '')

    def test_empty_dropdown_hides_parent(self):
        # An item whose dropdown renders empty is hidden (menu.py:87-88), but `no_items` has
        # already been cleared by then, so the empty container is still emitted.
        item = MenuItem(menu_display='Hidden', dropdown=('staff_only',))
        menu = HtmlMenu(make_request()).add_items(item)
        self.assertEqual(render_menu(menu), NAV + '</ul>')
        self.assertFalse(item.visible)


class DropdownTests(TestCase):

    def test_dropdown_with_header_and_divider(self):
        menu = HtmlMenu(make_request()).add_items(
            MenuItem(menu_display='Actions', dropdown=(
                HeaderItem('Record'),
                'about',
                DividerItem(),
                ('contact', 'Contact Us'),
            )),
        )
        html = render_menu(menu)
        self.assertIn('<li id="ID1" class="nav-item" style="position: relative" >'
                      '<a class="nav-link " href="javascript:void(0)">'
                      '<span class="dropdown-toggle">Actions</span></a></li>', html)
        self.assertIn('<div id=\'ID1-menu\' class="dropdown-menu" role="menu">'
                      '<div class="dropdown-header">Record</div>'
                      '<a  class="dropdown-item " href="/about/" >About Us</a>'
                      '<div class="dropdown-divider"></div>'
                      '<a  class="dropdown-item " href="/contact/" >Contact Us</a>'
                      '</div>', html)
        self.assertIn("dropdown_menu_function($('#ID1'), 'bottom-start')", html)


class TemplateTests(TestCase):
    """One assertion per menu template, so a template edit cannot pass unnoticed."""

    def setUp(self):
        self.request = make_request()

    def test_button_group(self):
        menu = HtmlMenu(self.request, 'button_group').add_items(('about', 'About Us'))
        self.assertEqual(render_menu(menu),
                         '<div class="btn-group"><a  href="/about/"\n'
                         '               class="btn btn-primary" ><span >About Us</span></a></div>')

    def test_breadcrumb(self):
        menu = HtmlMenu(self.request, 'breadcrumb').add_items('home', 'about')
        self.assertEqual(render_menu(menu),
                         '<nav aria-label="breadcrumb"><ol class="breadcrumb">'
                         '<li class="breadcrumb-item active" aria-current="page">Home</li>'
                         '<li class="breadcrumb-item"><a href="/about/"\n'
                         '                               class="" >About Us</a></li></ol></nav>')

    def test_tabs(self):
        menu = HtmlMenu(self.request, 'tabs').add_items('home', 'about')
        self.assertEqual(render_menu(menu),
                         '<ul class="nav nav-tabs">'
                         '<li class="nav-item"><a class="nav-link active" href="/home/" >Home</a></li>'
                         '<li class="nav-item"><a class="nav-link" href="/about/" >About Us</a></li>'
                         '</ul>\n')

    def test_buttons(self):
        menu = HtmlMenu(self.request, 'buttons').add_items('about')
        self.assertEqual(render_menu(menu),
                         '<div><a  href="/about/"\n'
                         '               class="mr-1 mb-1 btn btn-primary" ><span >About Us</span></a></div>')


class MenuConfigTests(TestCase):

    def test_menu_config_attributes(self):
        menu = HtmlMenu(make_request(), 'button_group').add_items('config')
        self.assertIn('data-role="config"', render_menu(menu))
