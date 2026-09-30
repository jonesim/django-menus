from ajax_helpers.html_include import SourceBase, pip_version


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


class DefaultInclude(DjangoMenus):
    pass
