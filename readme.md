[![PyPI version](https://badge.fury.io/py/django-tab-menus.svg)](https://badge.fury.io/py/django-tab-menus)

# django-tab-menus

A Django app for rendering flexible navigation menus and AJAX-loaded tab interfaces. Supports dropdowns, badges, keyboard shortcuts, permission-based visibility, and integration with [django-ajax-helpers](https://github.com/jonesim/django-ajax-helpers).

## Installation

```bash
pip install django-tab-menus
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'django_menus',
]
```

## Quick Start

The simplest menu is built with `HtmlMenu` and rendered in a template:

```python
from django_menus.menu import HtmlMenu, MenuItem, MenuMixin
from django.views.generic import TemplateView

class MyView(MenuMixin, TemplateView):
    template_name = 'my_template.html'

    def setup_menu(self):
        self.add_menu('main', 'base').add_items(
            'home',          # Django URL name — label auto-derived from view
            ('about', 'About Us'),
            ('contact', 'Contact'),
        )
```

In the template:

```html
{% load django_menu_tags %}
{% menu_content 'main' %}
```

`MenuMixin` injects all menus into the template context under `menus`, so `menus.main` is also accessible directly.

Two ready-made view classes save the boilerplate: `MenuTemplateView` is `MenuMixin + TemplateView`, and `AjaxMenuTemplateView` additionally mixes in django-ajax-helpers AJAX handling (needed for badge refresh, tabs and context menus).

## Menu Types

Pass a template name as the second argument to `add_menu()` (or as `template=` on `HtmlMenu`):

| Name | Layout |
|---|---|
| `'base'` | Bootstrap navbar |
| `'button_group'` | Inline button group |
| `'buttons'` | Stacked buttons |
| `'tabs'` | Tab bar |
| `'breadcrumb'` | Breadcrumb trail |
| `'dropdown'` | Standalone dropdown |

## Adding Items

### String shorthand

Passing a URL name string resolves the view and auto-derives the label from `view.menu_display` or the URL name:

```python
menu.add_items('dashboard', 'reports', 'settings')
```

### Tuple shorthand

```python
menu.add_items(
    ('reports', 'My Reports'),                          # (url_name, label)
    ('reports', 'My Reports', {'css_classes': 'btn-primary'}),  # with kwargs
)
```

### `MenuItem` class

The full item API:

```python
MenuItem(
    url,                        # URL name, raw URL, JS string, or AJAX command
    menu_display=None,          # str, tuple, or MenuItemDisplay instance
    link_type=MenuItem.URL_NAME,
    css_classes=None,           # str or list
    font_awesome=None,          # e.g. 'fas fa-edit'
    tooltip=None,
    badge=None,                 # MenuItemBadge instance
    dropdown=None,              # tuple of items for a nested dropdown
    show_caret=True,
    key=None,                   # keyboard shortcut, e.g. 'alt-s' or ['alt-s', 'shift-S']
    url_args=None,
    url_kwargs=None,
    attributes=None,            # dict of extra HTML attributes
    visible=True,
    disabled=False,
    target=None,                # link target, e.g. '_blank'
)
```

### Raw HTML

`HtmlMenuItem` injects arbitrary HTML into a menu slot:

```python
from django_menus.menu import HtmlMenuItem

menu.add_items(HtmlMenuItem(html='<span class="navbar-text">v2.1</span>'))
```

## Link Types

| Constant | Behaviour |
|---|---|
| `MenuItem.URL_NAME` | Django URL name resolved via `reverse()` (default) |
| `MenuItem.HREF` | Raw URL string |
| `MenuItem.AJAX_GET_URL_NAME` | URL name loaded via AJAX GET |
| `MenuItem.AJAX_BUTTON` | Submits an AJAX button (django-ajax-helpers) |
| `MenuItem.JAVASCRIPT` | Executes a JavaScript expression |
| `MenuItem.AJAX_COMMAND` | Sends an ajax_helpers command dict |

```python
# Raw URL
MenuItem('/some/path/', 'External', MenuItem.HREF)

# JavaScript
MenuItem("alert('hello')", 'Alert', MenuItem.JAVASCRIPT)

# AJAX GET (loads content without full page reload)
MenuItem('my_view', 'Load Content', MenuItem.AJAX_GET_URL_NAME)

# URL with args
MenuItem('profile', 'Profile', url_args=[user.pk])
MenuItem('profile', 'Profile', url_kwargs={'pk': user.pk})
# Shorthand: keyword args prefixed with url_ become URL kwargs
MenuItem('profile', 'Profile', url_pk=user.pk)
```

`AjaxButtonMenuItem` is a convenience class for posting an ajax-helpers button without writing the JavaScript yourself:

```python
from django_menus.menu import AjaxButtonMenuItem

menu.add_items(AjaxButtonMenuItem('refresh', 'Refresh'))   # posts {"button": "refresh"}
```

## MenuItemDisplay

Controls display properties — text, icon, CSS classes, tooltip, and HTML attributes:

```python
from django_menus.menu import MenuItemDisplay

# Keyword form
MenuItemDisplay(text='Save', font_awesome='fas fa-save', css_classes='btn-primary', tooltip='Save record')

# Tuple shorthand (text, icon, css_classes, tooltip, attributes)
MenuItem('save_view', ('Save', 'fas fa-save', 'btn-primary'))

# On a view class — auto-picked up when the URL is resolved
class MyView(TemplateView):
    menu_display = MenuItemDisplay('My View', 'fas fa-star', 'btn-success')
```

## Dropdowns

Pass a `dropdown` tuple to any `MenuItem`:

```python
from django_menus.menu import DividerItem, HeaderItem

menu.add_items(
    MenuItem(menu_display='Actions', dropdown=(
        HeaderItem('Record'),
        'edit_view',
        'delete_view',
        DividerItem(),
        'archive_view',
    )),
)
```

`HeaderItem` renders a non-clickable section header (`dropdown-header`); `DividerItem` a separator line. Options: `show_caret=False` hides the caret; `no_hover=True` requires a click to open.

### AJAX-loaded dropdowns

`AjaxMenuDropDownItem` renders a button whose dropdown contents are fetched from the server when clicked — useful when the items are expensive to build or depend on live data. The click posts `{"ajax": "<dropdown_view_name>"}` (default `'dropdown_menu'`) to the current view, which responds with `add_ajax_dropdown_menu`:

```python
from django_menus.menu import AjaxMenuDropDownItem

class MyView(AjaxMenuTemplateView):
    def setup_menu(self):
        self.add_menu('menu_items', 'button_group').add_items(
            AjaxMenuDropDownItem(menu_display='Options', css_classes='btn-success'))

    def ajax_dropdown_menu(self, *args, pos, **kwargs):
        return self.add_ajax_dropdown_menu('view1', 'view2', ('view4', 'View 4'), pos=pos)
```

An optional `value=` on the item is passed through to the handler, so one handler can serve several buttons.

## Context Menus

`ContextMenuMixin` attaches a right-click menu to any element matching `context_menu_selector` (default `'.context_menu'`). The right-click posts `{"ajax": "context_menu"}` to the view, which builds the menu on demand:

```python
from django_menus.menu import ContextMenuMixin, AjaxMenuTemplateView, HeaderItem, MenuItem

class MyView(ContextMenuMixin, AjaxMenuTemplateView):
    template_name = 'my_template.html'

    def ajax_context_menu(self, *args, **kwargs):
        return self.add_context_menu(
            HeaderItem('Actions'),
            'view1', 'view2',
            ('test_button', 'Send to View', MenuItem.AJAX_BUTTON),
        )
```

```html
<div class="context_menu" id="area_one">Right click me</div>

<!-- Per-element handler override: posts {"ajax": "special_context_menu"} instead -->
<div class="context_menu" id="area_two" data-ajax="special_context_menu">Right click me</div>
```

The clicked element's `id` is available in the handler kwargs, so the menu can vary per row/area. The view must include django-ajax-helpers handling (e.g. `AjaxMenuTemplateView`).

## Badges

Attach a `MenuItemBadge` to any `MenuItem`:

```python
from django_menus.menu import MenuItemBadge

def my_badge_fn(badge):
    badge.text = MyModel.objects.filter(unread=True).count()
    badge.css_class = 'danger'   # Bootstrap colour name

MenuItem('inbox', 'Inbox', badge=MenuItemBadge('inbox-badge', my_badge_fn))
```

The badge is rendered inside a `<span id="inbox-badge">` so it can be refreshed via AJAX without a page reload. Use `AjaxMenuTemplateView.timer_menu()` to poll for updates.

## Keyboard Shortcuts

```python
# Single key
MenuItem('save_view', 'Save', key='alt-s')

# Multiple bindings
MenuItem('save_view', 'Save', key=['alt-s', 'shift-S'])
```

Supported modifiers: `alt-`, `shift-`. The key name is case-sensitive (e.g. `'F2'` for the function key).

Shortcuts from every menu on the page — including menus loaded later via AJAX — are merged into a single document-level listener, so multiple menus can define keys without clobbering each other. Shortcuts are suppressed while a django-modals dialog is open.

## Permissions

### `view_permission`

Define a classmethod on a view to control whether the menu item pointing to that view is visible:

```python
class SecretView(TemplateView):
    @classmethod
    def view_permission(cls, request, menu_item):
        return request.user.is_staff
```

### `menu_permissions`

Define on a view to control non-URL-resolved items (e.g. AJAX buttons) while that view is active:

```python
class MyView(TemplateView):
    @classmethod
    def menu_permissions(cls, request, menu_item):
        return request.user.has_perm('myapp.can_edit')
```

### Callable `visible`

`visible` accepts a callable taking the request, for items whose target view you do not own:

```python
MenuItem('admin:index', 'Admin', visible=lambda request: request.user.is_staff)
```

## Menu Registry

A long dropdown listed in one central `setup_menu()` conflicts on every merge. The registry lets
each view declare its own place instead, so adding a page touches only the app that owns it.

Declare the sections once:

```python
DJANGO_MENUS_SECTIONS = {
    'settings': {'title': 'Settings'},
    'reports': {
        'title': 'Reports',
        'groups': ['sales', 'purchases', ('stock', 'Stock')],
        'sort': 'order',
    },
}
```

Then each view says where it belongs:

```python
from django_menus.menu import MenuEntry

class ExchangeRateList(ListView):
    menu_display = 'Exchange Rates'
    menu_entry = MenuEntry('settings')

class StockReorderReport(ListView):
    menu_display = 'Stock Reorder'
    menu_entry = MenuEntry('reports', 'stock')
```

and the central menu shrinks to a skeleton:

```python
def setup_menu(self):
    self.add_menu('main_menu').add_items(
        'dashboard_view',
        registry.menu_item('reports', self.request),
        registry.menu_item('settings', self.request,
                           MenuItem('page_info', 'Page Info', link_type=MenuItem.AJAX_BUTTON),
                           MenuItem('admin:index', 'Admin', visible=lambda r: r.user.is_staff)),
    )
```

The URLConf is walked once, lazily and cached; `MenuItem`s are built per request, so
`view_permission` and callable `visible` behave exactly as they do in a hand-written menu.

### `MenuEntry`

| Argument | Purpose |
|---|---|
| `section` | Key in `DJANGO_MENUS_SECTIONS`. Required. |
| `group` | Group within a grouped section. Required for grouped sections. |
| `url_name` | Only needed when the view is reachable under more than one url name. |
| `url_args` / `url_kwargs` | Arguments for `reverse()`, when the url pattern takes any. |
| `display` | Overrides `menu_display` **in this section only** — tabs and breadcrumbs keep the view's own label. |
| `order` | Sort position, used when the section sets `sort: 'order'`. |
| anything else | Passed to `MenuItem()` — `font_awesome`, `css_classes`, `key`, `tooltip`… |

Set `menu_entry` to a list to put one view in several sections. `menu_entry` is inherited, so a
subclass that should not appear must set `menu_entry = None`.

### Section options

| Key | Default | Meaning |
|---|---|---|
| `title` | capitalised section name | Label of the parent item built by `menu_item()`. |
| `font_awesome` | — | Icon for the parent item. |
| `groups` | none | Group names in render order. A `(name, header)` pair emits a `HeaderItem`. |
| `sort` | `'alpha'` | `'alpha'` by display text, `'order'` by `MenuEntry(order=...)`, or `'declared'` by URLConf order. |
| `divider` | on when grouped | Insert a `DividerItem` between groups. |
| `default_group` | first group | Group for entries that name none. |

Dividers and headers are only emitted between groups that still have visible items for this
request, so a group hidden by permissions never leaves a stray separator behind.

### API

```python
from django_menus.menu import registry

registry.dropdown(section, request, *extra)   # ordered list of items
registry.menu_item(section, request, *extra)  # parent MenuItem with the dropdown attached
registry.extra(item, group=..., order=..., sort_text=...)   # place a caller-built item
registry.specs(section)                       # what the scan found, for diagnostics
```

`extra` items are ordinary `MenuItem`s built at the call site — use them for anything the URLConf
cannot describe, such as an `AJAX_BUTTON` or a third-party view with no view class. They sort by
their own display text alongside the registered items.

### Checking it

Mistyped sections and groups, ambiguous url names and missing url arguments are reported by
`manage.py check` (ids `django_menus.E001`–`E007`, `W001`–`W002`) and raise `ImproperlyConfigured`
when the registry scans.

`manage.py show_menu` prints the resolved tree so ordering is inspectable without running the site:

```bash
manage.py show_menu                          # every configured section
manage.py show_menu reports --user ian       # one section, as a given user
manage.py show_menu --view dashboard_view    # the menus a view actually builds
manage.py show_menu --view dashboard_view --show-hidden --format json
```

## AJAX Tab Interfaces

`AjaxMenuTabs` handles a tab bar where each tab loads its content via AJAX:

```python
from django_menus.menu import AjaxMenuTabs, MenuItem

class MyTabView(AjaxMenuTabs):
    template_name = 'my_tabs.html'
    tab_template = 'my_tab_content.html'

    def setup_menu(self):
        super().setup_menu()
        self.add_menu('tab_menu', 'tabs').add_items(
            ('tab1_view', 'First Tab', MenuItem.AJAX_GET_URL_NAME),
            ('tab2_view', 'Second Tab', MenuItem.AJAX_GET_URL_NAME),
        )

    def tab_context(self, **kwargs):
        context = super().tab_context(**kwargs)
        context['data'] = MyModel.objects.all()
        return context

    def main_context(self, **kwargs):
        # Only called on the initial (non-AJAX) page load
        return {'title': 'My Tabs'}
```

- `tab_context()` is called on every request (initial and AJAX).
- `main_context()` is called only on the initial page load.
- `additional_content` lists extra areas to refresh on tab switch: `[(name, AjaxMenuTabs.MENU_CONTENT)]` for a menu, or `[(name, AjaxMenuTabs.TEMPLATE_CONTENT)]` for a template fragment.

## Global Button Defaults

Pre-configure named button styles in `settings.py` so any menu item whose display text matches the key inherits the style automatically:

```python
from django_menus.menu import MenuItemDisplay

DJANGO_MENUS_BUTTON_DEFAULTS = {
    'save':   MenuItemDisplay('Save',   'fas fa-save',   'btn-primary'),
    'delete': MenuItemDisplay('Delete', 'fas fa-trash',  'btn-danger'),
    'edit':   MenuItemDisplay('Edit',   'fas fa-pen',    'btn-secondary'),
}
```

Then in any view:

```python
self.add_menu('actions', 'button_group').add_items(
    MenuItem('save_view',   'save'),    # picks up the global style
    MenuItem('delete_view', 'delete'),
)
```

Individual menus can override or extend the global set with `button_defaults=`, without affecting other menus:

```python
self.add_menu('actions', 'button_group',
              button_defaults={'save': MenuItemDisplay('Save', 'fas fa-check', 'btn-outline-primary')})
```

## Template Tags

```html
{% load django_menu_tags %}

{# Render a menu by name from the context variable 'menus' #}
{% menu_content 'main_menu' %}

{# Render any menu object directly #}
{% show_menu menus.main_menu %}

{# Render a single button inline — keyword args are passed to MenuItem #}
{% display_button url='my_view' menu_display='Click me' %}

{# Render a template content fragment by context variable name #}
{% template_content 'tab_template' %}
```

## Running the Example Project

```bash
# With Docker
docker-compose up
# Visit http://localhost:8009

# Without Docker
cd django_examples
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
