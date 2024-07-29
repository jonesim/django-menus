import json
from urllib.parse import urlparse

from ajax_helpers.templatetags.ajax_helpers import button_javascript
from django.template.loader import render_to_string
from django.urls import reverse, resolve, Resolver404
from django.utils.safestring import mark_safe


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

    def __init__(self, disabled=False, visible=True, menu=None, badge=None, **kwargs):
        self.disabled = disabled
        self.visible = visible
        self._badge = badge
        self._menu = menu

    @property
    def menu(self):
        return self._menu

    @menu.setter
    def menu(self, menu):
        self._menu = menu

    @property
    def badge(self):
        if self._badge is None:
            return ''
        return self._badge

    @property
    def has_badge(self):
        if self._badge is not None:
            return True

    def test_visible(self, request):
        return True


class HtmlMenuItem(BaseMenuItem):

    default_render = False

    def __init__(self, html=None, **kwargs):
        self.html = html
        super().__init__(**kwargs)

    def render(self):
        return mark_safe(self.html)


class DividerItem(BaseMenuItem):

    default_render = False

    @staticmethod
    def render():
        return mark_safe('<div class="dropdown-divider"></div>')


class MenuItemDisplay:
    def __init__(self, text=None, font_awesome=None, css_classes=None, tooltip=None, attributes=None):
        self._css_classes = None

        if isinstance(text, (tuple, list)):
            params = {c: v for c, v in enumerate(text)}
            self.text = params.get(0)
            self.font_awesome = font_awesome if font_awesome else params.get(1)
            self.css_classes = css_classes if css_classes else params.get(2)
            self.tooltip = tooltip if tooltip else params.get(3)
            self._attributes = attributes if attributes else params.get(4)
        else:
            self.text = text
            self.font_awesome = font_awesome
            self.css_classes = css_classes
            self.tooltip = tooltip
            self._attributes = attributes

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

    def attributes(self):
        return MenuItem.attr(self._attributes, self.tooltip)


class MenuItem(BaseMenuItem):

    HREF = 0
    AJAX_GET_URL_NAME = 1
    URL_NAME = 2
    AJAX_BUTTON = 3
    JAVASCRIPT = 4
    AJAX_COMMAND = 5

    RESOLVABLE_LINK_TYPES = [AJAX_GET_URL_NAME,
                             URL_NAME,
                             HREF]

    def test_visible(self, request):
        if self.visible:
            if self.link_type in self.RESOLVABLE_LINK_TYPES and self.resolved_url != 'invalid':
                view_class = getattr(self.resolved_url.func, 'view_class', None)
                if hasattr(view_class, 'view_permission'):
                    self.visible = view_class.view_permission(request, self)
            elif request and request.resolver_match:
                view_class = getattr(request.resolver_match.func, 'view_class', None)
                if hasattr(view_class, 'menu_permissions'):
                    self.visible = view_class.menu_permissions(request, self)
        return self.visible

    @property
    def menu(self):
        return self._menu

    @menu.setter
    def menu(self, menu):
        self._menu = menu
        if menu.button_defaults and self.name in menu.button_defaults:
            self.menu_display = menu.button_defaults[self.name]
            if not isinstance(self.menu_display, MenuItemDisplay):
                self.menu_display = MenuItemDisplay(self.menu_display)
        if self.dropdown:
            self.dropdown.menu = menu

    def css(self):
        return ' '.join(self.menu_display.css_classes + (['disabled'] if self.disabled else []))

    @staticmethod
    def attr(attributes, tooltip):
        attributes = {} if attributes is None else attributes
        if tooltip:
            attributes.update({'title': tooltip, 'data-tooltip': 'tooltip', 'data-placement': 'bottom'})
        return attributes

    def __init__(self, url=None, menu_display=None, link_type=URL_NAME, css_classes=None, template=None,
                 badge=None, target=None, dropdown=None, show_caret=True, font_awesome=None, no_hover=False,
                 placement='bottom-start', url_args=None, url_kwargs=None, attributes=None,
                 dropdown_template='dropdown', dropdown_kwargs=None, tooltip=None, key=None, permission_name=None,
                 **kwargs):
        super().__init__(**kwargs, badge=badge)
        self._resolved_url = None
        self.link_type = link_type
        self.key = key
        self.permission_name = permission_name if permission_name else url
        if self.link_type in [self.URL_NAME, self.AJAX_GET_URL_NAME]:
            split_url = url.split(',') if url else [None]
            if url_args is None and len(split_url) > 1:
                url_args = split_url[1:]
                url = split_url[0]
        self._href = self.raw_href(url, url_args, url_kwargs, **kwargs)
        self._attributes = self.attr(attributes, tooltip)
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
        if isinstance(menu_display, MenuItemDisplay):
            self.menu_display = menu_display
        else:
            self.menu_display = MenuItemDisplay(menu_display, font_awesome, css_classes)
        self.kwargs = kwargs
        self.template = template
        self.target = target

        self.show_caret = show_caret

        if dropdown:
            if dropdown_kwargs is None:
                dropdown_kwargs = {}
            from .menu import HtmlMenu
            self.dropdown = HtmlMenu(template=dropdown_template,
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
        attributes.update(self._attributes)
        attributes.update(self.menu_display.attributes())
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
                if self.link_type in self.RESOLVABLE_LINK_TYPES:
                    if self.menu.compare_full_path:
                        return self.menu.request.get_full_path() == self._href
                    else:
                        return self.menu.request.path == self._href

    def render(self):
        if self.template is None:
            self.template = 'django_menus/single_button.html'
        return render_to_string(self.template, dict(**{'menu_item': self}, **self.kwargs))

    @staticmethod
    def get_additional_url_kwargs(url_kwargs, **kwargs):
        for key, value in kwargs.items():
            if key.startswith('url_'):
                code = key[4:]
                if url_kwargs is None:
                    url_kwargs = {code: value}
                else:
                    url_kwargs[code] = value
        return url_kwargs

    def raw_href(self, name_url, url_args, url_kwargs, **kwargs):
        url_kwargs = self.get_additional_url_kwargs(url_kwargs, **kwargs)
        if not name_url:
            return 'javascript:void(0)'
        elif self.link_type in [self.URL_NAME, self.AJAX_GET_URL_NAME]:
            return reverse(name_url, args=url_args if url_args else [], kwargs=url_kwargs if url_kwargs else {})
        elif self.link_type == self.AJAX_BUTTON:
            button = button_javascript(name_url).replace('"', "'")
            return f"javascript:{button}"
        elif self.link_type == self.AJAX_COMMAND:
            command = [name_url] if isinstance(name_url, dict) else name_url
            command = json.dumps(command).replace('"', "'")
            return f"javascript:ajax_helpers.process_commands({command})"
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


class AjaxButtonMenuItem(MenuItem):

    def __init__(self, button_name, menu_display=None, url_name=None, url_args=None, ajax_kwargs=None, **kwargs):
        ajax_kwargs = ajax_kwargs if ajax_kwargs else {}
        super().__init__(button_javascript(button_name, url_name, url_args, **ajax_kwargs).replace('"', "'"),
                         menu_display,
                         link_type=MenuItem.JAVASCRIPT,
                         **kwargs)
