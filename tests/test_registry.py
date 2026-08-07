"""The menu registry: scanning, ordering, grouping and per-request materialisation."""
from unittest import mock

from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from django_menus.menu import DividerItem, HeaderItem, HtmlMenu, MenuItem, registry
from tests.utils import make_request, render_menu


def texts(items):
    """Readable representation of a dropdown - dividers and headers included."""
    result = []
    for item in items:
        if isinstance(item, DividerItem):
            result.append('---')
        elif isinstance(item, HeaderItem):
            result.append(f'# {item.text}')
        else:
            result.append(item.menu_display.text)
    return result


class RegistryTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user('staff', is_staff=True)

    def setUp(self):
        registry.clear_cache()
        self.addCleanup(registry.clear_cache)


class ScanTests(RegistryTestCase):

    def test_collects_declared_views(self):
        found = [spec.view_class.__name__ for spec in registry.specs('settings')]
        self.assertCountEqual(found, ['ZebraSettings', 'AppleSettings', 'MangoSettings',
                                      'StaffSettings', 'MultiSection'])

    def test_ignores_views_without_an_entry(self):
        self.assertNotIn('HomeView', [s.view_class.__name__ for s in registry.specs('settings')])

    def test_namespaced_url_name_is_reconstructed(self):
        names = [spec.url_name for spec in registry.specs('support')]
        self.assertIn('phone_numbers:phone_numbers', names)

    def test_scan_reports_no_errors_for_the_fixture_urlconf(self):
        self.assertEqual([str(e) for e in registry.validate('tests.urls')], [])

    def test_multi_section_view_appears_in_both(self):
        self.assertIn('MultiSection', [s.view_class.__name__ for s in registry.specs('settings')])
        self.assertIn('MultiSection', [s.view_class.__name__ for s in registry.specs('support')])

    def test_scan_never_reverses(self):
        with mock.patch('django.urls.reverse', side_effect=AssertionError('reverse() called')):
            with mock.patch('django_menus.menu.menu_items.reverse',
                            side_effect=AssertionError('reverse() called')):
                registry.clear_cache()
                self.assertTrue(registry.specs('settings'))

    def test_scan_never_builds_menu_items(self):
        with mock.patch.object(registry.MenuSpec, 'menu_item',
                               side_effect=AssertionError('MenuItem built')):
            registry.clear_cache()
            self.assertTrue(registry.specs('reports'))

    def test_unknown_section_raises(self):
        with self.assertRaises(ImproperlyConfigured):
            registry.specs('no_such_section')

    def test_app_ready_neither_scans_nor_reverses(self):
        from django.apps import apps
        config = apps.get_app_config('django_menus')
        with mock.patch.object(registry, 'scan', side_effect=AssertionError('scanned')):
            with mock.patch('django.urls.reverse', side_effect=AssertionError('reverse()')):
                config.ready()


class AlphabeticalTests(RegistryTestCase):

    def test_sorted_case_insensitively(self):
        items = registry.dropdown('settings', make_request(user=self.staff))
        self.assertEqual(texts(items),
                         ['apple', 'Mango', 'Multi Section', 'Staff Settings', 'Zebra'])

    def test_declaration_order_is_not_used(self):
        """The URLConf declares zebra, apple, mango in that order."""
        items = registry.dropdown('settings', make_request(user=self.staff))
        self.assertNotEqual(texts(items)[:3], ['Zebra', 'apple', 'Mango'])

    def test_display_override_wins(self):
        items = registry.dropdown('support', make_request())
        self.assertEqual(texts(items), ['Phone Numbers', 'Renamed In Support', 'Support Only'])

    def test_display_override_leaves_the_view_alone(self):
        """The view's own menu_display still drives tabs and breadcrumbs."""
        from tests.views import MultiSection, SalesBreakdown
        self.assertEqual(MultiSection.menu_display, 'Multi Section')
        self.assertEqual(SalesBreakdown.menu_display, 'Distributors')

    def test_no_dividers_in_an_ungrouped_section(self):
        items = registry.dropdown('settings', make_request(user=self.staff))
        self.assertFalse(any(isinstance(i, DividerItem) for i in items))


class GroupedTests(RegistryTestCase):

    def test_group_order_comes_from_settings(self):
        items = registry.dropdown('reports', make_request(user=self.staff))
        self.assertEqual(texts(items), [
            'Sales Totals', 'Sales Breakdowns',
            '---', 'Purchase Totals',
            '---', 'Stock Staff Only', 'Stock Valuation',
            '---', '# Company', 'Company Performance',
        ])

    def test_explicit_order_beats_alphabetical(self):
        items = texts(registry.dropdown('reports', make_request(user=self.staff)))
        self.assertEqual(items[:2], ['Sales Totals', 'Sales Breakdowns'])

    @override_settings(DJANGO_MENUS_SECTIONS={
        'settings': {}, 'support': {},
        'reports': {'groups': ['sales', 'purchases', 'stock', ('company', 'Company')]}})
    def test_alphabetical_within_group(self):
        registry.clear_cache()
        items = texts(registry.dropdown('reports', make_request(user=self.staff)))
        self.assertEqual(items[:2], ['Sales Breakdowns', 'Sales Totals'])

    def test_empty_trailing_group_drops_its_divider(self):
        items = texts(registry.dropdown('reports', make_request()))
        self.assertEqual(items, [
            'Sales Totals', 'Sales Breakdowns',
            '---', 'Purchase Totals',
            '---', 'Stock Valuation',
        ])

    @override_settings(DJANGO_MENUS_SECTIONS={
        'settings': {}, 'support': {},
        'reports': {'groups': [('company', 'Company'), 'sales', 'purchases', 'stock'],
                    'sort': 'order'}})
    def test_empty_leading_group_drops_its_divider(self):
        registry.clear_cache()
        items = texts(registry.dropdown('reports', make_request()))
        self.assertEqual(items[0], 'Sales Totals')
        self.assertNotIn('# Company', items)

    def test_header_only_shown_when_the_group_has_items(self):
        self.assertNotIn('# Company', texts(registry.dropdown('reports', make_request())))
        self.assertIn('# Company', texts(registry.dropdown('reports',
                                                           make_request(user=self.staff))))

    def test_never_two_adjacent_dividers(self):
        for request in (make_request(), make_request(user=self.staff)):
            items = texts(registry.dropdown('reports', request))
            self.assertNotIn('---', items[:1])
            for first, second in zip(items, items[1:]):
                self.assertFalse(first == '---' and second == '---')


class UrlArgumentTests(RegistryTestCase):

    def test_url_args_are_applied(self):
        items = registry.dropdown('reports', make_request(user=self.staff))
        breakdown = next(i for i in items if getattr(i, 'menu_display', None)
                         and i.menu_display.text == 'Sales Breakdowns')
        self.assertEqual(breakdown.href(), '/reports/breakdown/2026/')

    def test_the_fixture_really_needs_the_argument(self):
        from django.urls import NoReverseMatch, reverse
        with self.assertRaises(NoReverseMatch):
            reverse('sales_breakdown')


class ExtraItemTests(RegistryTestCase):

    def test_extras_sort_by_display_text(self):
        button = MenuItem('page_info', 'Page Info', link_type=MenuItem.AJAX_BUTTON)
        items = registry.dropdown('settings', make_request(user=self.staff), button)
        self.assertEqual(texts(items),
                         ['apple', 'Mango', 'Multi Section', 'Page Info', 'Staff Settings', 'Zebra'])

    def test_ajax_button_extra_is_never_reversed(self):
        """'page_info' is not a url name at all."""
        from django.urls import NoReverseMatch, reverse
        with self.assertRaises(NoReverseMatch):
            reverse('page_info')

    def test_extra_with_callable_visible(self):
        def build(user):
            item = MenuItem('admin:index', 'Admin', visible=lambda r: r.user.is_staff)
            return texts(registry.dropdown('settings', make_request(user=user), item))

        self.assertIn('Admin', build(self.staff))
        self.assertNotIn('Admin', build(None))

    def test_sort_text_override(self):
        item = registry.extra(MenuItem('about', 'About Us'), sort_text='zzz')
        items = registry.dropdown('settings', make_request(user=self.staff), item)
        self.assertEqual(texts(items)[-1], 'About Us')

    def test_extra_placed_in_a_group(self):
        item = registry.extra(MenuItem('about', 'About Us'), group='purchases')
        items = texts(registry.dropdown('reports', make_request(user=self.staff), item))
        self.assertEqual(items[2:5], ['---', 'About Us', 'Purchase Totals'])

    def test_extra_in_an_unknown_group_raises(self):
        item = registry.extra(MenuItem('about', 'About Us'), group='nope')
        with self.assertRaises(ImproperlyConfigured):
            registry.dropdown('reports', make_request(user=self.staff), item)


class MenuItemTests(RegistryTestCase):

    def test_parent_uses_the_section_title(self):
        item = registry.menu_item('reports', make_request(user=self.staff))
        self.assertEqual(item.menu_display.text, 'Reports')
        self.assertTrue(item.dropdown)

    def test_parent_title_defaults_to_the_section_name(self):
        item = registry.menu_item('support', make_request())
        self.assertEqual(item.menu_display.text, 'Support')

    def test_parent_hidden_when_nothing_is_visible(self):
        with mock.patch.object(registry, 'specs', return_value=[]):
            item = registry.menu_item('support', make_request())
        self.assertFalse(item.visible)

    def test_renders_inside_a_menu(self):
        menu = HtmlMenu(make_request()).add_items(
            'home', registry.menu_item('support', make_request()))
        html = render_menu(menu)
        self.assertIn('Renamed In Support', html)
        self.assertIn('Support Only', html)

    def test_render_is_idempotent(self):
        def build():
            return render_menu(HtmlMenu(make_request()).add_items(
                registry.menu_item('reports', make_request())))

        self.assertEqual(build(), build())

    def test_view_permission_is_evaluated_twice_per_surviving_item(self):
        """Documented cost: once when the registry filters, once when the menu renders.

        Hidden items are only evaluated once - test_visible short circuits on `visible` being
        False, so nothing can flip back into view.
        """
        from tests.views import StockStaffOnly, StockValuation
        counted = {}
        for view_class, allowed in ((StockValuation, True), (StockStaffOnly, False)):
            patched = mock.Mock(return_value=allowed)
            patcher = mock.patch.object(view_class, 'view_permission', patched, create=True)
            patcher.start()
            self.addCleanup(patcher.stop)
            counted[view_class.__name__] = patched

        HtmlMenu(make_request()).add_items(registry.menu_item('reports', make_request())).render()

        self.assertEqual({name: patched.call_count for name, patched in counted.items()},
                         {'StockValuation': 2, 'StockStaffOnly': 1})


class CacheTests(RegistryTestCase):

    def test_scan_is_cached(self):
        registry.specs('settings')
        with mock.patch.object(registry, 'scan', side_effect=AssertionError('rescanned')):
            registry.specs('settings')

    @override_settings(ROOT_URLCONF='tests.urls_alt')
    def test_cache_is_keyed_on_root_urlconf(self):
        self.assertEqual(registry.specs('settings'), [])

    def test_reverting_root_urlconf_restores_the_specs(self):
        with override_settings(ROOT_URLCONF='tests.urls_alt'):
            self.assertEqual(registry.specs('settings'), [])
        self.assertTrue(registry.specs('settings'))

    @override_settings(DJANGO_MENUS_SECTIONS={'settings': {}, 'support': {}, 'reports': {}})
    def test_changing_sections_takes_effect(self):
        """reports is no longer grouped, so its entries' groups become invalid."""
        with self.assertRaises(ImproperlyConfigured):
            registry.specs('reports')
