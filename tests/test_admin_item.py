"""AdminMenuItem."""
from django.contrib.admin.utils import quote
from django.contrib.auth.models import Permission, User
from django.contrib.sessions.models import Session
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from django.utils import timezone

from django_menus.menu import AdminMenuItem, HtmlMenu, MenuItemDisplay
from tests.urls_admin import other_site
from tests.utils import make_request, render_menu


@override_settings(ROOT_URLCONF='tests.urls_admin')
class AdminMenuItemTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.target = User.objects.create_user('target')
        cls.locked = User.objects.create_user('locked')
        cls.superuser = User.objects.create_superuser('super')
        cls.staff = User.objects.create_user('staff', is_staff=True)
        cls.viewer = User.objects.create_user('viewer', is_staff=True)
        cls.viewer.user_permissions.add(Permission.objects.get(codename='view_user'))
        cls.inactive = User.objects.create_superuser('inactive', is_active=False)

    def render(self, item, user):
        return render_menu(HtmlMenu(make_request('/admin/', user=user), 'button_group').add_items(item))

    def test_links_to_the_change_page(self):
        html = self.render(AdminMenuItem(self.target), self.superuser)
        self.assertIn(f'href="/admin/auth/user/{self.target.pk}/change/"', html)
        self.assertIn('fas fa-tools', html)
        self.assertIn('title="Django Admin"', html)

    def test_hidden_from_non_staff(self):
        self.assertNotIn('Django Admin', self.render(AdminMenuItem(self.target), self.target))

    def test_hidden_from_inactive_superuser(self):
        self.assertNotIn('Django Admin', self.render(AdminMenuItem(self.target), self.inactive))

    def test_hidden_from_staff_without_permission(self):
        self.assertNotIn('Django Admin', self.render(AdminMenuItem(self.target), self.staff))

    def test_view_permission_is_enough(self):
        self.assertIn('/admin/auth/user/', self.render(AdminMenuItem(self.target), self.viewer))

    def test_model_admin_object_permission_is_respected(self):
        self.assertIn('/other-admin/auth/user/', self.render(AdminMenuItem(self.target, site=other_site),
                                                             self.superuser))
        self.assertNotIn('Django Admin', self.render(AdminMenuItem(self.locked, site=other_site), self.superuser))

    def test_site_by_name(self):
        html = self.render(AdminMenuItem(self.target, site='other_admin'), self.superuser)
        self.assertIn(f'href="/other-admin/auth/user/{self.target.pk}/change/"', html)

    def test_unknown_site_raises(self):
        with self.assertRaises(ImproperlyConfigured):
            AdminMenuItem(self.target, site='missing')

    def test_pk_is_admin_quoted(self):
        session = Session.objects.create(session_key='a_b/c', session_data='', expire_date=timezone.now())
        html = self.render(AdminMenuItem(session, site=other_site), self.superuser)
        self.assertIn(f'href="/other-admin/sessions/session/{quote(session.pk)}/change/"', html)

    def test_visible_narrows_further(self):
        item = AdminMenuItem(self.target, visible=lambda request: request.user.username == 'nobody')
        self.assertNotIn('Django Admin', self.render(item, self.superuser))

    def test_visibility_rechecked_per_request(self):
        item = AdminMenuItem(self.target)
        self.assertIn('Django Admin', self.render(item, self.superuser))
        self.assertNotIn('Django Admin', self.render(item, self.target))
        self.assertIn('Django Admin', self.render(item, self.superuser))

    def test_unregistered_model_is_hidden(self):
        session = Session(session_key='x')
        self.assertNotIn('Django Admin', self.render(AdminMenuItem(session), self.superuser))

    def test_unsaved_object_is_hidden(self):
        self.assertNotIn('Django Admin', self.render(AdminMenuItem(User(username='new')), self.superuser))

    def test_unsaved_object_with_pk_is_hidden(self):
        """A pk set before saving (e.g. a UUIDField default) doesn't make the object exist."""
        self.assertNotIn('Django Admin', self.render(AdminMenuItem(User(pk=9999, username='new')), self.superuser))

    def test_label(self):
        self.assertIn('</i> Admin<', self.render(AdminMenuItem(self.target, 'Admin'), self.superuser))

    def test_none_label_is_icon_only(self):
        html = self.render(AdminMenuItem(self.target, None), self.superuser)
        self.assertIn('aria-label="Django Admin"', html)
        self.assertNotIn('User_change', html)

    def test_tuple_icon_is_kept(self):
        html = self.render(AdminMenuItem(self.target, ('Admin', 'fas fa-cog')), self.superuser)
        self.assertIn('fas fa-cog', html)
        self.assertNotIn('fas fa-tools', html)

    def test_tuple_without_icon_gets_default(self):
        self.assertIn('fas fa-tools', self.render(AdminMenuItem(self.target, ('Admin',)), self.superuser))

    def test_menu_item_display_is_used_as_is(self):
        html = self.render(AdminMenuItem(self.target, MenuItemDisplay('Admin', 'fas fa-cog')), self.superuser)
        self.assertIn('fas fa-cog', html)
        self.assertNotIn('fas fa-tools', html)
