from urllib.parse import urlparse
from collections import namedtuple
from django.views.generic import TemplateView, View
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.urls import reverse, resolve, Resolver404
from ajax_helpers.mixins import AjaxHelpers
from ajax_helpers.templatetags.ajax_helpers import button_javascript
from ajax_helpers.utils import random_string
from django.conf import settings


class MenuItemBadge:

    def __init__(self, badge_id=None, format_function=None, text=None, css_class=None):
        self.id = badge_id
        self.text = text
        self.css_class = css_class
        self.format_function = format_function

    def badge_html(self):
        if self.format_function:
            self.format_function(self)
        if self.text:
            return mark_safe(f'&nbsp;<sup><span class="badge badge-pill badge-{self.css_class}">{self.text}</span></sup>')
        return ''

    def __str__(self):
        if self.id:
            return mark_safe(f'<span id="{self.id}">{self.badge_html()}</span>')
        else:
            return mark_safe(self.badge_html())


class BaseMenuItem:

    def __init__(self, disabled=False, visible=True, menu=None, **kwargs):
        self.disabled = disabled
        self.visible = visible
        self._menu = menu

    @property
    def menu(self):
        return self._menu

    @menu.setter
    def menu(self, menu):
        self._menu = menu


class DividerItem(BaseMenuItem):

    default_render = False

    @staticmethod
    def render():
        return mark_safe('<div class="dropdown-divider"></div>')


class MenuItemDisplay:
    def __init__(self, text=None, font_awesome=None, css_classes=None):
        self._css_classes = None

        if isinstance(text, self.__class__):
            self.text = text.text
            self.font_awesome = font_awesome if font_awesome else text.font_awesome
            self.css_classes = css_classes if css_classes else text.css_classes
        elif isinstance(text, (tuple, list)):
            params = {c: v for c, v in enumerate(text)}
            self.text = params.get(0)
            self.font_awesome = font_awesome if font_awesome else params.get(1)
            self.css_classes = css_classes if css_classes else params.get(2)
        else:
            self.text = text
            self.font_awesome = font_awesome
            self.css_classes = css_classes

    def display(self):
        if self.font_awesome:
            return mark_safe(f'<i class="{self.font_awesome}"></i> {self.text}')
        return mark_safe(self.text)

    @property
    def css_classes(self):
        return self._css_classes

    @css_classes.setter
    def css_classes(self, css):
        if css is None:
            self._css_classes = []
        elif type(css) == str:
            self._css_classes = [css]
        else:
            self._css_classes = css


class MenuItem(BaseMenuItem):

    HREF = 0
    AJAX_GET_URL_NAME = 1
    URL_NAME = 2
    AJAX_BUTTON = 3
    JAVASCRIPT = 4

    RESOLVABLE_LINK_TYPES = [AJAX_GET_URL_NAME,
                             URL_NAME,
                             HREF]

    @property
    def menu(self):
        return self._menu

    @menu.setter
    def menu(self, menu):
        self._menu = menu
        if menu.button_defaults and self.name in menu.button_defaults:
            self.menu_display = MenuItemDisplay(menu.button_defaults[self.name])
        if self.dropdown:
            self.dropdown.menu = menu

    def css(self):
        return ' '.join(self.menu_display.css_classes + (['disabled'] if self.disabled else []))

    def __init__(self, url=None, menu_display=None, link_type=URL_NAME, css_classes=None, template=None,
                 badge=None, target=None, dropdown=None, show_caret=True, font_awesome=None, no_hover=False,
                 placement='bottom-start', url_args=None, url_kwargs=None, attributes=None,
                 dropdown_kwargs=None, **kwargs):
        super().__init__(**kwargs)
        self._resolved_url = None
        self.link_type = link_type
        if self.link_type in [self.URL_NAME, self.AJAX_GET_URL_NAME]:
            split_url = url.split(',') if url else [None]
            if url_args is None and len(split_url) > 1:
                url_args = split_url[1:]
                url = split_url[0]
        self._href = self.raw_href(url, url_args, url_kwargs)
        self._attributes = attributes
        self.menu_config = {}
        if url is not None and link_type in self.RESOLVABLE_LINK_TYPES and self.resolved_url != 'invalid':
            view_class = getattr(self.resolved_url.func, 'view_class', None)
            if menu_display is None:
                if hasattr(view_class, 'menu_display'):
                    menu_display = view_class.menu_display
                else:
                    menu_display = self.resolved_url.url_name.capitalize()
            if hasattr(view_class, 'menu_config'):
                if callable(view_class.menu_config):
                    self.menu_config: dict = view_class.menu_config()
                else:
                    # noinspection PyTypeChecker
                    self.menu_config: dict = view_class.menu_config
        self.menu_display = MenuItemDisplay(menu_display, font_awesome, css_classes)
        self.kwargs = kwargs
        self.template = template
        self.target = target
        self._badge = badge
        self.show_caret = show_caret

        if dropdown:
            if dropdown_kwargs is None:
                dropdown_kwargs = {}
            self.dropdown = HtmlMenu(template='dropdown',
                                     no_hover=no_hover, placement=placement, **dropdown_kwargs).add_items(*dropdown)
        else:
            self.dropdown = None
            self.show_caret = False

        if self.template:
            self.default_render = False
        else:
            self.default_render = True

    def attributes(self):
        attributes = {}
        if 'attributes' in self.menu_config:
            if type(self.menu_config['attributes']) == dict:
                attributes.update(self.menu_config['attributes'])
            else:
                attributes.update(self.external_function(self.menu_config['attributes']))
        if self._attributes:
            attributes.update(self._attributes)
        if attributes:
            return mark_safe(' '.join([f'{k}="{v}"' for k, v in attributes.items()]))
        return ''

    @property
    def name(self):
        return self.menu_display.display()

    @property
    def resolved_url(self):
        if self._resolved_url is None:
            try:
                self._resolved_url = resolve(urlparse(self._href).path)
            except Resolver404:
                self._resolved_url = 'invalid'
        return self._resolved_url

    def params(self):
        return self.kwargs

    @property
    def active(self):
        if self.menu:
            if self.menu.active and self.resolved_url != 'invalid':
                try:
                    url_name = self.resolved_url.url_name
                    if self.resolved_url.namespace:
                        url_name = f'{self.resolved_url.namespace}:{url_name}'
                    if url_name == self.menu.active:
                        return True
                except Resolver404:
                    return
            elif self.menu.request is not None:
                if self.link_type in self.RESOLVABLE_LINK_TYPES and self.menu.request.path == self._href:
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
        if self.template is None:
            self.template = 'django_menus/single_button.html'
        return render_to_string(self.template, dict(**{'menu_item': self}, **self.kwargs))

    def raw_href(self, name_url, url_args, url_kwargs):
        if not name_url:
            return 'javascript:void(0)'
        elif self.link_type in [self.URL_NAME, self.AJAX_GET_URL_NAME]:
            return reverse(name_url, args=url_args if url_args else [], kwargs=url_kwargs if url_kwargs else {})
        elif self.link_type == self.AJAX_BUTTON:
            button = button_javascript(name_url).replace('"', "'")
            return f"javascript:{button}"
        elif self.link_type == self.JAVASCRIPT:
            return f"javascript:{name_url}"
        else:
            return f"{name_url}"

    def external_function(self, function_def):
        if callable(function_def):
            return function_def(self)
        elif isinstance(function_def, (list, tuple)):
            return function_def[0](self, *function_def[1:])

    def href(self):
        if self.disabled:
            return 'javascript:void(0)'
        href = self._href
        if 'href_format' in self.menu_config:
            if type(self.menu_config['href_format']) == str:
                href = self.menu_config['href_format'].format(href)
            else:
                href = self.external_function(self.menu_config['href_format'])
        elif self.link_type == self.AJAX_GET_URL_NAME:
            href = f"javascript: ajax_helpers.get_content('{href}')"
        if self.target:
            href += f'" target="{self.target}'
        return mark_safe(href)


class HtmlMenu:

    templates = {
        'base': 'django_menus/main_menu.html',
        'tabs': 'django_menus/tab_menu.html',
        'button_group': 'django_menus/button_group.html',
        'breadcrumb': 'django_menus/breadcrumb.html',
        'dropdown': 'django_menus/dropdown.html',
        'buttons': 'django_menus/button_menu.html',
    }

    def __init__(self, request=None, template='base', menu_id=None,
                 placement=None, no_hover=False, button_defaults=None, alignment=None):
        self.menu_items = []
        self.button_defaults = getattr(settings, 'DJANGO_MENUS_BUTTON_DEFAULTS', {})
        if button_defaults is not None:
            self.button_defaults.update(button_defaults)

        self.template = self.templates.get(template, template)
        self.request = request
        self.active = None
        self.no_hover = no_hover
        self.placement = placement
        self.alignment = alignment
        self.fixed_id = menu_id
        self.id = None

    def visible_items(self):
        return [i for i in self.menu_items if i.visible]

    def add_item(self, url_name=None, text=None,  link_type=MenuItem.URL_NAME, **kwargs):
        self.menu_items.append(MenuItem(url=url_name, menu_display=text, menu=self, link_type=link_type, **kwargs))

    def add_items(self, *args):
        for a in args:
            if isinstance(a, BaseMenuItem):
                a.menu = self
                self.menu_items.append(a)
            elif isinstance(a, View):
                self.add_item(a.request.path, getattr(a, 'menu_display', None), MenuItem.HREF)
            elif type(a) == tuple:
                if type(a[-1]) == dict:
                    self.add_item(*a[:-1], **a[-1])
                else:
                    self.add_item(*a)
            else:
                self.add_item(a)
        return self

    def badge_ajax(self):
        return [{'function': 'html', 'selector': '#' + i.badge.id, 'html': i.badge.badge_html()}
                for i in self.menu_items if i.has_badge]

    def render(self):
        if self.fixed_id:
            self.id = self.fixed_id
        else:
            self.id = random_string()
        extra_menus = ''
        for i in self.menu_items:
            if hasattr(i, 'dropdown') and i.dropdown:
                # noinspection PyUnresolvedReferences
                extra_menus += i.dropdown.render()
        return mark_safe(render_to_string(self.template, context={'menu': self}) + extra_menus)


class MenuMixin:

    def add_menu(self, menu_name, menu_type=None, **kwargs):
        request = getattr(self, 'request', None)
        if menu_type:
            self.menus[menu_name] = HtmlMenu(request, menu_type, **kwargs)
        else:
            self.menus[menu_name] = HtmlMenu(request, **kwargs)
        return self.menus[menu_name]

    def get_context_data(self, **kwargs):
        self.setup_menu()
        super_context = getattr(super(), 'get_context_data')
        if super_context and callable(super_context):
            context = super_context(**kwargs)
        else:
            context = {}
        context['menus'] = self.menus
        return context

    def setup_menu(self):
        return

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.menus = {}


class MenuTemplateView(MenuMixin, TemplateView):

    pass


class AjaxMenuTemplateView(AjaxHelpers, MenuTemplateView):

    def timer_menu(self, **_kwargs):
        self.setup_menu()
        for m in self.menus.values():
            self.response_commands += m.badge_ajax()
        return self.command_response()


class AjaxMenuTabs(AjaxMenuTemplateView):

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


class AjaxButtonMenuItem(MenuItem):

    def __init__(self, button_name, menu_display=None, url_name=None, url_args=None, ajax_kwargs=None, **kwargs):
        ajax_kwargs = ajax_kwargs if ajax_kwargs else {}
        super().__init__(button_javascript(button_name, url_name, url_args, **ajax_kwargs).replace('"', "'"),
                         menu_display,
                         link_type=MenuItem.JAVASCRIPT,
                         **kwargs)
