import datetime
from ajax_helpers.mixins import AjaxHelpers
from django_menus.menu import MenuItem, DividerItem, AjaxMenuTemplateView, HtmlMenu, AjaxMenuTabs, MenuItemBadge, \
    MenuItemDisplay
from django.utils.safestring import mark_safe


def setup_main_menu(request):
    menu = HtmlMenu(request).add_items(
        'view1',
        ('ajaxtab', 'Ajax Tabs', ),
    )
    return menu


class MainMenu(AjaxMenuTemplateView):

    def setup_menu(self):
        super().setup_menu()
        self.menus['main_menu'] = setup_main_menu(self.request)


class AjaxTabExample(MainMenu, AjaxMenuTabs):

    template_name = 'base_ajax_tabs.html'
    tab_template = 'tab_template.html'
    additional_content = [('button_menu', AjaxMenuTabs.MENU_CONTENT)]

    def setup_menu(self):
        super().setup_menu()
        self.add_menu('tab_menu', 'tabs').add_items(
            ('ajaxtab', 'Tab1', MenuItem.AJAX_GET_URL_NAME, ),
            MenuItem('content2', 'Tab2', MenuItem.AJAX_GET_URL_NAME, badge=MenuItemBadge('demo-badge',
                                                                                         self.demo_badge)),
        )
        self.menus['main_menu'].active = 'ajaxtab'

        self.add_menu('button_menu', 'button_group').add_items(
            MenuItem('ajaxtab', 'Tab 1'),
            ('content2', 'Tab 2'),
        )

    @staticmethod
    def demo_badge(badge):
        badge.text = datetime.datetime.now().strftime('%S')
        badge.css_class = 'warning'

    def main_context(self, **kwargs):
        return {'main_data': 'Main context'}

    def tab_context(self, **_kwargs):
        return {'tab_data': mark_safe('<h2>Tab context data</h2>')}


class AjaxTabExample2(AjaxTabExample):

    tab_template = 'tab_template2.html'


class View1(MainMenu):
    template_name = 'view1.html'
    breadcrumb = ['view1']

    def button_test_button(self, *args, **kwargs):
        return self.command_response('message', text='From view')

    def setup_menu(self):
        super().setup_menu()

        self.add_menu('menu_items', 'button_group').add_items(
            'string',
            ('string', 'Tuple', {'css_classes': 'btn-secondary'}),
            MenuItem('view1', 'Class'),
        )

        defaults = {'edit': MenuItemDisplay('Edit-default', 'fas fa-pen', 'btn-success')}
        self.add_menu('menu_display', 'button_group', button_defaults=defaults).add_items(
            'url_name',
            ('string', 'String', {'css_classes': ['btn-secondary']}),
            ('string', '<span class="btn-info">HTML<i class="fas fa-code"></i></span>'),
            'view4',
            MenuItem('string', menu_display='String with font_awesome + CSS',
                     font_awesome='fas fa-exclamation-triangle', css_classes=['btn-success']),
            MenuItem('view1', ('Tuple', 'fas fa-exclamation-circle', ['btn-danger'])),
            MenuItem('view1', MenuItemDisplay(text='MenuItemDisplay', css_classes=['btn-dark'])),
            MenuItem('view1', 'edit'),
        )

        self.add_menu('link_examples', 'button_group').add_items(
            ('view1', 'Simple URL name'),
            ('int_path', 'Path with url args', {'url_args': [1]}),
            ('int_path', 'Path with url kwargs', {'url_kwargs': {'int': 2}}),
            ('/view1/', 'Raw URL', MenuItem.HREF),
            ("alert('javascript alert')", 'Javascript', MenuItem.JAVASCRIPT),
            ('test_button', 'Send to View', MenuItem.AJAX_BUTTON),

        )

        self.add_menu('demo', 'button_group').add_items('view1', 'view2', 'view3', 'view4')

        self.add_menu('demo_dropdown', 'button_group').add_items(
            'view1',
            MenuItem(menu_display='All Views', dropdown=('view1', 'view2', 'view3', 'view4')),
            MenuItem(font_awesome='fas fa-info',
                     dropdown=('view1', 'view2', 'view3', DividerItem(), 'view4'),
                     show_caret=False)
        )

        self.add_menu('demo_css', 'button_group').add_items(
            MenuItem('view1', ('View 1', 'fas fa-eye', ['btn-danger'])),
            'view2', 'view3', MenuItem('view4', 'View 4 override', css_classes=['btn-warning']))

        self.add_menu('tab_menu', 'tabs').add_items('view1', 'view2', 'view3', 'view4')
        self.add_menu('main').add_items('view1', 'view2', 'view3', ('view4', 'View 4'))

        self.add_menu('breadcrumb', 'breadcrumb').add_items(*self.breadcrumb)

        self.add_menu('badge').add_items(
            MenuItem('view1', badge=MenuItemBadge('demo_badge_1', self.demo_badge1)),
            MenuItem('view2', badge=MenuItemBadge('demo_badge_2', self.demo_badge2)),
            'view3')

        self.add_menu('dropdown').add_items(
            MenuItem(menu_display='Dropdown', dropdown=('view1', MenuItem('view2', visible=True), 'view3')),
            MenuItem(menu_display='Hidden item', dropdown=('view1', MenuItem('view2', visible=False), 'view3')),
            MenuItem(menu_display='Disabled item', dropdown=('view1', MenuItem('view2', disabled=True), 'view3')),
            MenuItem(menu_display='Divider', dropdown=('view1', 'view2', DividerItem(), 'view3')),
            MenuItem(menu_display='No Caret', show_caret=False, dropdown=('view1', 'view2', 'view3')),
            MenuItem(menu_display='No hover', no_hover=True, dropdown=('view1', 'view2', 'view3')),
        )

    @staticmethod
    def demo_badge1(badge):
        badge.text = datetime.datetime.now().strftime('%S')
        badge.css_class = 'warning'

    @staticmethod
    def demo_badge2(badge):
        badge.text = '!'
        badge.css_class = 'danger'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.__class__.__name__
        return context


class View2(View1):
    breadcrumb = ['view1', 'view2']
    pass


class View3(View1):
    breadcrumb = ['view1', 'view2', 'view3']
    menu_display = 'View-3'


class View4(View1):
    breadcrumb = ['view1', 'view2', 'view3', ('view4', 'View4')]
    menu_display = MenuItemDisplay('View4', font_awesome='fas fa-adjust', css_classes=['btn-success'])