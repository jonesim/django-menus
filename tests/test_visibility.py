"""Callable `visible`, and the interaction between test_visible and visible_items."""
from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase

from django_menus.menu import DividerItem, HtmlMenu, MenuItem
from tests.utils import make_request, render_menu


class CallableVisibleTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user('staff', is_staff=True)

    @staticmethod
    def staff_only(request):
        return request.user.is_staff

    def test_hidden_for_anonymous(self):
        menu = HtmlMenu(make_request()).add_items(
            'home', MenuItem('about', 'About Us', visible=self.staff_only))
        self.assertNotIn('/about/', render_menu(menu))

    def test_shown_for_staff(self):
        menu = HtmlMenu(make_request(user=self.staff)).add_items(
            'home', MenuItem('about', 'About Us', visible=self.staff_only))
        self.assertIn('/about/', render_menu(menu))

    def test_resolved_to_bool_before_visible_items(self):
        """visible_items() filters the raw attribute, so the callable must be gone by then."""
        item = MenuItem('about', 'About Us', visible=self.staff_only)
        menu = HtmlMenu(make_request()).add_items('home', item)
        menu.render()
        self.assertIsInstance(item.visible, bool)
        self.assertNotIn(item, menu.visible_items())

    def test_view_permission_can_still_veto(self):
        """A truthy callable does not bypass the target view's view_permission."""
        item = MenuItem('staff_only', visible=lambda request: True)
        menu = HtmlMenu(make_request()).add_items('home', item)
        menu.render()
        self.assertFalse(item.visible)

    def test_applies_to_base_menu_items(self):
        divider = DividerItem(visible=lambda request: False)
        menu = HtmlMenu(make_request()).add_items('home', divider)
        self.assertNotIn('dropdown-divider', render_menu(menu))

    def test_callable_receives_the_request(self):
        seen = []
        request = make_request()
        HtmlMenu(request).add_items(MenuItem('about', 'About', visible=seen.append)).render()
        self.assertEqual(seen, [request])


class ExistingVisibleBehaviourTests(TestCase):
    """resolve_visible must be a no-op for every pre-existing caller."""

    def test_bool_true_unchanged(self):
        item = MenuItem('about', 'About Us')
        self.assertTrue(item.test_visible(make_request()))

    def test_bool_false_unchanged(self):
        item = MenuItem('about', 'About Us', visible=False)
        self.assertFalse(item.test_visible(make_request()))

    def test_base_menu_item_still_reports_visible(self):
        self.assertTrue(DividerItem().test_visible(make_request()))
        self.assertTrue(DividerItem(visible=False).test_visible(make_request()))


class AdminIndexTests(TestCase):
    """django.contrib.admin's index has no view_class, so only the callable governs it."""

    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user('staff', is_staff=True)

    def build(self, user):
        return render_menu(HtmlMenu(make_request(user=user)).add_items(
            'home', MenuItem('admin:index', 'Admin', visible=lambda r: r.user.is_staff)))

    def test_hidden_for_anonymous(self):
        self.assertNotIn('/admin/', self.build(AnonymousUser()))

    def test_shown_for_staff(self):
        self.assertIn('/admin/', self.build(self.staff))
