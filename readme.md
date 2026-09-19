[![PyPI version](https://badge.fury.io/py/django-tab-menus.svg)](https://badge.fury.io/py/django-tab-menus)

Django app to render menus and load tabs with Ajax

See example django project with docker compose file 

Add to installed apps in settings   
`'django_menus',`
    

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

`menu_key_press.html` stays outside the packs — it is a keyboard handler, not Bootstrap markup.

**Running the examples on either version.** The nav bar carries a `BS4 → BS5` toggle; it puts
`?bootstrap=5` on the URL and remembers the choice in the session, so a menu can be compared on
both without a restart. `MENUS_EXAMPLE_BOOTSTRAP=5` in the environment, or in settings, sets
where a fresh session starts.

Bootstrap 4 stays the default because the rest of the stack still emits it. On the Bootstrap 5
page the menus are correct and django-modals, show_src_code and crispy's template pack are
not — the example app makes that visible rather than hiding it, and it is the remaining work.

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
