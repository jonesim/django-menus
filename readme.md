[![PyPI version](https://badge.fury.io/py/django-tab-menus.svg)](https://badge.fury.io/py/django-tab-menus)

Django app to render menus and load tabs with Ajax

See example django project with docker compose file 

Add to installed apps in settings   
`'django_menus',`
    

## Bootstrap 4 and Bootstrap 5

The menus render on either version, out of one set of templates. There is no version setting
to turn: everything Bootstrap 5 renamed is emitted under both spellings at once, and an
unrecognised class or data attribute is inert in either version, so each picks up the half it
understands.

```html
<ul class="navbar-nav ml-auto ms-auto">
<i class="fas fa-caret-right float-right float-end"></i>
<a title="Edit" data-placement="bottom" data-bs-placement="bottom">
```

This matches what django-cards does, which matters because the menu renders inside a card
header — a version switch in one package could not compose with a dual-emitting neighbour.

**What you have to do yourself.** `css_classes`, `MenuItemDisplay`, the badge `css_class` and
`attributes` are passed through untouched, so a project that wants to serve both versions
writes both names:

```python
MenuItem('view1', 'Edit', css_classes=['btn-primary', 'mr-1', 'me-1'])
```

**Running the examples on Bootstrap 5.** The nav bar carries a `BS4 → BS5` toggle; it puts
`?bootstrap=5` on the URL and remembers the choice in the session, so a menu can be compared
on both without a restart. `MENUS_EXAMPLE_BOOTSTRAP=5` in the environment, or in settings,
sets where a fresh session starts.

Bootstrap 4 stays the default because the rest of the stack still emits it. On the Bootstrap 5
page the menus are correct and django-modals, show_src_code and crispy's template pack are
not — the example app makes that visible rather than hiding it, and it is the remaining work.

**The one load-order requirement.** jQuery must load before Bootstrap 5, which is what
`base.html` does. Bootstrap 5 dropped jQuery as a dependency and registers its plugin
interface only when jQuery got there first; without it `ajax_helpers.tooltip` quietly does
nothing. The same order keeps `window.Popper` pointing at the Popper 1 that ajax_helpers
ships, which is what the dropdown positioning is written against — Bootstrap 5's bundle keeps
its own Popper 2 private. `django_menus.js` detects Popper 2 anyway, for a project that brings
its own.

**One template this does not reach.** `ajax_tooltip.html` passes a Bootstrap-classed template
to `ajax_helpers.tooltip`, and ajax_helpers 1.0.0 rewrote that function around its own `ah-`
classes -- it reads `.ah-tooltip-inner` out of whatever template it is handed. So that template
no longer matches on either Bootstrap version, independently of anything here. No example view
exercises it. The fix is to stop passing a Bootstrap template and let ajax_helpers use its own,
which is version-neutral; it is left alone here because it is not a Bootstrap 5 question.

**Keeping it dual.** `menu_examples/tests/test_bootstrap_dual_classes.py` scans the package for
a name of either version standing without its twin, and reports file and line. A gap is
invisible on whichever version nobody is looking at, so it is checked in both directions.
