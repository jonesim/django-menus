import datetime
import threading
import time

from django.utils.safestring import mark_safe
from django.views.generic.base import RedirectView
from django_modals.helper import base64_json
from django_modals.modals import Modal

from django_menus.menu.menu import AjaxMenuDropDownItem
from menu_examples.globals import DUMMY_MENU_ID
from show_src_code.modals import BaseSourceCodeModal
from show_src_code.view_mixins import DemoViewMixin

from django_menus.menu import DividerItem, AjaxMenuTemplateView, HtmlMenu, AjaxMenuTabs, MenuItemBadge, \
    MenuItemDisplay
from django_menus.menu import MenuItem
from django_menus.menu.context_menu import ContextMenuMixin
from django_menus.menu.menu_items import HeaderItem


def setup_main_menu(request):
    menu = HtmlMenu(request).add_items(
        'view1',
        ('ajaxtab', 'Ajax Tabs', ),
        ('modal_examples', 'Modal Examples'),
        ('context_examples', 'Context Examples'),
        ('ajax_dropdown_menu_examples', 'Ajax-DropDown Menu Examples'),
        ('repeat_click_examples', 'Repeat Clicks'),
    )
    return menu


class MainMenu(DemoViewMixin, AjaxMenuTemplateView):

    def setup_menu(self):
        super().setup_menu()
        self.menus['main_menu'] = setup_main_menu(self.request)


class AjaxTabExample(MainMenu, AjaxMenuTabs):

    template_name = 'menu_examples/base_ajax_tabs.html'
    tab_template = 'menu_examples/tab_template.html'
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

    tab_template = 'menu_examples/tab_template2.html'


class View1(MainMenu):
    template_name = 'menu_examples/view1.html'
    breadcrumb = ['view1']

    def button_test_button(self, *args, **kwargs):
        return self.command_response('message', text='From view')

    def menu_item_menu(self):
        self.add_menu('menu_items', 'button_group').add_items(
            'string',
            ('string', 'Tuple', {'css_classes': 'btn-secondary'}),
            MenuItem('view1', 'Class'),
        )

    def menu_display_menu(self):
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
            MenuItem('view1', 'edit', tooltip='tooltip'),
            MenuItem('view1', menu_display='', font_awesome='fas fa-pen'),  # just a font awesome icon
            MenuItem('view1', 'global_edit'),  # comes from DJANGO_MENUS_BUTTON_DEFAULTS
            MenuItem('admin:index')
        )

    @staticmethod
    def demo_badge(badge):
        badge.text = datetime.datetime.now().strftime('%S')
        badge.css_class = 'warning'

    def menu_links(self):
        self.add_menu('link_examples', 'button_group').add_items(
            ('view1', 'Simple URL name'),
            ('int_path', 'Path with url args', {'url_args': [1]}),
            ('int_path', 'Path with url kwargs', {'url_kwargs': {'int': 2}}),
            ('int_path', 'Path with url_(name)', {'url_int': 3}),
            MenuItem('int_path', 'Path with menu item url_(name)', url_int=4, badge=MenuItemBadge('demo-badge',
                                                                                         self.demo_badge)),
            ('/view1/#123', 'Raw URL', MenuItem.HREF),
            ("ajax_helpers.post_json({'data': {'button': 'delete'}, 'url': '/modal/company/52/'})", 'Raw URL',
             MenuItem.HREF),

            ("alert('javascript alert')", 'Javascript', MenuItem.JAVASCRIPT),
            ('test_button', 'Send to View', MenuItem.AJAX_BUTTON),
        )

    def button_groups(self):

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
            'view2',
            'view3',
            MenuItem('view4', 'View 4 override', css_classes=['btn-warning'])
        )

    def tab_menu(self):
        self.add_menu('tab_menu', 'tabs').add_items(('view1', {'key': 'a'}), MenuItem('view2', key=['alt-b', 'alt-B'], menu_display='View 2 (ALT b or B)'), 'view3', 'view4')

    def dropdowns(self):
        self.add_menu('dropdown').add_items(
            MenuItem(menu_display='Dropdown', dropdown=('view1', MenuItem('view2', visible=True), 'view3')),
            MenuItem(menu_display='Hidden item', dropdown=('view1', MenuItem('view2', visible=False), 'view3')),
            MenuItem(menu_display='Disabled item', dropdown=('view1', MenuItem('view2', disabled=True), 'view3')),
            MenuItem(menu_display='Divider', dropdown=('view1', 'view2', DividerItem(), 'view3')),
            MenuItem(menu_display='No Caret', show_caret=False, dropdown=('view1', 'view2', 'view3')),
            MenuItem(menu_display='No hover', no_hover=True, dropdown=('view1', 'view2', 'view3')),
        )

    def setup_menu(self):
        super().setup_menu()
        self.menu_item_menu()
        self.menu_display_menu()
        self.menu_links()
        self.button_groups()
        self.tab_menu()

        self.add_menu('main').add_items('view1', 'view2', 'view3', ('view4', 'View 4'))

        self.add_menu('breadcrumb', 'breadcrumb').add_items(*self.breadcrumb)

        self.add_menu('badge').add_items(
            MenuItem('view1', badge=MenuItemBadge('demo_badge_1', self.demo_badge1)),
            MenuItem('view2', badge=MenuItemBadge('demo_badge_2', self.demo_badge2)),
            'view3')
        self.dropdowns()

        self.add_menu('loop_buttons', 'button_group').add_items(
            (f"alert('{DUMMY_MENU_ID}')", 'Test loop id', MenuItem.JAVASCRIPT),
            MenuItem(menu_display='', placement='bottom-end', css_classes='btn-secondary',
                     dropdown=((f"alert('{DUMMY_MENU_ID}')", 'Test loop id', MenuItem.JAVASCRIPT),
                               )))

        self.add_menu('attr', 'button_group').add_items(
            MenuItem('view1', 'Look at link',
                     attributes={'data-toggle': 'hello_world', 'data-target': 'this_world'},
                     query_string_params={'qs': 'foo', 'bar': 'baz'}),
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
    breadcrumb = ['view1', 'view2', 'view3', 'view4']
    menu_display = 'View-3'


class View4(View1):
    breadcrumb = ['view1', 'view2', 'view3', ('view4', 'View4')]
    menu_display = MenuItemDisplay('View4', font_awesome='fas fa-adjust', css_classes=['btn-success'], tooltip='Menu display tool tip')


class SourceCodeModal(BaseSourceCodeModal):
    code = {
        'menu_item': View1.menu_item_menu,
        'menu_display': View1.menu_display_menu,
        'menu_links': View1.menu_links,
        'button_groups': View1.button_groups,
        'tab_menu': View1.tab_menu,
        'dropdowns': View1.dropdowns,
    }


class ModalExamples(MainMenu):
    template_name = 'menu_examples/modal_examples.html'

    def setup_menu(self):
        super().setup_menu()
        self.add_menu('modals', 'buttons').add_items(
            ('test_modal', 'Simple Modal F2', {'key': 'F2'}),
            ('test_modal,XYZ', 'Modal with simple string slug'),
            ('test_modal,key-XYZ', 'Modal with string slug'),
            ('test_modal', 'Modal with url_args (pk) slug', {'url_args': ('ABC',)}),
            ('test_modal', 'Modal with url_args dict slug', {'url_args': ('key-ABC',)}),

            (f'test_modal64,{base64_json({"key-Y": "value"})}', 'base64 params as string'),
            ('test_modal64', 'base64 params as dict', {'url_args': (base64_json({'key-X': 'value'}),)}),

        )


class ContextMenu(ContextMenuMixin, MainMenu):
    template_name = 'menu_examples/context_examples.html'

    def ajax_context_menu(self, *args, **kwargs):
        return self.add_context_menu(HeaderItem('Context Menu'),
                                     'view1', 'view2', 'view3', ('view4', 'View 4'),
                                     MenuItem(menu_display='dropdown ',
                                              dropdown=('view1', 'view2', 'view3', DividerItem(), 'view4'),
                                              show_caret=True,
                                              placement='right-start',
                                              ),
                                     'view3'
                                     )

    def ajax_special_context_menu(self, *args, **kwargs):
        return self.add_context_menu('view1',
                                     'view2',
                                     'view3',

                                    ('test_button', 'Send to View', MenuItem.AJAX_BUTTON))

    def button_test_button(self, *args, **kwargs):
        return self.command_response('message', text='From view')


class RequestCounter:
    """Counts requests the bump view has received, for the repeat-click example below.

    Deliberately NOT in the session. Two requests arriving together each read the session,
    add one, and write it back, so one increment gets lost - which is a genuine race, but a
    different one from the one this page is about, and it made the example quietly under-report
    the double-click it exists to show. A process-global behind a lock counts what actually
    arrived. Shared by everyone using the demo, which is fine for a demo and would not be for
    anything else.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.hits = 0

    def bump(self):
        with self._lock:
            self.hits += 1

    def reset(self):
        with self._lock:
            self.hits = 0


request_counter = RequestCounter()


class RepeatClickExamples(MainMenu):
    """Opting in to the repeat-click guard, and seeing what it does and does not hold.

    A menu item usually points at a view that just shows a page, where clicking twice costs
    nothing. Some point at a view that DOES something, and those are reached twice by a
    double-click - the counter on this page is bumped by one of those.
    """

    template_name = 'menu_examples/repeat_click_examples.html'

    def setup_menu(self):
        super().setup_menu()
        self.menus['main_menu'].active = 'repeat_click_examples'
        self.add_menu('repeat_click', 'button_group').add_items(
            MenuItem('bump_counter', 'Bump the counter', font_awesome='fas fa-plus'),
            # A javascript: item is never held, however short the gap: the page has not gone
            # anywhere, so a second click is not a repeat of a navigation - it is a second
            # action, which is usually exactly what the user wants (close a modal, reopen it).
            MenuItem("alert('Clicked. A javascript: item is never held.')",
                     'A javascript: item',
                     link_type=MenuItem.JAVASCRIPT,
                     css_classes='btn-outline-secondary'),
            MenuItem('reset_counter', 'Reset', css_classes='btn-outline-danger'),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bump_count'] = request_counter.hits
        return context


class BumpCounter(RedirectView):
    """Stands in for a view that acts on a GET and then redirects back.

    Deliberately NOT idempotent - it counts every request it is sent, so a double-click that
    gets through shows up as two. That is the shape the guard is for; the real fix for a view
    like this is to make it idempotent, and the guard is the layer in front of that.

    And deliberately slow. The guard drops a click that repeats a navigation ALREADY UNDER WAY,
    so there has to be a window in which one is. Answering this instantly on a local runserver
    closes that window: the first navigation finishes before the second click of a double-click
    lands, both then count whether the guard is on or off, and the page below demonstrates
    nothing. A real server doing real work supplies the delay; here it is faked.
    """

    pattern_name = 'repeat_click_examples'
    work_seconds = 1

    def get_redirect_url(self, *args, **kwargs):
        request_counter.bump()
        time.sleep(self.work_seconds)
        return super().get_redirect_url(*args, **kwargs)


class ResetCounter(RedirectView):
    pattern_name = 'repeat_click_examples'

    def get_redirect_url(self, *args, **kwargs):
        request_counter.reset()
        return super().get_redirect_url(*args, **kwargs)


class TestModal(Modal):
    button_container_class = 'text-center'

    def modal_content(self):
        return f'Slug {self.slug.__str__()}'


class AjaxDropDownMenu(MainMenu):
    template_name = 'menu_examples/ajax_dropdown_menu_examples.html'

    def setup_menu(self):
        super().setup_menu()
        self.add_menu('menu_items', 'button_group').add_items(
            'string', AjaxMenuDropDownItem(css_classes='btn-success'))

    def ajax_dropdown_menu(self, *args, pos, **kwargs):
        return self.add_ajax_dropdown_menu('view1', 'view2', 'view3', ('view4', 'View 4'), pos=pos)
