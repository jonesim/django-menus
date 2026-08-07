"""manage.py show_menu."""
import json
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import CommandError, call_command
from django.test import TestCase

from django_menus.menu import registry
from tests.utils import make_request
from tests.views import MenuView


def run(*args, **options):
    out = StringIO()
    call_command('show_menu', *args, stdout=out, **options)
    return out.getvalue()


class ShowMenuTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user('staff', is_staff=True)

    def setUp(self):
        registry.clear_cache()
        self.addCleanup(registry.clear_cache)


class ViewModeTests(ShowMenuTestCase):

    def test_prints_the_whole_menu(self):
        output = run('--view', 'menu_view')
        for expected in ('main_menu', 'Home', 'Reports', 'Settings', 'Support',
                         'Sales Breakdowns', 'Page Info', 'Phone Numbers'):
            self.assertIn(expected, output)

    def test_matches_the_rendered_menu(self):
        """The acceptance criterion: same items, same order, as the view actually renders."""
        view = MenuView()
        view.setup(make_request('/menu/'))
        view.setup_menu()
        menu = view.menus['main_menu']
        menu.render()

        rendered = []

        def collect(items):
            for item in items:
                display = getattr(item, 'menu_display', None)
                if not item.visible or display is None:
                    continue    # dividers and headers carry no display
                rendered.append(display.text)
                dropdown = getattr(item, 'dropdown', None)
                if dropdown is not None:
                    collect(dropdown.menu_items)

        collect(menu.menu_items)

        data = json.loads(run('--view', 'menu_view', format='json'))
        reported = []

        def walk(nodes):
            for node in nodes:
                if node['type'] in ('divider', 'header'):
                    continue
                reported.append(node['label'])
                walk(node.get('items') or ())

        walk(data['menus'][0]['items'])
        self.assertEqual(reported, rendered)

    def test_user_changes_visibility(self):
        self.assertNotIn('Staff Settings', run('--view', 'menu_view'))
        self.assertIn('Staff Settings', run('--view', 'menu_view', user='staff'))

    def test_admin_extra_only_for_staff(self):
        self.assertNotIn('/admin/', run('--view', 'menu_view'))
        self.assertIn('/admin/', run('--view', 'menu_view', user='staff'))

    def test_show_hidden_reveals_items_the_menu_holds(self):
        self.assertNotIn('Staff Only', run('--view', 'menu_view'))
        output = run('--view', 'menu_view', show_hidden=True)
        self.assertIn('Staff Only', output)
        self.assertIn('(hidden)', output)

    def test_menu_filter(self):
        self.assertIn('main_menu', run('--view', 'menu_view', menu='main_menu'))
        with self.assertRaises(CommandError):
            run('--view', 'menu_view', menu='no_such_menu')

    def test_path_instead_of_view(self):
        self.assertIn('main_menu', run('--path', '/menu/'))

    def test_url_arguments_use_comma_syntax(self):
        self.assertIn('/menu/3/', run('--view', 'menu_view_pk,3', format='json'))

    def test_unknown_view(self):
        with self.assertRaises(CommandError):
            run('--view', 'not_a_url')

    def test_view_without_menus(self):
        with self.assertRaises(CommandError):
            run('--view', 'home')

    def test_unknown_user(self):
        with self.assertRaises(CommandError):
            run('--view', 'menu_view', user='nobody')


class RegistryModeTests(ShowMenuTestCase):

    def test_all_sections_by_default(self):
        output = run()
        for section in ('settings', 'support', 'reports'):
            self.assertIn(f"section '{section}'", output)

    def test_named_section(self):
        output = run('support')
        self.assertIn("section 'support'", output)
        self.assertNotIn("section 'settings'", output)

    def test_lists_registered_specs(self):
        """A spec that is registered but not visible is still reported."""
        output = run('settings')
        self.assertIn('tests.views.StaffSettings', output)
        self.assertNotIn('Staff Settings ', output)

    def test_group_and_order_are_shown(self):
        output = run('reports')
        self.assertIn('group=sales order=1', output)
        self.assertIn('groups=sales, purchases, stock, company', output)

    def test_unknown_section(self):
        with self.assertRaises(CommandError):
            run('nope')

    def test_json_shape(self):
        data = json.loads(run('support', format='json'))
        self.assertEqual(data['sections'][0]['section'], 'support')
        self.assertEqual([i['label'] for i in data['sections'][0]['items']],
                         ['Phone Numbers', 'Renamed In Support', 'Support Only'])


class FormattingTests(ShowMenuTestCase):

    def test_ascii_by_default(self):
        output = run('--view', 'menu_view')
        self.assertIn('+-- ', output)
        self.assertNotIn('├──', output)

    def test_unicode_opt_in(self):
        self.assertIn('├──', run('--view', 'menu_view', unicode=True))

    def test_flat_format(self):
        output = run('--view', 'menu_view', format='flat')
        self.assertNotIn('+-- ', output)
        self.assertIn('Reports', output)
