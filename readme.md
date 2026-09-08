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
the milliseconds to hold a link for, at whichever level fits. They cascade
**item -> menu -> page -> off**, so the narrowest one set wins:

    # one item - usually the one that knows it minds being clicked twice
    MenuItem('next_stage', 'Go to Next Stage', django_menus_repeat_click_ms=2000)

    # every item in a menu that has not set its own
    HtmlMenu(request, 'button_group', django_menus_repeat_click_ms=2000)

    # a page, or a whole site if set on a base view class
    class MyView(MenuTemplateView):
        repeat_click_ms = 2000

Because an item's own value wins, one item can be held on a page with the guard off, and
`django_menus_repeat_click_ms=0` on an item opts it out where the page has it on.

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
