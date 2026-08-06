# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**django-tab-menus** is a Django library (PyPI: `django-tab-menus`) for rendering flexible navigation menus and AJAX-loaded tab interfaces. It integrates tightly with `django-ajax-helpers`.

## Commands

**Run the example project:**
```bash
cd django_examples
python manage.py migrate
python manage.py runserver
```

**Docker (example project on port 8009):**
```bash
docker-compose up
```

**Build the package:**
```bash
python setup.py sdist bdist_wheel
```

There is no formal test suite. Feature validation is done by running the example project at `django_examples/menu_examples/`.

## Architecture

### Core package: `django_menus/menu/`

**`menu.py`** — The main entry points:
- `HtmlMenu` — A menu container. Instantiate with a request and template type (`'base'`, `'tabs'`, `'button_group'`, `'breadcrumb'`, `'dropdown'`, `'buttons'`). Call `.add_item()` / `.add_items()` to populate, then `.render()` to output HTML.
- `MenuMixin` — A Django view mixin. Override `setup_menu()` and call `self.add_menu(name, template)` to attach menus to a view. Menus are injected into template context automatically. Also provides `add_ajax_dropdown_menu(*items, pos=...)` — the response handler for `AjaxMenuDropDownItem`.
- `MenuTemplateView` — `MenuMixin` + `TemplateView` convenience class.
- `AjaxMenuTemplateView` — `MenuTemplateView` + `django-ajax-helpers` integration; adds `timer_menu()` for badge polling.
- `AjaxMenuDropDownItem` — A `MenuItem` whose dropdown contents are fetched via AJAX on click; posts `{"ajax": "<dropdown_view_name>"}` (default `'dropdown_menu'`) to the current view, handled by `ajax_dropdown_menu(*args, pos, **kwargs)` returning `add_ajax_dropdown_menu(...)`.

**`menu_items.py`** — Item types added to `HtmlMenu`:
- `MenuItem` — The primary item class. Handles link resolution, permissions, dropdowns, badges, icons, keyboard shortcuts. The first positional arg is the link target (URL name, raw URL, JS, or command), the second is display (text string, tuple, or `MenuItemDisplay`), the third is `link_type`.
- `MenuItemDisplay` — Encapsulates display props: `(text, font_awesome_icon, css_classes, tooltip, attributes)`. Accepts tuple shorthand.
- `MenuItemBadge` — Renders a Bootstrap badge; supports a `format_function` for dynamic content.
- `BaseMenuItem` — Abstract base for custom items; subclass and implement `visible`, `disabled`, `badge`.
- `HtmlMenuItem` — Injects raw HTML into a menu.
- `DividerItem` — Renders a `dropdown-divider` separator (used inside dropdowns).
- `HeaderItem` — Renders a non-clickable `dropdown-header` section header (used inside dropdowns and context menus).
- `AjaxButtonMenuItem` — Wraps `MenuItem` for AJAX form-submit buttons.

**`tabs.py`** — `AjaxMenuTabs`: tab-based interfaces where each tab loads content via AJAX. Tabs are either template-based or menu-based. Use `tab_response()` to handle tab switching.

**`context_menu.py`** — `ContextMenuMixin`: right-click context menus. Elements matching `context_menu_selector` (default `'.context_menu'`) post `{"ajax": "context_menu"}` on right-click, handled by `ajax_context_menu(*args, **kwargs)` returning `self.add_context_menu(*items)`. A `data-ajax="other_name"` attribute on the element routes to `ajax_other_name` instead; the element's `id` and other data attributes arrive in the handler kwargs. Requires `django-ajax-helpers` on the view (e.g. `AjaxMenuTemplateView`).

### Link types on `MenuItem`

Defined as constants on `MenuItem`: `HREF`, `URL_NAME`, `AJAX_GET_URL_NAME`, `AJAX_BUTTON`, `JAVASCRIPT`, `AJAX_COMMAND`. The constructor auto-detects link type in many cases.

### Template tags: `django_menus/templatetags/django_menu_tags.py`

- `{% menu_content 'menu_name' %}` — render a menu by name from the `menus` context dict; the argument is a quoted string, not a bare variable
- `{% show_menu menu %}` — render a menu object directly, with placeholder support
- `{% display_button url='my_view' menu_display='Label' %}` — render a single `MenuItem` as a button; keyword args only, passed to `MenuItem(**kwargs)`
- `{% template_content 'content_name' %}` — render a template content fragment by context variable name (quoted string)

### Templates: `django_menus/templates/django_menus/`

One template per layout style: `main_menu.html`, `tab_menu.html`, `button_group.html`, `button_menu.html`, `breadcrumb.html`, `dropdown.html`, `single_button.html`. Override these in a project's templates directory to customise rendering.

### Static assets

CSS and JS live under `django_menus/static/`. Registered via `includes.py` using the `django-ajax-helpers` `SourceBase` mechanism — add `django_menus` to `INSTALLED_APPS` and run `collectstatic`.

### Example project: `django_examples/`

`django_examples/menu_examples/views.py` is the authoritative reference for all menu features. When adding new features, add a corresponding example view there.

## Settings

```python
INSTALLED_APPS = ['django_menus', ...]

# Optional: pre-configure named buttons globally
DJANGO_MENUS_BUTTON_DEFAULTS = {
    'save': MenuItemDisplay('Save', 'fas fa-save', 'btn-primary'),
}
```

## jQuery removal & Bootstrap 5 support (in progress, July 2026)

Part of a cross-package migration (summary in `X:\CLAUDE.md`). Status here: **barely started** — only the keyboard-shortcut path is converted.

### Done (uncommitted)
- `templates/django_menus/menu_key_press.html` converted to vanilla JS: `addEventListener('keydown')`, per-menu key dicts merged into a shared `window.django_menu_key_dict`, `django_modal` global now guarded.
- Supporting hygiene (relative imports, defensive dict copies, `find_packages()` in setup.py, readme rewrite) — not functional migration.

### Remaining — jQuery
- **`static/django_menus/django_menus.js` is fully jQuery + Popper v1** (`new Popper(...)`). Rewrite needed for: `dropdown_menu_function` / `dropdown_menu_click` (hover/click dropdowns), and the `enable_context_menu` / `context_menu` ajax_helpers commands (`$(document).on` delegation, `$.each(this.dataset)`, `$(window)` metrics, `.outerWidth/outerHeight`, namespaced `click.contextMenu` events). `click_href` and `get_ajax_dropdown_menu` are already vanilla.
- Must be converted **together with** `templates/django_menus/dropdown.html:14,16` — those call sites pass a jQuery object (`$('#{{ menu.id }}')`) into the JS functions; change them to pass an element or id.
- Popper v1 → Popper v2 (`Popper.createPopper`) or pure CSS positioning; coordinate with whatever ajax_helpers ends up bundling (it currently ships Popper 1.16.1).

### Remaining — Bootstrap 5
Dropdowns and tabs never used Bootstrap's JS plugins (custom JS + ajax_helpers commands throughout), so there is no `data-bs-*` attribute work — it is class renames plus one structural item:
- `main_menu.html:2` `ml-auto`/`mr-auto` → `ms-auto`/`me-auto`; `button_menu.html:6` `mr-1` → `me-1`; `context_menu.html:6` `float-right` → `float-end`.
- `menu_items.py:22` — `MenuItemBadge` emits `badge badge-pill badge-{colour}`; BS5 needs `badge rounded-pill text-bg-{colour}`. This is the highest-impact change because the colour is caller-supplied, so it needs a Bootstrap-version switch — **no BS-version setting exists in this package yet**; adopt the same mechanism as django-modals (`MODALS_CSS_FRAMEWORK`).
- `ajax_tooltip.html:6` uses BS4 tooltip markup (`.tooltip`/`.arrow`/`.tooltip-inner`) — ajax_helpers' rewritten tooltip now uses namespaced `ah-tooltip`/`ah-arrow`/`ah-tooltip-inner`; update to match.
- `static/django_menus/django_menus.css` targets `.navbar-dark` (deprecated in BS 5.3) — cosmetic.

## Releasing

Full process in `X:\CLAUDE.md` → "Releasing a package". Summary: once-over the diff since the last release tag (`git fetch --tags origin` first), bump `version` in `pyproject.toml` (packaging was converted from setup.py — the version now lives only there), commit, run `X:\release.bat` — it tags `v<version>` and pushes, and `.github/workflows/publish.yml` publishes to PyPI via trusted publishing. First Actions release: confirm the GitHub `pypi` environment and the PyPI trusted publisher for `django-tab-menus` are configured.
