"""Bootstrap 4/5 markup selected by the ``CSS_FRAMEWORK`` setting.

The Bootstrap 4 output is pinned byte-for-byte in test_regression; these tests cover the switch itself.
"""
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from django_menus import css_framework
from django_menus.menu import HtmlMenu, MenuItem, MenuItemBadge
from tests.utils import make_request, render_menu

BS4_ONLY = ['ml-auto', 'mr-auto', 'mr-1', 'float-right', 'badge-pill', 'data-placement']


class FrameworkMarkupMixin:

    def setUp(self):
        self.request = make_request()

    def render(self, template, *items, **kwargs):
        return render_menu(HtmlMenu(self.request, template, **kwargs).add_items(*items))

    def context_menu(self):
        return self.render('context', MenuItem('about', 'About', dropdown=['contact']))

    def badge(self):
        return str(MenuItemBadge(text='3', css_class='danger'))

    def tooltip_button(self):
        return self.render('buttons', MenuItem('about', 'About', tooltip='All about us'))


class Bootstrap4Tests(FrameworkMarkupMixin, TestCase):

    def test_default_is_bootstrap4(self):
        self.assertIsInstance(css_framework.css_classes(), css_framework.Bootstrap4Classes)
        self.assertNotIsInstance(css_framework.css_classes(), css_framework.Bootstrap5Classes)

    def test_alignment(self):
        self.assertIn('navbar-nav mr-auto', self.render('base', 'about'))
        self.assertIn('navbar-nav ml-auto', self.render('base', 'about', alignment='right'))

    def test_button_spacing(self):
        self.assertIn('class="mr-1 mb-1 btn', self.render('buttons', 'about'))

    def test_context_menu_caret(self):
        self.assertIn('pt-1 float-right', self.context_menu())

    def test_badge(self):
        self.assertIn('class="badge badge-pill badge-danger"', self.badge())

    def test_tooltip_attribute(self):
        self.assertIn('data-placement="bottom"', self.tooltip_button())


@override_settings(CSS_FRAMEWORK='bootstrap5')
class Bootstrap5Tests(FrameworkMarkupMixin, TestCase):

    def test_alignment(self):
        self.assertIn('navbar-nav me-auto', self.render('base', 'about'))
        self.assertIn('navbar-nav ms-auto', self.render('base', 'about', alignment='right'))

    def test_button_spacing(self):
        self.assertIn('class="me-1 mb-1 btn', self.render('buttons', 'about'))

    def test_context_menu_caret(self):
        self.assertIn('pt-1 float-end', self.context_menu())

    def test_badge(self):
        self.assertIn('class="badge rounded-pill text-bg-danger"', self.badge())

    def test_tooltip_attribute(self):
        html = self.tooltip_button()
        self.assertIn('data-bs-placement="bottom"', html)
        self.assertIn('data-tooltip="tooltip"', html)

    def test_no_bootstrap4_markup(self):
        html = ''.join([self.render('base', 'about'), self.render('base', 'about', alignment='right'),
                        self.render('buttons', 'about'), self.context_menu(), self.badge(),
                        self.tooltip_button()])
        for token in BS4_ONLY:
            self.assertNotIn(token, html)


class FrameworkSettingTests(TestCase):

    @override_settings(CSS_FRAMEWORK='tailwind')
    def test_unknown_framework(self):
        with self.assertRaises(ImproperlyConfigured):
            css_framework.css_classes()


class TooltipTemplateTests(TestCase):

    def test_template_follows_ajax_helpers_version(self):
        html = MenuItem('about', template='django_menus/ajax_tooltip.html', tooltip_name='about',
                        tooltip_class='wide').render()
        if css_framework.AH_TOOLTIPS:
            self.assertIn('<div class="ah-tooltip wide" role="tooltip"><div class="ah-arrow">', html)
        else:
            self.assertIn('<div class="tooltip wide" role="tooltip"><div class="arrow">', html)
        self.assertNotIn('&lt;', html)
