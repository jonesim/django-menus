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
python manage.py runserver --settings=django_examples.settings_bs5   # Bootstrap 5; needs django-ajax-helpers >= 1.0.1
```

Running natively on Windows fails with `'View1' object has no attribute 'app'` under either settings module: `show_src_code`'s `DemoViewMixin.package_button` matches the app with `c.path.split('/')`, which never matches a backslash path. Docker (Linux) is unaffected.

**Docker (example project on port 8009):**
```bash
docker-compose up
```

Two services: `django_menus` (Bootstrap 4, port 8009, `requirements.txt` on Python 3.8) and `django_menus_bs5` (Bootstrap 5, port 8010, `requirements_bs5.txt` on Python 3.13 via Dockerfile build args, `settings_bs5` with its own `db_bs5.sqlite3`). ajax-helpers 1.0.x needs Python >= 3.9, hence the split. `requirements_bs5.txt` requires `django-ajax-helpers>=1.0.1`.

**Build the package:**
```bash
python -m build
```

**Run the tests:**
```bash
python -m django test tests --settings=tests.settings
```

The `tests/` package at the repo root has its own settings module and URLConf — `django_examples.settings` cannot host tests because `menu_examples.apps.ModalConfig` (via `show_src_code.apps.PypiAppConfig`) makes a live PyPI request when the app registry is populated. `tests/` is excluded from the wheel by the `packages.find` include filter.

Coverage is the menu registry plus a regression baseline pinning every `add_items` form and every menu template to its exact rendered HTML. Anything not covered there is still validated by running the example project at `django_examples/menu_examples/`.

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

**`registry.py`** — `MenuRegistry`-style module-level API that builds dropdown contents from `menu_entry` declarations on view classes, so each app owns its own menu entries instead of one central `setup_menu()`:
- `MenuEntry(section, group=None, url_name=None, url_args=None, url_kwargs=None, display=None, order=None, **item_kwargs)` — the declaration, set as `menu_entry` on a view class (or a list of them for several sections). Pure data; it must never call `reverse()`/`resolve()`, because it is built at import time.
- Entries are read from `view_class.__dict__`, never inherited. A listed page usually has archived/grouped/pk-taking subclasses reachable under their own url names, and inheriting would silently add a duplicate item for each; a subclass that should appear declares its own `MenuEntry`.
- `MenuSpec` — one scanned `(entry, full url name, view class)` triple. `menu_item()` materialises it; that is the only place `MenuItem` is constructed.
- `dropdown(section, request, *extra)` / `menu_item(section, request, *extra)` — build the section per request. `extra` items are caller-built `MenuItem`s (an `AJAX_BUTTON`, `admin:index`, anything the URLConf cannot describe) and sort by their display text alongside the registered ones.
- `extra(item, group=..., order=..., sort_text=...)` — stamp `registry_group` / `registry_order` / `registry_sort_text` on a caller-built item.
- Sections come from `DJANGO_MENUS_SECTIONS`; `sort` is `'alpha'` (default), `'order'` or `'declared'`. Dividers and headers are emitted only between groups that still have visible items after `test_visible`, so a permission-hidden group leaves no stray separator.
- The URLConf scan is cached on `get_urlconf() or settings.ROOT_URLCONF` — the same key Django's own `get_resolver` uses — and `clear_cache` is connected to `setting_changed` in `apps.ready()`.

**`checks.py`** — system checks (`django_menus.E001`–`E007`, `W001`–`W002`) sharing `registry.validate()` with the scan, which also raises `ImproperlyConfigured`. `E005` catches a url pattern needing more arguments than the entry supplies, statically, without reversing.

**`management/commands/show_menu.py`** — prints the resolved menu. Registry mode lists each section and everything the scan found; `--view <url_name>` instantiates the view, calls `setup_menu()` and walks `view.menus`, which is the only way to see the top-level skeleton and the `extra` items. `--format json` makes the output assertable.

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

Part of a cross-package migration (summary in `X:\CLAUDE.md`). Status here: **jQuery- and Popper-free** — keyboard shortcuts, dropdowns and context menus are all vanilla JS; dropdowns are positioned by vendored Floating UI.

### Done (uncommitted)
- `templates/django_menus/menu_key_press.html` converted to vanilla JS: `addEventListener('keydown')`, per-menu key dicts merged into a shared `window.django_menu_key_dict`, `django_modal` global now guarded.
- Supporting hygiene (relative imports, defensive dict copies, `find_packages()` in setup.py, readme rewrite) — not functional migration.

### `static/django_menus/django_menus.js` — vanilla, positioned with Floating UI
- Dropdowns are positioned by **Floating UI 1.8.0** (Popper's successor; Bootstrap 6 uses it too), vendored as `static/django_menus/floating-ui.core.umd.min.js` + `floating-ui.dom.umd.min.js` and loaded before `django_menus.js` by `includes.py` (`DjangoMenus.js_filename`, order pinned by `test_floating_ui_included_before_menus_js`). It exposes `window.FloatingUIDOM`, so it never clashes with the Popper v1 BS4's `bootstrap.js` needs; BS5 mode ships no usable Popper (`bootstrap.bundle`'s is private). To upgrade, replace both files from `cdn.jsdelivr.net/npm/@floating-ui/{core,dom}@<ver>/dist/*.umd.min.js` and bump the version in the `includes.py` comment.
- `show_menu()` uses `computePosition` with `offset(MENU_GAP)`, `flip()`, `shift()` and the default `absolute` strategy — same model as Popper v1 (correct inside transformed ancestors, scrolls with its container, clipped by `overflow` ancestors exactly as 0.0.17 was). `autoUpdate` keeps an open menu attached; its cleanup is stored on `menu._menu_cleanup` and every close goes through `hide_menu()`, which stops it. Placement names are Floating UI/Popper ones (`bottom-start` default, `bottom-end`, `right-start` for nested items).
- If `FloatingUIDOM` is missing (e.g. an AMD loader on the page captured the UMD build) menus still open, placed by Bootstrap's `.dropdown-menu` CSS.
- `dropdown_menu_function` / `dropdown_menu_click` take an id (what `dropdown.html` now passes), an element, or a jQuery object for custom templates written against the old version.
- `context_menu` inserts its html with `insert_context_menu()`, which re-creates `<script>` tags so nested dropdowns set themselves up — not via ajax_helpers' `replace_with`, which ajax-helpers 0.0.20 lacks.
- No JS test harness in the repo. The Floating UI switch was verified with a headless Playwright run (BS4 on ajax-helpers 0.0.22, BS5 on 1.0.1) against pages rendered from real `HtmlMenu` dropdowns: hover/click open-close, autoUpdate stopped on close, bottom-start/bottom-end/right-start, flip, page scroll, scrolling container, transformed ancestor, jQuery-object reference, no-Floating-UI fallback. Context menus were not re-tested (unchanged); the earlier probe against both docker services covered them, nested `right-start`, `data-ajax` routing and the AJAX dropdown.
- **ajax-helpers 1.0.0 is broken for AJAX POSTs:** its fetch client never sends `X-Requested-With`, but `is_ajax()` requires it, so every AJAX POST returns `None` → 500 (context menus, AJAX dropdowns, badge timers, buttons). Fixed in 1.0.1 (on PyPI). `pyproject.toml` excludes it (`django-ajax-helpers>=0.0.16,!=1.0.0` — the lower bound because `includes.py` passes a list as `js_filename`, supported since 0.0.16) and `settings_bs5` refuses to start on it.

### Bootstrap 5 — done (branch `bootstrap5`, based on `menu-registry`)
**`css_framework.py`** — the framework comes from the ecosystem-wide `CSS_FRAMEWORK` setting via `ajax_helpers.config.get_css_framework()` (falls back to reading the setting directly on ajax-helpers 0.0.x, which has no `config` module). No package-specific setting. Pattern borrowed from django-modals' `field_render.py`: `Bootstrap4Classes` holds class-name tokens, `Bootstrap5Classes` overrides only what differs, `FRAMEWORKS` maps name → class, `css_classes()` returns a cached instance.
- Templates receive the instance as `css` (`HtmlMenu.render`, `MenuItem.render`): `{{ css.align_start }}`/`{{ css.align_end }}` (main_menu), `{{ css.button_spacing }}` (button_menu), `{{ css.float_end }}` (context_menu). Custom templates still get `menu`/`menu_item` as before.
- Python-built markup: `MenuItemBadge` → `css_classes().badge(colour)`; `MenuItem.attr()` tooltip placement → `data-placement` / `data-bs-placement`.
- `ajax_tooltip.html` gets `tooltip_template` from `css_framework.tooltip_template()` — keyed on the **ajax_helpers version** (`AH_TOOLTIPS`: 1.0.0 → `ah-tooltip`/`ah-arrow`/`ah-tooltip-inner`), not on Bootstrap.
- Tests: `tests/test_css_framework.py`; BS4 output stays byte-identical (pinned by `test_regression.py`).
- Left: `static/django_menus/django_menus.css` targets `.navbar-dark` (deprecated in BS 5.3) — cosmetic.

## Releasing

Full process in `X:\CLAUDE.md` → "Releasing a package". Summary: once-over the diff since the last release tag (`git fetch --tags origin` first), bump `version` in `pyproject.toml` (packaging was converted from setup.py — the version now lives only there), commit, run `X:\release.bat` — it tags `v<version>` and pushes, and `.github/workflows/publish.yml` publishes to PyPI via trusted publishing. 0.0.18 (Oct 2026) was the first Actions release and the last jQuery/Popper one; 1.0.0 is this branch.

**Before releasing 1.0.0:** the `advance` remote (Tom's fork) brought its own `v1.0.0`–`v1.0.2` tags into the local repo, and `release.bat` pushes a local-only tag without checking which commit it points at. Delete them (`git tag -d v1.0.0 v1.0.1 v1.0.2`) and set `git config remote.advance.tagOpt --no-tags` first.
