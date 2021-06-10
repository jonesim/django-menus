from collections import namedtuple
from django.views.generic import TemplateView
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.urls import reverse, resolve, Resolver404
from ajax_helpers.mixins import AjaxHelpers
from ajax_helpers.templatetags.ajax_helpers import button_javascript
from ajax_helpers.utils import random_string


class MenuItemBadge:

    def __init__(self, badge_id, format_function):
        self.id = badge_id
        self.text = None
        self.css_class = None
        self.format_function = format_function

    def badge_html(self):
        self.format_function(self)
        if self.text:
            return mark_safe(f'<sup class="badge badge-pill badge-{self.css_class}">{self.text}</sup>')
        return ''

    def __str__(self):
        return mark_safe(f'<span id="{self.id}">{self.badge_html()}<span>')


class BaseMenuItem:

    def __init__(self, disabled=False, visible=True, css_classes=None, **kwargs):
        self.disabled = disabled
        self.visible = visible
        if css_classes is None:
            self.css_classes = []
        else:
            self.css_classes = css_classes

    def css(self):
        classes = self.css_classes
        if self.disabled:
            classes += ['disabled']
        return ' '.join(classes)


class DividerItem(BaseMenuItem):

    default_render = False

    @staticmethod
    def render():
        return mark_safe('<div class="dropdown-divider"></div>')


class MenuItem(BaseMenuItem):

    HREF = 0
    AJAX_GET_URL_NAME = 1
    URL_NAME = 2
    AJAX_BUTTON = 3
    JAVASCRIPT = 4

    def __init__(self, name, url=None, menu=None, link_type=URL_NAME, template=None, badge=None, target=None,
                 dropdown=None,  **kwargs):
        super().__init__(**kwargs)

        self.name = mark_safe(name)
        self.url = url
        self.link_type = link_type
        self.kwargs = kwargs
        self.template = template
        self.menu = menu
        self.target = target
        self._badge = badge

        if dropdown:
            self.dropdown = HtmlMenu(template_name='django_menus/dropdown.html').add_items(*dropdown)
            self.css_classes.append('dropdown-toggle')
        if self.template:
            self.default_render = False
        else:
            self.default_render = True

    @property
    def active(self):
        if self.menu.active:
            try:
                resolved_url = resolve(self.raw_href())
                url_name = resolved_url.url_name
                if resolved_url.namespace:
                    url_name = f'{resolved_url.namespace}:{url_name}'
                if url_name == self.menu.active:
                    return True
            except Resolver404:
                return
        else:
            if (self.link_type in [self.URL_NAME, self.AJAX_GET_URL_NAME, self.HREF]
                    and self.menu.request.path == self.raw_href()):
                return True

    @property
    def badge(self):
        if self._badge is None:
            return ''
        return self._badge

    @property
    def has_badge(self):
        if self._badge is not None:
            return True

    def render(self):
        return render_to_string(self.template, dict(**{'menu_item': self}, **self.kwargs))

    def raw_href(self):
        if not self.url:
            return ''
        elif self.link_type in [self.URL_NAME, self.AJAX_GET_URL_NAME]:
            return reverse(self.url)
        elif self.link_type == self.AJAX_BUTTON:
            button = button_javascript(self.url).replace('"', "'")
            return f"javascript:{button}"
        elif self.link_type == self.JAVASCRIPT:
            return f"javascript:{self.url}"
        else:
            return f"{self.url}"

    def href(self):
        if self.disabled:
            return 'javascript:void(0)'
        href = self.raw_href()
        if self.link_type == self.AJAX_GET_URL_NAME:
            href = f"javascript: ajax_helpers.get_content('{href}')"
        if self.target:
            href += f'" target="{self.target}'
        return mark_safe(href)


class HtmlMenu:

    def __init__(self, request=None, template_name='django_menus/tab_menu.html', menu_id=None):
        self.menu_items = []
        self.template = template_name
        self.request = request
        self.active = None
        if menu_id:
            self.id = menu_id
        else:
            self.id = random_string()

    def visible_items(self):
        return [i for i in self.menu_items if i.visible]

    def add_item(self, text, url_name=None, link_type=MenuItem.URL_NAME, **kwargs):
        self.menu_items.append(MenuItem(text, url=url_name, menu=self, link_type=link_type, **kwargs))

    def add_items(self, *args):
        if isinstance(args[0], (tuple, list, MenuItem)):
            for a in args:
                if isinstance(a, BaseMenuItem):
                    a.menu = self
                    self.menu_items.append(a)
                else:
                    if type(a[-1]) == dict:
                        self.add_item(*a[:-1], **a[-1])
                    else:
                        self.add_item(*a)
        else:
            self.add_item(*args)
        return self

    def badge_ajax(self):
        return [{'function': 'html', 'selector': '#' + i.badge.id, 'html': i.badge.badge_html()}
                for i in self.menu_items if i.has_badge]

    def render(self):
        extra_menus = ''
        for i in self.menu_items:
            if hasattr(i, 'dropdown'):
                extra_menus += i.dropdown.render()
        return mark_safe(render_to_string(self.template, context={'menu': self}) + extra_menus)


class MenuMixin:
    tab_template = None

    def add_menu(self, menu_name, **kwargs):
        self.menus[menu_name] = HtmlMenu(self.request, **kwargs)
        return self.menus[menu_name]

    def add_main_menu(self, menu_name='main_menu', **kwargs):
        return self.add_menu(menu_name, template_name='django_menus/main_menu.html', **kwargs)

    def add_button_menu(self, menu_name='button_group', **kwargs):
        return self.add_menu(menu_name, template_name='django_menus/button_group.html', **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.menus = {}


class TemplateMenuView(MenuMixin, TemplateView):

    def setup_menu(self):
        return

    def get_context_data(self, **kwargs):
        self.setup_menu()
        context = super().get_context_data(**kwargs)
        context['menus'] = self.menus
        return context


class AjaxTabs(AjaxHelpers):

    TEMPLATE_CONTENT = 0
    MENU_CONTENT = 1
    AjaxCommand = namedtuple('AjaxCommand', ['name', 'type'])

    _ajax_commands = [
        AjaxCommand('tab_template', TEMPLATE_CONTENT),
        AjaxCommand('tab_menu', MENU_CONTENT),
    ]

    additional_content = []

    def create_ajax_commands(self, context):
        for c in self.ajax_commands:
            if c.type == self.TEMPLATE_CONTENT:
                html = context[c.name]
            else:
                html = self.menus[c.name].render()
            self.add_command('html', selector='#' + c.name, html=html)

    def get(self, request, *args, **kwargs):
        self.ajax_commands = self._ajax_commands + [self.AjaxCommand(*a) for a in self.additional_content]
        if request.is_ajax():
            context = self.get_context_data(**kwargs)
            self.create_ajax_commands(context)
            response = self.command_response()
            response['Cache-Control'] = 'No-Cache,No-Store'
            return response
        return super().get(request, *args, **kwargs)

    def main_context(self, **kwargs):
        return {}

    def tab_context(self, **kwargs):
        return {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.request.is_ajax():
            context.update(self.main_context())
        context.update(self.tab_context())
        for c in self.ajax_commands:
            if c.type == self.TEMPLATE_CONTENT:
                context[c.name] = mark_safe(render_to_string(getattr(self, c.name), context=context))
        return context

    def timer_menu(self, **_kwargs):
        self.setup_menu()
        for m in self.menus.values():
            self.response_commands += m.badge_ajax()
        return self.command_response()
