[![PyPI version](https://img.shields.io/pypi/v/django-advanced-menus)](https://pypi.org/project/django-advanced-menus/)

# django-advanced-menus

Django app to render menus and load tabs with Ajax.

The [django-advance-utils](https://github.com/django-advance-utils) line of Ian Jones's
[django-tab-menus](https://github.com/jonesim/django-menus), forked so that releases can be cut as
the downstream libraries and django-advanced-report-builder need them. The Python package is still
`django_menus`, so existing imports and `INSTALLED_APPS` entries do not change; only the pip name
does. It depends on [ajax-advanced-helpers](https://github.com/django-advance-utils/ajax-advanced-helpers).

    pip install django-advanced-menus

See example django project with docker compose file 

Add to installed apps in settings   
`'django_menus',`
    

### Repeat clicks on menu links

Every menu item renders as an `<a href>`, and a menu item can point at a view that *does*
something rather than one that just shows a page. A double-click sends the URL twice, and a view
that resolves what to act on from its own current state - rather than from the state the link was
drawn against - acts on both.

This is **off by default** - swallowing a click is a behaviour change, and whether a project has
menu items pointing at views that mind being called twice is the project's business. Opt in with
the milliseconds to hold a link for, at whichever level fits. They cascade
**item -> menu -> page -> off**, so the narrowest one set wins:

    # one item - usually the one that knows it minds being clicked twice
    MenuItem('next_stage', 'Go to Next Stage', django_menus_repeat_click_ms=2000)

    # every item in a menu that has not set its own
    HtmlMenu(request, 'button_group', django_menus_repeat_click_ms=2000)

    # a page, or a whole site if set on a base view class
    class MyView(MenuTemplateView):
        repeat_click_ms = 2000

A target view can also declare it, which is arguably the best place - the view that minds being
called twice is the thing that knows:

    class MyView(View):
        menu_config = {'attributes': {'data-django-menus-repeat-ms': 2000}}

That sits below the item and menu arguments, which are set at the call site and so win.

Because an item's own value wins, one item can be held on a page with the guard off, and
`django_menus_repeat_click_ms=0` on an item opts it out where the page has it on. A menu-level
value also reaches the items of a dropdown built on one of that menu's items.

The first two forms render a `data-django-menus-repeat-ms` attribute on the anchor and need
nothing else. The view attribute reaches the page through the `django_menus_script` context
variable, so output that once in a base template, alongside the include:

    {% lib_include module='django_menus.includes' %}
    {{ django_menus_script }}

All that does is set a JS window of the same name, which the guard reads on every click rather
than capturing at load - so it can also be set or changed directly, from a page's own script or a
console while diagnosing, on either side of the include:

    django_menus_repeat_click_ms = 2000;

Anywhere it is set, `0` turns it off, and anything that is not a number above zero reads as off.

See the **Repeat Clicks** page in the example app for all three working side by side.

Once on, a second click on the same anchor inside that window is swallowed. Only real navigations
are affected - a `javascript:` href leaves the page in place and clicking again straight away is
often what the user means (close a modal, reopen it), so those are left alone, as are modified
clicks (ctrl/cmd/shift/alt, or any button but the primary) which open the link elsewhere.

Two limits worth knowing. The window collapses a double-click; it does not cover an impatient
re-click several seconds into a slow response, because holding a link until the page actually
goes away would strand anything that deliberately leaves the page up, like a download or a
`target="_blank"`. And the rule is about the href, not the effect: a `JAVASCRIPT` item is free to
set `window.location` itself, an `AJAX_BUTTON`'s view can answer with a redirect, and
`AJAX_GET_URL_NAME` fetches a view - those hit the view twice on a double-click just the same and
are out of scope here.

If you override these templates with your own copies, carry the `django-menus-item` class across
or those menus will not be covered.

### Showing that the click registered

While a link is held it carries a `django-menus-clicked` class. Swallowing the second click stops
the duplicate request, but people double-click *because* the first click appeared to do nothing,
so the class is there to let you address the cause as well:

    a.django-menus-clicked { opacity: .65; cursor: default; }

No styling is shipped for it, so it does nothing until a project adds a rule. Style the
appearance only - `pointer-events: none` looks like the obvious choice and lets the click fall
*through* to whatever sits underneath, which inside a dropdown is another menu item. The click is
already stopped in JS; the class only has to look the part.

The class is cleared when the hold expires, so a navigation that never arrives - cancelled, a
download, a `target="_blank"` - cannot leave a link looking permanently dead.

This is defence in depth, not a substitute for making such a view idempotent - the back button, a
refresh and a second tab all still send the request twice.

## Bootstrap 4 and Bootstrap 5

Menus ships a template pack per Bootstrap version:

    django_menus/templates/django_menus/bootstrap4/
    django_menus/templates/django_menus/bootstrap5/

Pick one in settings. Bootstrap 4 is the default:

```python
DJANGO_MENUS_TEMPLATE_PACK = 'bootstrap5'
```

Each pack holds the complete set of menu templates and emits only its own version's names, so
the rendered page carries no classes the browser will ignore, and the two packs are free to
diverge structurally where Bootstrap 5 changed more than a name.

**Serving both from one deployment.** The setting may instead be a dotted path to a callable
taking the request and returning a pack name — a pack name never contains a dot, which is what
tells the two apart. The example app uses that for its nav bar toggle:

```python
DJANGO_MENUS_TEMPLATE_PACK = 'menu_examples.context_processors.template_pack_for_request'
```

**Overriding a template.** Menus no longer ships anything at the old flat paths, and the flat
path is tried *before* the pack. So a project that already overrides `django_menus/main_menu.html`
in its own templates directory keeps that override, and anything it does not override falls
through to the pack. One consequence worth knowing: an override is version-agnostic by
definition, so it applies to both packs.

**What a pack does not reach.** Two things, both deliberate:

- A tooltip's placement is a key in the attributes dict rather than markup, so its Bootstrap 5
  rename lives in `django_menus/packs.py` as `PACK_ATTRIBUTES`. It is the only such entry.
- `css_classes`, `MenuItemDisplay`, the badge `css_class` and `attributes` are passed through
  untouched, so those are yours to spell:

  ```python
  MenuItem('view1', 'Edit', css_classes=['btn-primary', 'me-1'])
  ```

`menu_key_press.html` and `script.html` stay outside the packs — one is a keyboard handler and the
other sets the repeat-click window, neither is Bootstrap markup.

**Running the examples on either version.** The nav bar carries a `BS4 → BS5` toggle; it puts
`?bootstrap=5` on the URL and remembers the choice in the session, so a menu can be compared on
both without a restart. `MENUS_EXAMPLE_BOOTSTRAP=5` in the environment, or in settings, sets
where a fresh session starts.

Bootstrap 4 stays the default because the rest of the stack still emits it. On the Bootstrap 5
page the menus are correct and django-modals, show_src_code and crispy's template pack are
not — the example app makes that visible rather than hiding it, and it is the remaining work.

**Two settings, two paragraphs.** The template pack above is chosen by `DJANGO_MENUS_TEMPLATE_PACK`;
the scripts a page loads are chosen by the ecosystem-wide `CSS_FRAMEWORK` that ajax-helpers reads
(see the positioning section below). This paragraph describes Bootstrap 5 markup on a page whose
`CSS_FRAMEWORK` is still `bootstrap4`, so ajax-helpers still loads jQuery and Popper 1. With both
set to `bootstrap5`, ajax-helpers 1.0.1 loads neither and the menus include loads Popper 2 itself.

**The one load-order requirement.** jQuery must load before Bootstrap 5, which is what
`base.html` does. Bootstrap 5 dropped jQuery as a dependency and registers its plugin interface
only when jQuery got there first; without it `ajax_helpers.tooltip` quietly does nothing. The
same order keeps `window.Popper` pointing at the Popper 1 that ajax_helpers ships, which is what
the dropdown positioning is written against — Bootstrap 5's bundle keeps its own Popper 2
private. `django_menus.js` detects Popper 2 anyway, for a project that brings its own.

**One template this does not reach.** `ajax_tooltip.html` passes a Bootstrap-classed template to
`ajax_helpers.tooltip`, and ajax_helpers 1.0.0 rewrote that function around its own `ah-`
classes — it reads `.ah-tooltip-inner` out of whatever template it is handed. That template no
longer matches on either Bootstrap version, independently of anything here. No example view
exercises it. The fix is to stop passing a Bootstrap template and let ajax_helpers use its own,
which is version-neutral; it is left alone here because it is not a Bootstrap 5 question.

**Keeping the packs in step.** Two folders means a fix can land in one and not the other, and
unlike a missing class name that is invisible on whichever version you are not looking at. So
`menu_examples/tests/test_template_packs.py` normalises every Bootstrap 4 name in a pack4
template to its Bootstrap 5 spelling and requires the result to equal the pack5 file exactly.
A deliberate divergence goes in `STRUCTURAL_DIVERGENCE` with a note, which is the point at
which someone has to think about it. It is empty today: every difference is still a rename.

## Bootstrap 4 and Bootstrap 5: positioning the dropdowns

Dropdown menus are positioned with Popper. Bootstrap 4 puts Popper 1 on the page as a global
constructor, and that is what the menus have always used. Bootstrap 5 bundles Popper 2 privately
and leaves `window.Popper` unset, so under Bootstrap 5 the default include loads `@popperjs/core`
itself (vendored, with a jsDelivr fallback) and the script detects whichever generation it finds.
The switch is the ecosystem-wide `CSS_FRAMEWORK` setting that ajax-helpers reads:

```python
CSS_FRAMEWORK = 'bootstrap5'   # default 'bootstrap4'
```

Nothing changes under Bootstrap 4. With no Popper on the page at all, a menu opens straight
below its button.
