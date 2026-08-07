"""Every misconfiguration is reported as a system check and as an exception."""
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.test import TestCase, override_settings

from django_menus.checks import check_menu_registry
from django_menus.menu import registry


@override_settings(ROOT_URLCONF='tests.urls_invalid')
class BrokenDeclarationTests(TestCase):

    def setUp(self):
        registry.clear_cache()
        self.addCleanup(registry.clear_cache)

    def ids(self):
        return [message.id for message in check_menu_registry()]

    def message_for(self, code):
        for message in check_menu_registry():
            if message.id == f'django_menus.{code}':
                return message
        self.fail(f'{code} was not reported. Got: {self.ids()}')

    def test_unknown_section(self):
        self.assertIn('nope', self.message_for('E001').msg)

    def test_unknown_group(self):
        self.assertIn("group 'nope'", self.message_for('E002').msg)

    def test_missing_group_in_a_grouped_section(self):
        codes = [m.msg for m in check_menu_registry() if m.id == 'django_menus.E002']
        self.assertTrue(any('sets no group' in msg for msg in codes), codes)

    def test_ambiguous_url_name(self):
        message = self.message_for('E003')
        self.assertIn('ambiguous_a', message.msg)
        self.assertIn('ambiguous_b', message.msg)

    def test_unknown_url_name(self):
        self.assertIn('not_a_url', self.message_for('E004').msg)

    def test_missing_url_args_from_an_enclosing_include(self):
        message = self.message_for('E005')
        self.assertIn('takes 1 argument(s) but', message.msg)
        self.assertIn('supplies 0', message.msg)

    def test_missing_url_args_is_detected_without_reversing(self):
        with mock.patch('django.urls.reverse', side_effect=AssertionError('reverse() called')):
            self.assertIn('django_menus.E005', self.ids())

    def test_menu_entry_of_the_wrong_type(self):
        self.assertIn('must be a MenuEntry', self.message_for('E006').msg)

    def test_missing_display_is_a_warning(self):
        message = self.message_for('W001')
        self.assertEqual(message.level, 30)
        self.assertIn('NoDisplay', message.msg)

    @override_settings(DJANGO_MENUS_BUTTON_DEFAULTS={'Clashing Button': 'Replaced'})
    def test_button_default_clash_is_a_warning(self):
        registry.clear_cache()
        self.assertIn('Clashing Button', self.message_for('W002').msg)

    def test_scan_raises_as_well_as_reporting(self):
        with self.assertRaises(ImproperlyConfigured) as caught:
            registry.specs('settings')
        message = str(caught.exception)
        for code in ('E001', 'E002', 'E003', 'E004', 'E005', 'E006'):
            self.assertIn(code, message)

    def test_warnings_do_not_raise(self):
        errors = [e for e in registry.validate() if not e.is_error]
        self.assertTrue(errors)
        self.assertTrue(all(e.code.startswith('W') for e in errors))


class ValidUrlConfTests(TestCase):

    def setUp(self):
        registry.clear_cache()
        self.addCleanup(registry.clear_cache)

    def test_no_check_messages(self):
        self.assertEqual(check_menu_registry(), [])

    def test_manage_check_passes(self):
        call_command('check')

    def test_check_never_reverses(self):
        with mock.patch('django.urls.reverse', side_effect=AssertionError('reverse() called')):
            self.assertEqual(check_menu_registry(), [])


@override_settings(ROOT_URLCONF='tests.urls_invalid')
class BadSortTests(TestCase):

    def setUp(self):
        registry.clear_cache()
        self.addCleanup(registry.clear_cache)

    @override_settings(DJANGO_MENUS_SECTIONS={'settings': {'sort': 'sideways'}})
    def test_unknown_sort_option(self):
        registry.clear_cache()
        codes = [m.id for m in check_menu_registry()]
        self.assertIn('django_menus.E007', codes)
