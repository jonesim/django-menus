[![PyPI version](https://badge.fury.io/py/django-tab-menus.svg)](https://badge.fury.io/py/django-tab-menus)

Django app to render menus and load tabs with Ajax

See example django project with docker compose file 

Add to installed apps in settings   
`'django_menus',`
    

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
