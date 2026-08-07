from django.views.generic import TemplateView

from django_menus.menu import MenuEntry, MenuItem, MenuItemDisplay, MenuTemplateView, registry


class BaseView(TemplateView):
    template_name = 'does_not_need_to_exist.html'


class HomeView(BaseView):
    pass


class AboutView(BaseView):
    menu_display = 'About Us'


class ContactView(BaseView):
    menu_display = MenuItemDisplay('Contact', 'fas fa-envelope')


class ConfigView(BaseView):
    menu_display = 'Configured'
    menu_config = {'attributes': {'data-role': 'config'}}


class StaffOnlyView(BaseView):
    menu_display = 'Staff Only'

    @classmethod
    def view_permission(cls, request, menu_item=None):
        return bool(request and request.user.is_staff)


class MonthReport(BaseView):
    menu_display = 'Month Report'


class MultiName(BaseView):
    """Reachable under two url names - ambiguous unless an entry names one."""
    menu_display = 'Multi Name'


class PhoneList(BaseView):
    """Registered under a namespaced url name."""
    menu_display = 'Phone Numbers'
    menu_entry = MenuEntry('support')


class NestedDetail(BaseView):
    """Lives under an include() that itself captures a url argument."""
    menu_display = 'Nested Detail'


class MenuView(MenuTemplateView):
    """The end to end fixture: a registry driven main menu with per-request extras."""
    template_name = 'does_not_need_to_exist.html'

    def setup_menu(self):
        self.add_menu('main_menu').add_items(
            'home',
            MenuItem('staff_only'),
            registry.menu_item('reports', self.request),
            registry.menu_item(
                'settings', self.request,
                MenuItem('page_info', 'Page Info', link_type=MenuItem.AJAX_BUTTON),
                MenuItem('admin:index', 'Admin', visible=lambda r: r.user.is_staff)),
            registry.menu_item('support', self.request),
        )


# --------------------------------------------------------------------------- registry fixtures
# Declared out of alphabetical order on purpose, so ordering tests cannot pass by accident.

class ZebraSettings(BaseView):
    menu_display = 'Zebra'
    menu_entry = MenuEntry('settings')


class AppleSettings(BaseView):
    menu_display = 'apple'
    menu_entry = MenuEntry('settings')


class MangoSettings(BaseView):
    menu_display = 'Mango'
    menu_entry = MenuEntry('settings')


class StaffSettings(BaseView):
    """Only visible to staff, so a section can be emptied per request."""
    menu_display = 'Staff Settings'
    menu_entry = MenuEntry('settings')

    @classmethod
    def view_permission(cls, request, menu_item=None):
        return bool(request and request.user.is_staff)


class SupportOnly(BaseView):
    menu_display = 'Support Only'
    menu_entry = MenuEntry('support')


class SalesTotals(BaseView):
    menu_display = 'Sales Totals'
    menu_entry = MenuEntry('reports', 'sales', order=1)


class SalesBreakdown(BaseView):
    """A report whose url takes an argument, with a menu-only display override.

    order=2 puts it after Sales Totals, which alphabetical ordering would not.
    """
    menu_display = 'Distributors'
    menu_entry = MenuEntry('reports', 'sales', display='Sales Breakdowns', url_args=[2026],
                           order=2)


class PurchaseTotals(BaseView):
    menu_display = 'Purchase Totals'
    menu_entry = MenuEntry('reports', 'purchases')


class StockValuation(BaseView):
    menu_display = 'Stock Valuation'
    menu_entry = MenuEntry('reports', 'stock')


class StockStaffOnly(BaseView):
    menu_display = 'Stock Staff Only'
    menu_entry = MenuEntry('reports', 'stock')

    @classmethod
    def view_permission(cls, request, menu_item=None):
        return bool(request and request.user.is_staff)


class CompanyStaffOnly(BaseView):
    """The only member of the last reports group, so that group empties for anonymous users."""
    menu_display = 'Company Performance'
    menu_entry = MenuEntry('reports', 'company')

    @classmethod
    def view_permission(cls, request, menu_item=None):
        return bool(request and request.user.is_staff)


class MultiSection(BaseView):
    """One view in two sections, with a different label in each."""
    menu_display = 'Multi Section'
    menu_entry = [MenuEntry('settings'), MenuEntry('support', display='Renamed In Support')]
