[![PyPI version](https://badge.fury.io/py/django-tab-menus.svg)](https://badge.fury.io/py/django-tab-menus)

Django app to render menus and load tabs with Ajax

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
the milliseconds to hold a link for:

    django_menus_repeat_click_ms = 2000;

It is read on each click rather than captured at load, and an assignment made before this app's
JS loads survives, so it can be set either side of the include and changed at any point in a
page's life. Set it back to `0` to turn it off again; anything that is not a number above zero
reads as off.

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

This is defence in depth, not a substitute for making such a view idempotent - the back button, a
refresh and a second tab all still send the request twice.
