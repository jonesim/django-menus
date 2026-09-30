"""The two Bootstrap packs stay in step, and each renders its own version's names.

django-menus ships one template folder per Bootstrap version. That buys clean markup and room
for the versions to diverge structurally, at the cost dual emission did not have: a fix applied
to one pack and not the other is **silent**. Nothing in the rendered page looks wrong on the
version you happen to be looking at, and there is no twin missing from a class attribute for a
scanner to notice.

So the drift is what is pinned here. `test_packs_are_identical_once_renamed` normalises every
Bootstrap 4 name in a pack4 template to its Bootstrap 5 spelling and requires the result to
equal the pack5 template exactly. A caret fixed in one pack and not the other fails it, naming
the file. When the packs are *meant* to diverge -- a structural difference dual emission could
not have expressed, which is the reason for having packs at all -- the pair is added to
STRUCTURAL_DIVERGENCE with a note, and that is the moment someone has to think about it.
"""
import os
import re

from django.template.loader import render_to_string
from django.test import SimpleTestCase, override_settings

import django_menus
from django_menus.menu import HtmlMenu, MenuItem
from django_menus.menu.menu_items import DividerItem, HeaderItem, MenuItemBadge
from django_menus.packs import pack_attribute, template_pack

TEMPLATE_ROOT = os.path.join(os.path.dirname(os.path.abspath(django_menus.__file__)),
                             'templates', 'django_menus')
PACKS = ('bootstrap4', 'bootstrap5')

# Bootstrap 4 token -> Bootstrap 5 token, applied to normalise a pack4 template before
# comparing it with its pack5 twin. Only renames belong here.
RENAMES = {
    'float-left': 'float-start', 'float-right': 'float-end',
    'text-left': 'text-start', 'text-right': 'text-end',
    'dropdown-menu-right': 'dropdown-menu-end',
    'btn-block': 'w-100',
    'badge-pill': 'rounded-pill',
    'font-italic': 'fst-italic', 'text-monospace': 'font-monospace',
    'sr-only': 'visually-hidden', 'sr-only-focusable': 'visually-hidden-focusable',
    'custom-select': 'form-select', 'custom-select-sm': 'form-select-sm',
    'arrow': 'tooltip-arrow',
    'close': 'btn-close',
}
for _c in ('primary', 'secondary', 'success', 'danger', 'warning', 'info', 'light', 'dark'):
    RENAMES[f'badge-{_c}'] = f'text-bg-{_c}'
# The badge colour is a caller-supplied css_class interpolated into the template, so the
# literal pairs above never match it. It is still a rename, so it belongs here rather than in
# STRUCTURAL_DIVERGENCE -- and text-bg- rather than the bare bg- because a badge coloured
# `warning` needs Bootstrap 5 to pick the dark foreground that goes with a yellow ground.
RENAMES['badge-{{ badge.css_class }}'] = 'text-bg-{{ badge.css_class }}'
for _w in ('bold', 'bolder', 'normal', 'light', 'lighter'):
    RENAMES[f'font-weight-{_w}'] = f'fw-{_w}'
_SIZES = [str(n) for n in range(6)] + ['auto'] + [f'n{n}' for n in range(1, 6)]
for _bp in ('', 'sm-', 'md-', 'lg-', 'xl-'):
    for _n in _SIZES:
        RENAMES[f'ml-{_bp}{_n}'] = f'ms-{_bp}{_n}'
        RENAMES[f'mr-{_bp}{_n}'] = f'me-{_bp}{_n}'
        if not _n.startswith('n'):
            RENAMES[f'pl-{_bp}{_n}'] = f'ps-{_bp}{_n}'
            RENAMES[f'pr-{_bp}{_n}'] = f'pe-{_bp}{_n}'
# Bootstrap's own data attributes, which became data-bs-* in Bootstrap 5. The whole plugin
# option surface, not just what the packs use today -- the point is the one added next.
DATA_ATTRS = (
    'toggle', 'target', 'dismiss', 'parent', 'content', 'trigger', 'placement', 'html',
    'offset', 'backdrop', 'keyboard', 'focus', 'ride', 'slide', 'slide-to', 'interval',
    'pause', 'wrap', 'container', 'delay', 'animation', 'boundary', 'display', 'reference',
    'spy', 'method', 'autohide',
)

# Templates whose two packs differ by more than a rename, each with why. Empty on purpose:
# every difference today is a rename, which is the argument for having kept this small.
STRUCTURAL_DIVERGENCE = {}


def _normalise(text):
    """Rewrite a Bootstrap 4 template into how the Bootstrap 5 one should read."""
    for bs4, bs5 in sorted(RENAMES.items(), key=lambda kv: -len(kv[0])):
        text = re.sub(rf'(?<![\w-]){re.escape(bs4)}(?![\w-])', bs5, text)
    for attr in DATA_ATTRS:
        text = re.sub(rf'(?<![\w-])data-{attr}=', f'data-bs-{attr}=', text)
    return text


def _pack_files(pack):
    return sorted(f for f in os.listdir(os.path.join(TEMPLATE_ROOT, pack)) if f.endswith('.html'))


def _read(pack, name):
    with open(os.path.join(TEMPLATE_ROOT, pack, name)) as f:
        return f.read()


class TestPacksStayInStep(SimpleTestCase):

    def test_packs_hold_the_same_templates(self):
        self.assertEqual(_pack_files('bootstrap4'), _pack_files('bootstrap5'),
                         'A template was added to one pack and not the other')

    def test_packs_are_identical_once_renamed(self):
        """The check that catches a fix applied to one pack only."""
        drifted = []
        for name in _pack_files('bootstrap4'):
            if name in STRUCTURAL_DIVERGENCE:
                continue
            if _normalise(_read('bootstrap4', name)) != _read('bootstrap5', name):
                drifted.append(name)
        self.assertEqual(drifted, [],
                         'These differ by more than a Bootstrap rename. Either the two packs '
                         'have drifted, or the difference is deliberate and belongs in '
                         'STRUCTURAL_DIVERGENCE with a note:\n' + '\n'.join(drifted))

    def test_no_bootstrap4_names_left_in_the_bootstrap5_pack(self):
        """A pack5 template that kept a Bootstrap 4 spelling renders nothing on 5."""
        found = []
        for name in _pack_files('bootstrap5'):
            text = _read('bootstrap5', name)
            for bs4 in RENAMES:
                if re.search(rf'(?<![\w-]){re.escape(bs4)}(?![\w-])', text):
                    found.append(f'bootstrap5/{name}: {bs4!r}')
            for attr in DATA_ATTRS:
                if re.search(rf'(?<![\w-])data-{attr}=', text):
                    found.append(f'bootstrap5/{name}: data-{attr}')
        self.assertEqual(found, [], 'Bootstrap 4 names in the Bootstrap 5 pack:\n' + '\n'.join(found))


class TestPackSelection(SimpleTestCase):
    """The setting actually reaches the markup, for templates and for the bits built in Python."""

    def _menu_html(self, pack):
        with override_settings(DJANGO_MENUS_TEMPLATE_PACK=pack):
            menu = HtmlMenu(template='buttons').add_items(MenuItem('/x/', 'Edit', link_type=MenuItem.HREF))
            return menu.render()

    def test_button_menu_spacing_follows_the_pack(self):
        self.assertIn('mr-1', self._menu_html('bootstrap4'))
        self.assertNotIn('me-1', self._menu_html('bootstrap4'))
        self.assertIn('me-1', self._menu_html('bootstrap5'))
        self.assertNotIn('mr-1', self._menu_html('bootstrap5'))

    def test_badge_follows_the_pack(self):
        badge = MenuItemBadge(text='4', css_class='warning')
        with override_settings(DJANGO_MENUS_TEMPLATE_PACK='bootstrap4'):
            self.assertIn('badge-pill', badge.badge_html())
            self.assertIn('badge-warning', badge.badge_html())
        with override_settings(DJANGO_MENUS_TEMPLATE_PACK='bootstrap5'):
            self.assertIn('rounded-pill', badge.badge_html())
            self.assertIn('text-bg-warning', badge.badge_html())
            self.assertNotIn('badge-pill', badge.badge_html())

    def test_tooltip_placement_attribute_follows_the_pack(self):
        """The one Bootstrap name that is a dict key rather than markup."""
        with override_settings(DJANGO_MENUS_TEMPLATE_PACK='bootstrap4'):
            self.assertEqual(pack_attribute('placement'), 'data-placement')
            item = MenuItem('/x/', 'Edit', link_type=MenuItem.HREF, tooltip='tip')
            item.menu = HtmlMenu()
            self.assertIn('data-placement="bottom"', item.attributes())
        with override_settings(DJANGO_MENUS_TEMPLATE_PACK='bootstrap5'):
            self.assertEqual(pack_attribute('placement'), 'data-bs-placement')
            item = MenuItem('/x/', 'Edit', link_type=MenuItem.HREF, tooltip='tip')
            item.menu = HtmlMenu()
            self.assertIn('data-bs-placement="bottom"', item.attributes())

    def test_divider_and_header_follow_the_pack(self):
        menu = HtmlMenu()
        for pack in PACKS:
            with override_settings(DJANGO_MENUS_TEMPLATE_PACK=pack):
                divider, header = DividerItem(menu=menu), HeaderItem(text='Group', menu=menu)
                self.assertIn('dropdown-divider', divider.render())
                self.assertIn('Group', header.render())

    def test_default_is_bootstrap4(self):
        with override_settings():
            del_settings = override_settings()
            del_settings.enable()
            try:
                self.assertEqual(template_pack(), 'bootstrap4')
            finally:
                del_settings.disable()

    def test_setting_may_be_a_callable_taking_the_request(self):
        """How the example app serves both versions off one deployment."""
        with override_settings(DJANGO_MENUS_TEMPLATE_PACK=lambda request: 'bootstrap5'):
            self.assertEqual(template_pack(None), 'bootstrap5')
        with override_settings(
                DJANGO_MENUS_TEMPLATE_PACK='menu_examples.tests.test_template_packs.pack_five'):
            self.assertEqual(template_pack(None), 'bootstrap5')


def pack_five(_request):
    """Target for the dotted-path form of the setting, exercised above."""
    return 'bootstrap5'


class TestProjectOverrideStillWins(SimpleTestCase):
    """Moving the templates into packs must not break a project that overrode a flat path.

    Menus ships nothing at ``django_menus/<name>.html`` any more, so that path resolves only
    if the project supplies it -- and it is tried first, ahead of the pack.
    """

    def test_flat_path_is_tried_before_the_pack(self):
        from django_menus.packs import pack_template
        template = pack_template('button_menu.html')
        self.assertTrue(template.template.name.endswith('bootstrap4/button_menu.html'),
                        f'resolved to {template.template.name}')

    def test_package_ships_nothing_at_the_flat_paths(self):
        flat = [f for f in os.listdir(TEMPLATE_ROOT) if f.endswith('.html')]
        self.assertEqual(flat, ['menu_key_press.html', 'script.html'],
                         'Only the keyboard handler and the repeat-click script belong outside the packs; anything else '
                         'here shadows both packs for every project.')


class TestNoFrameworkOwnedCloseButton(SimpleTestCase):
    """`.close` and `.btn-close` were the pair dual emission could not carry together.

    A pack can express them, which is the argument for packs -- so this is a reminder rather
    than a prohibition: neither is used today, and if one ever is, its twin must appear in the
    other pack rather than in the same class attribute.
    """

    def test_close_classes_are_not_used(self):
        found = []
        for pack in PACKS:
            for name in _pack_files(pack):
                for match in re.finditer(r'''class=("[^"]*"|'[^']*')''', _read(pack, name)):
                    classes = match.group(1)[1:-1].split()
                    if 'close' in classes or 'btn-close' in classes:
                        found.append(f'{pack}/{name}')
        self.assertEqual(found, [], '\n'.join(found))


class TestRenderedPagesUseOneVersionOnly(SimpleTestCase):
    """End to end: a rendered menu carries its pack's names and none of the other's."""

    def test_rendered_menu_is_single_version(self):
        for pack, wanted, unwanted in (('bootstrap4', 'mr-auto', 'me-auto'),
                                       ('bootstrap5', 'me-auto', 'mr-auto')):
            with override_settings(DJANGO_MENUS_TEMPLATE_PACK=pack):
                html = HtmlMenu(template='base').add_items(
                    MenuItem('/x/', 'One', link_type=MenuItem.HREF)).render()
                self.assertIn(wanted, html)
                self.assertNotIn(unwanted, html)
