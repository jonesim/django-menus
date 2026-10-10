import json
import re
from urllib.parse import urlparse, urlencode

from ajax_helpers.templatetags.ajax_helpers import button_javascript
from django.template.loader import render_to_string
from django.urls import reverse, resolve, Resolver404
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import mark_safe

from django_menus.packs import pack_attribute, render_pack_template


REPEAT_CLICK_ATTRIBUTE = 'data-django-menus-repeat-ms'


def coerce_repeat_click_ms(value, source):
    """Milliseconds as an int, with an error that names the knob rather than int()'s.

    Fails loudly rather than reading a typo as "off": this is set once in code, and a page that
    silently stopped guarding a link would be far harder to notice than an exception.
    """
    if isinstance(value, bool):
        raise TypeError(f'{source} takes milliseconds, not a boolean - use 0 to turn it off')
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f'{source} takes milliseconds as a number, not {value!r}') from None


class MenuItemBadge:

    def __init__(self, badge_id=None, format_function=None, text=None, css_class=None):
        self.id = badge_id
        self.text = text
        self.css_class = css_class
        self.format_function = format_function
        # Set when the badge is read off its item, so the pack can be resolved for the
        # request the menu is rendering for. A badge built and rendered on its own falls
        # back to the configured default.
        self.request = None

    def badge_html(self):
        if self.format_function:
            self.format_function(self)
        if self.text:
            return mark_safe(render_pack_template('badge.html', {'badge': self}, self.request))
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
        # The badge renders through the pack, so it needs the menu's request to know which.
        self._badge.request = getattr(self._menu, 'request', None)
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

    def render(self):
        return mark_safe(render_pack_template('divider.html', {}, getattr(self.menu, 'request', None)))


class HeaderItem(BaseMenuItem):
    default_render = False

    def __init__(self, text=None, **kwargs):
        self.text = text
        super().__init__(**kwargs)

    def render(self):
        return mark_safe(render_pack_template(
            'header.html', {'text': self.text}, getattr(self.menu, 'request', None)))


#: A plain attribute name: a letter, `_` or `:` to start, then letters, digits, `-`, `_`, `:` or
#: `.`. No whitespace, quotes, `=`, `/` or angle brackets, so one key can never close its own
#: attribute and open a second one.
#:
#: Used with `fullmatch`, not `match`: `$` matches *before a trailing newline* as well as at the
#: end of the string, so `'data-id\n'` satisfies `...$` and the pattern would not mean what the
#: line above it says.
_ATTRIBUTE_NAME = re.compile(r'[A-Za-z_:][-A-Za-z0-9_:.]*')


def attribute_name_is_safe(name):
    """Whether `name` may be written as an attribute name.

    Attribute names are **checked, not escaped**: escaping is the wrong tool here. A name is not
    quoted in the output, so the characters that do the damage are the ones that end it -- a
    space, `=`, a quote -- and a key of `x onmouseover` renders a second attribute the browser
    runs, whatever is done to the value beside it.

    `on*` is refused as well, so a key cannot be a native event handler. The ajax dropdown
    templates do write an `onclick` of their own, but in their own markup rather than through this
    dict, so refusing the name here does not disturb it -- and a caller passing `onclick` would
    have put a second one on the same tag, which is its own reason to refuse. A menu item that
    needs to run something has the javascript and ajax link types for it.

    **What this does not promise.** That a name is inert in the page it lands on. `x-on:click`,
    `@click`, `v-on:`, `hx-on:` and `data-action` are all well-formed names that execute under
    some front-end framework, and this library cannot know which a consumer loads; refusing them
    would break the callers using them deliberately, and the list has no end. The guarantee is
    narrower and structural: **a name cannot become markup** -- it cannot close its own attribute,
    open a second one, or end the tag -- and it cannot be a native `on*`.

    If attribute *names* are reaching this from untrusted input, that is the thing to fix. No
    policy here can help: `data-*` alone is enough to drive most framework code.
    """
    name = str(name)
    return bool(_ATTRIBUTE_NAME.fullmatch(name)) and not name.lower().startswith('on')


class MenuItemDisplay:
    # On the class as well, so a subclass whose __init__ does not call this one still has it.
    safe = False

    def __init__(self, text=None, font_awesome=None, css_classes=None, tooltip=None, attributes=None, safe=False):
        self._css_classes = None
        self.safe = safe

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
        """The label, as ``{{ }}`` would print it: escaped unless it is marked safe.

        A label is **text unless it says otherwise**. ``mark_safe`` here marked every one safe
        whatever it held, so an item whose label came from a value -- a project name, a file name,
        a report's name -- put that value into the page as markup, and the item was safe only
        because the caller happened to escape it. A label that really is markup says so with
        ``safe=True``; a label already marked safe where it was made (``mark_safe``,
        ``format_html``, a rendered template) is left alone by ``conditional_escape`` too.

        The icon goes through ``format_html`` for the same reason: ``font_awesome`` is written
        into a ``class`` attribute, and it is not always a literal either.

        ``None`` still reads as ``'None'``, as it did -- that is what a menu with no display shows
        today, and changing it is a separate question from what a label may contain.
        """
        text = mark_safe(self.text) if self.safe else self.text
        if self.font_awesome:
            return format_html('<i class="{}"></i> {}', self.font_awesome, text)
        return conditional_escape(text)

    def default_key(self):
        """The key `button_defaults` is matched on for an item showing this display.

        Separate from `display()` because a key is not a rendering. `display()` escapes, and a
        default keyed `R&D` has to go on matching a label of `R&D`; this returns what `display()`
        returned *before* it escaped, so which items match which default is unchanged.

        **A subclass with its own `display()` keeps the key that renderer gave**, without having
        to hear about this method: the lookup used to go through `display()`, and a custom one is
        the subclass's own code, untouched by the escaping added here, so calling it returns what
        it always returned. Override this as well only to choose a *different* key.
        """
        if type(self).display is not MenuItemDisplay.display:
            return self.display()
        if self.font_awesome:
            return f'<i class="{self.font_awesome}"></i> {self.text}'
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

    def _apply_menu_repeat_click_ms(self):
        """Take the menu's repeat-click window wherever this item has not set its own.

        Called from __init__ as well as from the menu setter, because HtmlMenu.add_item passes
        menu= to the constructor and so never runs the setter - which is how the tuple and string
        shorthands used to miss out on a menu-level value entirely while MenuItem objects got it.
        """
        menu_ms = getattr(self._menu, 'django_menus_repeat_click_ms', None)
        if menu_ms is None:
            return
        if REPEAT_CLICK_ATTRIBUTE not in self._attributes:
            self._attributes[REPEAT_CLICK_ATTRIBUTE] = coerce_repeat_click_ms(
                menu_ms, 'HtmlMenu(django_menus_repeat_click_ms=...)'
            )
        # A dropdown is an HtmlMenu of its own, built before this runs and with no link back, so
        # it does not inherit on its own account. It has to, because the item a user actually
        # clicks is inside the dropdown - the toggle carrying it goes nowhere.
        if self.dropdown is not None and self.dropdown.django_menus_repeat_click_ms is None:
            self.dropdown.django_menus_repeat_click_ms = menu_ms
            for item in self.dropdown.menu_items:
                if hasattr(item, '_apply_menu_repeat_click_ms'):
                    item._apply_menu_repeat_click_ms()

    @menu.setter
    def menu(self, menu):
        self._menu = menu
        self._apply_menu_repeat_click_ms()
        if menu.button_defaults:
            key = self.default_key
            if key in menu.button_defaults:
                self.menu_display = menu.button_defaults[key]
                if not isinstance(self.menu_display, MenuItemDisplay):
                    self.menu_display = MenuItemDisplay(self.menu_display)
        if self.dropdown:
            self.dropdown.menu = menu

    def css(self):
        return ' '.join(self.menu_display.css_classes + (['disabled'] if self.disabled else []))

    @staticmethod
    def attr(attributes, tooltip):
        # Copied, not adopted. This is stored as the item's own _attributes and then written to -
        # a tooltip adds three keys, a repeat-click window adds one - so keeping the caller's
        # dict meant an `attributes=` dict shared between items, or held at module level, picked
        # those up and passed them to every other item using it, for the life of the process.
        # Only the version-neutral half of the tooltip is added here: this runs in __init__,
        # before the item is attached to a menu, so there is no request yet and no way to know
        # the pack. The placement attribute, whose name Bootstrap 5 changed, is added in
        # attributes() below, which does run at render time.
        attributes = {} if attributes is None else dict(attributes)
        if tooltip:
            attributes.update({'title': tooltip, 'data-tooltip': 'tooltip'})
        return attributes

    def __init__(self, url=None, menu_display=None, link_type=URL_NAME, css_classes=None, template=None,
                 badge=None, target=None, dropdown=None, show_caret=True, font_awesome=None, no_hover=False,
                 placement='bottom-start', url_args=None, url_kwargs=None, attributes=None,
                 dropdown_template='dropdown', dropdown_kwargs=None, tooltip=None, key=None, permission_name=None,
                 query_string_params=None, django_menus_repeat_click_ms=None, safe=False, **kwargs):
        super().__init__(**kwargs, badge=badge)
        self.query_string_params = query_string_params
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
        # Milliseconds to hold THIS item for after it is clicked, overriding whatever the menu or
        # the page has set - including turning the guard on for one item when it is off for the
        # page, which is the point: the item that minds being clicked twice is usually the one
        # that knows it. 0 opts an item out again where the page has it on.
        if django_menus_repeat_click_ms is not None:
            self._attributes[REPEAT_CLICK_ATTRIBUTE] = coerce_repeat_click_ms(
                django_menus_repeat_click_ms, 'MenuItem(django_menus_repeat_click_ms=...)'
            )
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
            self.menu_display = MenuItemDisplay(menu_display, font_awesome, css_classes, safe=safe)
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

        # Last, because it needs self.dropdown. Covers the add_item path, where menu= arrives as
        # a constructor argument and the property setter never runs.
        self._apply_menu_repeat_click_ms()

    def attributes(self):
        attributes = {}
        if 'attributes' in self.menu_config:
            if type(self.menu_config['attributes']) == dict:
                attributes.update(self.menu_config['attributes'])
            else:
                attributes.update(self.external_function(self.menu_config['attributes']))
        attributes.update(self._attributes)
        attributes.update(self.menu_display.attributes())
        if 'data-tooltip' in attributes:
            request = getattr(self.menu, 'request', None)
            attributes[pack_attribute('placement', request)] = 'bottom'
        self.add_accessible_name(attributes)
        if attributes:
            # A value is written inside double quotes, so it is escaped unless it is marked safe
            # -- the same rule as the label. A tooltip is the usual one to hold text somebody
            # typed, and a quote in it closed the attribute and started another.
            #
            # A name is checked instead, and dropped when it is not a plain attribute name: it is
            # not quoted, so escaping would not stop it, and `attributes=` and the
            # `menu_config['attributes']` callable both let a caller supply the key.
            # `str(k)` once, and that same string is both checked and written. Interpolating
            # `k` here instead would render `format(k)`, which a class is free to make differ
            # from its `__str__` -- validating one representation and emitting another is the
            # shape of the bug however unlikely the object.
            names = ((str(k), v) for k, v in attributes.items())
            return mark_safe(' '.join([
                f'{name}="{conditional_escape(v)}"'
                for name, v in names
                if attribute_name_is_safe(name)
            ]))
        return ''

    def add_accessible_name(self, attributes):
        """Give an icon-only item a name a screen reader can read.

        An item rendered as an icon with no words has no text of its own, so its accessible name
        is whatever the icon font puts in ``::before`` -- for Font Awesome that is a private use
        codepoint, and a screen reader announces nothing useful. The words do exist: an icon-only
        button is normally given its tooltip instead, which reaches sighted readers on hover and
        assistive technology not at all, because ``title`` is only used for the accessible name
        when the element has no content and the icon counts as content.

        So where an item has a tooltip and no words, the tooltip becomes ``aria-label`` as well.

        Only then, and this is the important half:

        * an item that shows words is left alone. ``aria-label`` overrides the visible label, so
          setting one on a labelled item makes the announced name differ from the name on screen
          whenever the tooltip says something else -- which is what a tooltip is usually for.
        * an ``aria-label`` the caller passed in ``attributes`` is never overwritten.

        The icon itself is deliberately *not* marked ``aria-hidden``. It would be the tidier
        markup, but it changes the accessible name of every labelled item too (dropping the glyph
        that currently prefixes it), and that is a breaking change for anything selecting on the
        name rather than a fix for anyone reading the page.
        """
        if attributes.get('aria-label') or self.menu_display.text:
            return
        label = attributes.get('title') or self.menu_display.tooltip
        if label:
            attributes['aria-label'] = label

    @property
    def name(self):
        return self.menu_display.display()

    @property
    def default_key(self):
        """The key `button_defaults` is matched on, which the display decides.

        Not `name`. `name` is the label *rendered* -- escaped, and with the icon's `<i>` in front
        of the words when the item carries one -- and a key is not a rendering. Keyed on `name`,
        a default keyed `R&D` stopped matching an item labelled `R&D` the moment `display()`
        began escaping, silently and only for the keys that hold a character worth escaping.

        It is `MenuItemDisplay.default_key` that answers, so a subclass with its own renderer can
        say what its key is rather than have one reconstructed from fields it may not use.
        """
        return self.menu_display.default_key()

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
            self.template = 'single_button.html'
        context = dict(**{'menu_item': self}, **self.kwargs)
        # Same rule as HtmlMenu.templates: a bare filename is resolved against the pack, a
        # path is one the caller supplied and is used exactly as given.
        if '/' not in self.template:
            return render_pack_template(self.template, context, getattr(self.menu, 'request', None))
        return render_to_string(self.template, context)

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
            url = reverse(name_url, args=url_args if url_args else [], kwargs=url_kwargs if url_kwargs else {})
            if self.query_string_params is not None:
                if isinstance(self.query_string_params, dict):
                    url += '?' + urlencode(self.query_string_params)
                else:
                    url += self.query_string_params
            return url
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

    def href(self, with_target=True):
        """The item's href, for rendering inside `href="..."`.

        `with_target=False` for anywhere the result is used as a URL rather than dropped into
        that attribute: a target is added by closing the attribute early and opening a second
        one, so the return value is markup rather than a URL whenever an item has one. That is
        fine in a template and wrong everywhere else - the keyboard-shortcut handler assigned it
        to `a.href` and navigated to `/report.pdf" target="_blank`.
        """
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
        if with_target and self.target:
            href += f'" target="{self.target}'
        return mark_safe(href)


class AjaxButtonMenuItem(MenuItem):

    def __init__(self, button_name, menu_display=None, url_name=None, url_args=None, ajax_kwargs=None, **kwargs):
        ajax_kwargs = ajax_kwargs if ajax_kwargs else {}
        super().__init__(button_javascript(button_name, url_name, url_args, **ajax_kwargs).replace('"', "'"),
                         menu_display,
                         link_type=MenuItem.JAVASCRIPT,
                         **kwargs)
