from ajax_helpers.html_include import SourceBase, pip_version

try:
    from ajax_helpers.config import get_css_framework
except ImportError:  # ajax-helpers 0.0.x has no framework switch and only ever loaded Bootstrap 4
    def get_css_framework():
        from django.conf import settings
        return getattr(settings, 'CSS_FRAMEWORK', 'bootstrap4')


# The query string on the served django_menus.js/.css for a consumer that includes them plainly,
# so bump the package version whenever either file changes. Static is usually served with a
# far-future expiry and no content hashing, and an unchanged version leaves the URL byte
# identical - returning browsers would keep the file they already have and never run the new JS,
# which is exactly the users who have been there before. (A consumer passing its own `version=`,
# e.g. its git revision, busts the cache on every deploy and does not depend on this.)
version = pip_version('django-tab-menus')


class DjangoMenus(SourceBase):
    static_path = 'django_menus/'
    filename = 'django_menus'
    js_path = ''
    css_path = ''


class Popper2(SourceBase):
    """@popperjs/core 2, which the dropdowns position with under Bootstrap 5.

    Bootstrap 4 ships Popper 1 as a global constructor, and ajax-helpers loads it with the
    framework. Bootstrap 5's bundle carries Popper 2 privately and leaves ``window.Popper``
    unset, so under Bootstrap 5 nothing on the page positions a menu unless this is loaded.
    The script in django_menus.js detects whichever generation is present.
    """
    static_path = 'django_menus/popper/'
    cdn_path = 'cdn.jsdelivr.net/npm/@popperjs/core@2.11.8/dist/umd/'
    cdn_js_path = ''
    js_path = ''
    js_filename = 'popper.min.js'


class DefaultInclude(DjangoMenus):
    """The menus script and stylesheet, with Popper 2 in front of them under Bootstrap 5.

    Done inside ``javascript()`` rather than as a callable ``packages`` entry so it works on
    both ajax-helpers lines: the 0.0.x include tag only understands a list of classes.
    """

    def javascript(self):
        js = super().javascript()
        if get_css_framework() == 'bootstrap5':
            js = Popper2(self.version, self.legacy).includes(self.cdn) + js
        return js
