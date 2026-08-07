"""Build dropdown contents from declarations on the view classes themselves.

A view opts in by setting ``menu_entry``::

    class ExchangeRateList(ListView):
        menu_display = 'Exchange Rates'
        menu_entry = MenuEntry('settings')

The registry walks the URLConf once, lazily and cached, collecting a spec for every view with a
``menu_entry``.  ``dropdown()`` materialises those specs into ``MenuItem``s per request and applies
the section's ordering policy.  Nothing is reversed or resolved until then - the scan never builds a
``MenuItem``.

Sections are declared in settings::

    DJANGO_MENUS_SECTIONS = {
        'settings': {'title': 'Settings'},
        'reports': {'title': 'Reports', 'groups': ['sales', 'purchases', 'stock']},
    }
"""
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import URLPattern, URLResolver, get_resolver, get_urlconf

from .menu_items import DividerItem, HeaderItem, MenuItem, MenuItemDisplay

ALPHA = 'alpha'
ORDER = 'order'
DECLARED = 'declared'

SORT_OPTIONS = (ALPHA, ORDER, DECLARED)

# Sorts after every real order/index without needing None comparisons.
LAST = 10 ** 9


class MenuEntry:
    """A view class's declaration of where it belongs in a menu.

    Pure data - it must never touch reverse() or resolve(), because it is built at import time.

    section       name of a key in DJANGO_MENUS_SECTIONS
    group         group within a grouped section
    url_name      required only when the view is reachable under more than one url name
    url_args      positional arguments for reverse()
    url_kwargs    keyword arguments for reverse()
    display       overrides view_class.menu_display for this section only
    order         sort position, used when the section sets sort='order'
    item_kwargs   anything else is passed straight to MenuItem()
    """

    def __init__(self, section, group=None, url_name=None, url_args=None, url_kwargs=None,
                 display=None, order=None, **item_kwargs):
        self.section = section
        self.group = group
        self.url_name = url_name
        self.url_args = url_args
        self.url_kwargs = url_kwargs
        self.display = display
        self.order = order
        self.item_kwargs = item_kwargs

    def __repr__(self):
        return f'MenuEntry({self.section!r}, group={self.group!r}, url_name={self.url_name!r})'


class MenuSpec:
    """One registered (view class, url name, entry) triple, ready to materialise."""

    def __init__(self, entry, url_name, view_class, declared_index):
        self.entry = entry
        self.url_name = url_name
        self.view_class = view_class
        self.declared_index = declared_index

    @property
    def section(self):
        return self.entry.section

    @property
    def group(self):
        return self.entry.group

    @property
    def view_path(self):
        return f'{self.view_class.__module__}.{self.view_class.__name__}'

    def menu_item(self):
        """Build the MenuItem.  Calls reverse() and resolve(), so only ever per request."""
        kwargs = dict(self.entry.item_kwargs)
        if self.entry.display is not None:
            kwargs['menu_display'] = self.entry.display
        if self.entry.url_args is not None:
            kwargs['url_args'] = list(self.entry.url_args)
        if self.entry.url_kwargs is not None:
            kwargs['url_kwargs'] = dict(self.entry.url_kwargs)
        item = MenuItem(self.url_name, **kwargs)
        return stamp(item, group=self.entry.group, order=self.entry.order,
                     index=self.declared_index)

    def __repr__(self):
        return f'MenuSpec({self.url_name!r}, {self.view_path})'


class RegistryError:
    """One problem found while scanning.  Rendered both as a system check and as an exception."""

    def __init__(self, code, message, obj=None, hint=None):
        self.code = code
        self.message = message
        self.obj = obj
        self.hint = hint

    @property
    def is_error(self):
        return self.code.startswith('E')

    def __str__(self):
        return f'({self.code}) {self.message}'


def stamp(item, group=None, order=None, index=None, sort_text=None):
    """Attach the ordering metadata dropdown() sorts on.  Returns the item."""
    if group is not None:
        item.registry_group = group
    if order is not None:
        item.registry_order = order
    if index is not None:
        item.registry_index = index
    if sort_text is not None:
        item.registry_sort_text = sort_text
    return item


def extra(item, group=None, order=None, sort_text=None):
    """Stamp a caller-built item so it sorts alongside the registered ones.

    Only needed when the item must land in a particular group, at a particular order, or sort on
    something other than its display text - a plain MenuItem passed to dropdown() already sorts by
    its own display text.
    """
    return stamp(item, group=group, order=order, sort_text=sort_text)


def display_text(menu_display):
    """The plain text of a menu_display, whatever form it was declared in."""
    if menu_display is None:
        return None
    if isinstance(menu_display, MenuItemDisplay):
        return menu_display.text
    if isinstance(menu_display, (tuple, list)):
        return menu_display[0] if menu_display else None
    return menu_display


# ----------------------------------------------------------------------------- section settings

def section_settings():
    return getattr(settings, 'DJANGO_MENUS_SECTIONS', {})


def sections():
    return list(section_settings())


def section_config(section):
    config = section_settings().get(section)
    if config is None:
        raise ImproperlyConfigured(
            f"django_menus: unknown menu section '{section}'. "
            f'Add it to DJANGO_MENUS_SECTIONS (configured: {", ".join(sections()) or "none"}).')
    return config


def section_groups(config):
    """(ordered group names, {group name: header text}) for a section config."""
    names = []
    headers = {}
    for group in config.get('groups') or ():
        if isinstance(group, (tuple, list)):
            names.append(group[0])
            if len(group) > 1 and group[1]:
                headers[group[0]] = group[1]
        else:
            names.append(group)
    return names, headers


# ------------------------------------------------------------------------------------ url scan

def walk_urls(patterns, namespaces=(), captured=0):
    """Yield (URLPattern, namespace tuple, arguments captured by enclosing includes)."""
    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            nested = namespaces + ((pattern.namespace,) if pattern.namespace else ())
            try:
                sub_patterns = pattern.url_patterns
            except ImproperlyConfigured:
                # A broken include is Django's problem to report - it must not take the menu down.
                continue
            for found in walk_urls(sub_patterns, nested, captured + pattern.pattern.regex.groups):
                yield found
        elif isinstance(pattern, URLPattern):
            yield pattern, namespaces, captured


def view_entries(view_class, errors):
    """The MenuEntry list declared by a view class.  Inherited entries count."""
    declared = getattr(view_class, 'menu_entry', None)
    if declared is None:
        return []
    entries = declared if isinstance(declared, (list, tuple)) else [declared]
    valid = []
    for entry in entries:
        if isinstance(entry, MenuEntry):
            valid.append(entry)
        else:
            errors.append(RegistryError(
                'E006', f'{view_class.__name__}.menu_entry must be a MenuEntry (or a list of '
                        f'them), not {type(entry).__name__}.', obj=view_class))
    return valid


def scan(urlconf):
    """Walk the URLConf and return ({section: [MenuSpec]}, [RegistryError])."""
    names_by_view = {}
    required_args = {}
    view_order = []

    for pattern, namespaces, captured in walk_urls(get_resolver(urlconf).url_patterns):
        if not pattern.name:
            continue
        full_name = ':'.join(namespaces + (pattern.name,))
        required_args.setdefault(full_name, captured + pattern.pattern.regex.groups)
        view_class = getattr(pattern.callback, 'view_class', None)
        if view_class is None:
            continue
        names = names_by_view.setdefault(view_class, [])
        if full_name not in names:
            names.append(full_name)
        if view_class not in view_order:
            view_order.append(view_class)

    found = {}
    errors = []
    index = 0
    for view_class in view_order:
        for entry in view_entries(view_class, errors):
            url_name = entry.url_name
            if url_name is None:
                names = names_by_view[view_class]
                if len(names) > 1:
                    errors.append(RegistryError(
                        'E003', f'{view_class.__name__} is reachable under several url names '
                                f'({", ".join(names)}), so its menu_entry must say which one to '
                                f'use.', obj=view_class,
                        hint=f"MenuEntry('{entry.section}', url_name='{names[0]}')"))
                    continue
                url_name = names[0]
            elif url_name not in required_args:
                errors.append(RegistryError(
                    'E004', f"{view_class.__name__}.menu_entry names url '{url_name}', which is "
                            f'not in the URLConf.', obj=view_class))
                continue
            spec = MenuSpec(entry, url_name, view_class, index)
            index += 1
            validate_spec(spec, required_args[url_name], errors)
            found.setdefault(entry.section, []).append(spec)
    return found, errors


def validate_spec(spec, required, errors):
    entry = spec.entry
    config = section_settings().get(entry.section)
    if config is None:
        errors.append(RegistryError(
            'E001', f"{spec.view_class.__name__}.menu_entry names section '{entry.section}', "
                    f'which is not in DJANGO_MENUS_SECTIONS.', obj=spec.view_class))
    else:
        group_names = section_groups(config)[0]
        if entry.group is not None and entry.group not in group_names:
            errors.append(RegistryError(
                'E002', f"{spec.view_class.__name__}.menu_entry names group '{entry.group}', "
                        f"which section '{entry.section}' does not define "
                        f'({", ".join(group_names) or "it has no groups"}).', obj=spec.view_class))
        elif entry.group is None and group_names:
            errors.append(RegistryError(
                'E002', f"section '{entry.section}' is grouped, but "
                        f'{spec.view_class.__name__}.menu_entry sets no group.',
                obj=spec.view_class, hint=f'Groups: {", ".join(group_names)}'))
        if config.get('sort', ALPHA) not in SORT_OPTIONS:
            errors.append(RegistryError(
                'E007', f"section '{entry.section}' has sort='{config['sort']}'; expected one of "
                        f'{", ".join(SORT_OPTIONS)}.'))

    supplied = len(entry.url_args or ()) + len(entry.url_kwargs or {})
    if supplied < required:
        errors.append(RegistryError(
            'E005', f"url '{spec.url_name}' takes {required} argument(s) but "
                    f'{spec.view_class.__name__}.menu_entry supplies {supplied} - reversing it '
                    f'will fail.', obj=spec.view_class,
            hint='Set url_args or url_kwargs on the MenuEntry.'))

    text = display_text(entry.display)
    if text is None:
        text = display_text(getattr(spec.view_class, 'menu_display', None))
        if text is None:
            errors.append(RegistryError(
                'W001', f'{spec.view_class.__name__} has no menu_display and its menu_entry sets '
                        f'no display, so the menu will show a capitalised url name.',
                obj=spec.view_class))
    if text is not None and text in getattr(settings, 'DJANGO_MENUS_BUTTON_DEFAULTS', {}):
        errors.append(RegistryError(
            'W002', f"'{text}' is also a DJANGO_MENUS_BUTTON_DEFAULTS key, so the item will be "
                    f'relabelled after the section has been sorted.', obj=spec.view_class))


# ---------------------------------------------------------------------------------------- cache

_cache = {}


def cache_key():
    return get_urlconf() or settings.ROOT_URLCONF


def clear_cache(**kwargs):
    """Signal receiver for setting_changed, and a manual reset for tests."""
    if kwargs.get('setting') in (None, 'ROOT_URLCONF', 'DJANGO_MENUS_SECTIONS',
                                 'DJANGO_MENUS_BUTTON_DEFAULTS'):
        _cache.clear()


def scanned():
    key = cache_key()
    if key not in _cache:
        found, errors = scan(key)
        fatal = [e for e in errors if e.is_error]
        if fatal:
            raise ImproperlyConfigured(
                'django_menus registry:\n  ' + '\n  '.join(str(e) for e in fatal))
        _cache[key] = found
    return _cache[key]


def validate(urlconf=None):
    """Every problem in the current URLConf.  Used by the system check; never raises."""
    return scan(urlconf or cache_key())[1]


def specs(section=None):
    found = scanned()
    if section is None:
        return {name: list(items) for name, items in found.items()}
    section_config(section)
    return list(found.get(section, ()))


# ------------------------------------------------------------------------------------- building

def sort_key(item, sort):
    text = getattr(item, 'registry_sort_text', None)
    if text is None:
        text = display_text(getattr(item, 'menu_display', None))
    text = (text or '').lower()
    index = getattr(item, 'registry_index', LAST)
    if sort == ORDER:
        order = getattr(item, 'registry_order', None)
        return LAST if order is None else order, text, index
    if sort == DECLARED:
        return index, text, 0
    return text, index, 0


def dropdown(section, request=None, *extra_items, group=None, filter_visible=True):
    """The ordered contents of a section, ready to pass to MenuItem(dropdown=...).

    `extra_items` are caller-built menu items - use them for anything the URLConf cannot describe,
    such as an AJAX_BUTTON or a third-party view with no view class.  They sort by their display
    text alongside the registered items.

    Returns [] when nothing is visible, which makes the parent item render nothing.
    """
    config = section_config(section)
    group_names, headers = section_groups(config)
    default_group = config.get('default_group') or (group_names[0] if group_names else None)
    sort = config.get('sort', ALPHA)
    use_dividers = config.get('divider', bool(group_names))

    buckets = {}
    for spec in specs(section):
        item = spec.menu_item()
        buckets.setdefault(getattr(item, 'registry_group', None) or default_group, []).append(item)
    for item in extra_items:
        item_group = getattr(item, 'registry_group', None) or group or default_group
        buckets.setdefault(item_group, []).append(item)

    unknown = [name for name in buckets if name not in (group_names or [default_group])]
    if unknown:
        raise ImproperlyConfigured(
            f"django_menus: section '{section}' has no group(s) {', '.join(map(str, unknown))}.")

    contents = []
    for name in (group_names or [default_group]):
        items = buckets.get(name) or []
        items.sort(key=lambda i: sort_key(i, sort))
        if filter_visible and request is not None:
            items = [i for i in items if i.test_visible(request)]
        if not items:
            continue
        if contents and use_dividers:
            contents.append(DividerItem())
        if name in headers:
            contents.append(HeaderItem(headers[name]))
        contents += items
    return contents


def menu_item(section, request=None, *extra_items, **menu_item_kwargs):
    """The parent MenuItem for a section, with its dropdown already built.

    Hidden when the section has nothing visible for this request.
    """
    config = section_config(section)
    menu_item_kwargs.setdefault('menu_display', config.get('title') or section.capitalize())
    if config.get('font_awesome'):
        menu_item_kwargs.setdefault('font_awesome', config['font_awesome'])
    contents = dropdown(section, request, *extra_items)
    item = MenuItem(dropdown=tuple(contents), **menu_item_kwargs)
    if not contents:
        item.visible = False
    return item
