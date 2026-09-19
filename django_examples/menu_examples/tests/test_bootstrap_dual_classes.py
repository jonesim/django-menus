"""Every Bootstrap 4 name in the package carries its Bootstrap 5 twin, and vice versa.

django-menus renders for projects on Bootstrap 4 and projects on Bootstrap 5 out of one set of
templates, by emitting both spellings side by side: `class="mr-1 me-1"`,
`data-placement="bottom" data-bs-placement="bottom"`. An unknown class or data attribute is
inert in either version, so each framework picks up the half it understands and ignores the
other. This is the convention django-cards adopted in #33, and the menu renders inside a card
header, so the two have to agree.

That only holds while it is done everywhere. A single template that gains an `ml-2` and no
`ms-2` is a gap nobody sees under Bootstrap 4 -- and a single `ms-1` with no `ml-1` is a gap
nobody sees under Bootstrap 5. Both directions are checked here.

The convention the checks encode:

- a class token is followed by its twin inside the same quoted run, in either order;
- a Bootstrap data attribute is followed immediately by its ``data-bs-`` twin with the same
  value, so ``data-placement="bottom" data-bs-placement="bottom"``.

The scanners are textual, so they cannot see a class built by an f-string or a data attribute
that only exists as a dict key. Both shapes are in ``menu_items.py``, so
``TestDualledNamesTheScannerCannotSee`` renders them and asserts on the output instead.
"""
import os
import re

from django.test import SimpleTestCase

import django_menus
from django_menus.menu import MenuItem
from django_menus.menu.menu_items import MenuItemBadge

PACKAGE_ROOT = os.path.dirname(os.path.abspath(django_menus.__file__))

# Directories holding third-party code that is not ours to respell. None today.
VENDORED = ()

# Bootstrap 4 token -> Bootstrap 5 token. Every pair is safe to carry together: the Bootstrap 5
# name is either absent from Bootstrap 4 (inert there) or present with the same meaning.
CLASS_PAIRS = {
    'float-left': 'float-start',
    'float-right': 'float-end',
    'text-left': 'text-start',
    'text-right': 'text-end',
    'dropdown-menu-right': 'dropdown-menu-end',
    'btn-block': 'w-100',
    'badge-pill': 'rounded-pill',
    'font-italic': 'fst-italic',
    'text-monospace': 'font-monospace',
    'sr-only': 'visually-hidden',
    'sr-only-focusable': 'visually-hidden-focusable',
    'custom-select': 'form-select',
    'custom-select-sm': 'form-select-sm',
    'arrow': 'tooltip-arrow',
}
for _c in ('primary', 'secondary', 'success', 'danger', 'warning', 'info', 'light', 'dark'):
    # text-bg-* rather than the bare bg-* django-cards pairs with, because a menu badge's
    # colour is the caller's: bg-warning on Bootstrap 5 leaves white text on yellow, while
    # text-bg-warning sets the contrasting foreground too. Inert on Bootstrap 4 either way.
    CLASS_PAIRS[f'badge-{_c}'] = f'text-bg-{_c}'
for _w in ('bold', 'bolder', 'normal', 'light', 'lighter'):
    CLASS_PAIRS[f'font-weight-{_w}'] = f'fw-{_w}'

# The spacing utilities, including the responsive variants (ml-sm-2) and the negative margins
# (ml-n2) -- a gap hides in those exactly as well as in the plain form.
_SIZES = [str(n) for n in range(6)] + ['auto'] + [f'n{n}' for n in range(1, 6)]
for _bp in ('', 'sm-', 'md-', 'lg-', 'xl-'):
    for _n in _SIZES:
        CLASS_PAIRS[f'ml-{_bp}{_n}'] = f'ms-{_bp}{_n}'
        CLASS_PAIRS[f'mr-{_bp}{_n}'] = f'me-{_bp}{_n}'
        if not _n.startswith('n'):  # padding has no negative scale
            CLASS_PAIRS[f'pl-{_bp}{_n}'] = f'ps-{_bp}{_n}'
            CLASS_PAIRS[f'pr-{_bp}{_n}'] = f'pe-{_bp}{_n}'
for _bp in ('sm-', 'md-', 'lg-', 'xl-'):
    CLASS_PAIRS[f'float-{_bp}left'] = f'float-{_bp}start'
    CLASS_PAIRS[f'float-{_bp}right'] = f'float-{_bp}end'
    CLASS_PAIRS[f'text-{_bp}left'] = f'text-{_bp}start'
    CLASS_PAIRS[f'text-{_bp}right'] = f'text-{_bp}end'

# The reverse check runs only over Bootstrap 5 names that do not exist in Bootstrap 4, so a bare
# one is unambiguously a gap. `w-100` and `rounded-pill` are left out: both are ordinary
# Bootstrap 4 utilities and stand on their own perfectly well.
_ALSO_VALID_IN_BS4 = ('w-100', 'rounded-pill')
BS5_ONLY = {bs5: bs4 for bs4, bs5 in CLASS_PAIRS.items() if bs5 not in _ALSO_VALID_IN_BS4}
# A <select> wants .form-select in Bootstrap 5 and .form-control in Bootstrap 4, so the
# Bootstrap 5 name never appears without the Bootstrap 4 one.
BS5_ONLY['form-select'] = 'form-control'
BS5_ONLY['form-select-sm'] = 'form-control-sm'

# Bootstrap's own data attributes, which became `data-bs-*` in Bootstrap 5. The list is the
# whole plugin option surface, not just the ones the package happens to use today -- the point
# of the test is the one somebody adds next.
DATA_ATTRS = (
    'toggle', 'target', 'dismiss', 'parent', 'content', 'trigger', 'placement', 'html',
    'offset', 'backdrop', 'keyboard', 'focus', 'ride', 'slide', 'slide-to', 'interval',
    'pause', 'wrap', 'container', 'delay', 'animation', 'boundary', 'display', 'reference',
    'spy', 'method', 'autohide',
)
# Deliberately absent: `title`, a Bootstrap tooltip option that collides with the plain HTML
# attribute django-menus sets beside its tooltip marker.

# `data-tooltip` is django-menus' own marker, read by the example app's initialiser and by
# ajax_helpers.tooltip. It was never Bootstrap's -- Bootstrap spells it `data-toggle="tooltip"`
# -- so it takes no `data-bs-` twin. It is not in DATA_ATTRS, and this documents why.
NOT_BOOTSTRAP = re.compile(r'data-tooltip=')

# A selector matching both spellings, e.g. `[data-toggle="tooltip"],[data-bs-toggle=...]`.
# That is a jQuery selector, not markup, so the "twin follows immediately" rule does not apply.
SELECTOR = re.compile(r'\[data-(?:bs-)?[a-z-]+=("[^"]*"|\'[^\']*\')\]')


def _source_files():
    for dirpath, _dirnames, filenames in os.walk(PACKAGE_ROOT):
        rel_dir = os.path.relpath(dirpath, PACKAGE_ROOT)
        if any(rel_dir.startswith(v) for v in VENDORED):
            continue
        for name in filenames:
            if name.endswith(('.html', '.py', '.js', '.css')):
                path = os.path.join(dirpath, name)
                yield os.path.relpath(path, PACKAGE_ROOT), open(path).read()


def _quoted_run(text, index):
    """The quoted string the character at `index` sits inside.

    Good enough to stand in for "the same class attribute" in a template and "the same string
    literal" in Python or JavaScript, which is the granularity the twin has to share. Falls
    back to the whole line when the token is not quoted at all.
    """
    line_start = text.rfind('\n', 0, index) + 1
    line_end = text.find('\n', index)
    if line_end == -1:
        line_end = len(text)
    best = (line_start, line_end)
    for quote in ('"', "'"):
        start = text.rfind(quote, line_start, index)
        if start == -1:
            continue
        end = text.find(quote, index)
        if end == -1 or end > line_end:
            continue
        if start > best[0]:
            best = (start, end)
    return text[best[0]:best[1]]


def _line_of(text, index):
    return text.count('\n', 0, index) + 1


class TestBootstrapClassesAreDualled(SimpleTestCase):

    def _scan(self, pairs):
        missing = []
        for rel_path, text in _source_files():
            for token, twin in pairs.items():
                for match in re.finditer(rf'(?<![\w-]){re.escape(token)}(?![\w-])', text):
                    run = _quoted_run(text, match.start())
                    if re.search(rf'(?<![\w-]){re.escape(twin)}(?![\w-])', run):
                        continue
                    missing.append(
                        f'{rel_path}:{_line_of(text, match.start())}: '
                        f'{token!r} without {twin!r}'
                    )
        return missing

    def test_every_bootstrap4_class_carries_its_bootstrap5_twin(self):
        missing = self._scan(CLASS_PAIRS)
        self.assertEqual(missing, [], 'Bootstrap 5 name missing beside a Bootstrap 4 one:\n'
                                      + '\n'.join(missing))

    def test_every_bootstrap5_only_class_carries_its_bootstrap4_twin(self):
        """The direction that fails silently on a Bootstrap 4 page."""
        missing = self._scan(BS5_ONLY)
        self.assertEqual(missing, [], 'Bootstrap 4 name missing beside a Bootstrap 5 one:\n'
                                      + '\n'.join(missing))


class TestBootstrapDataAttributesAreDualled(SimpleTestCase):

    def test_every_bootstrap_data_attribute_carries_its_data_bs_twin(self):
        missing = []
        for rel_path, text in _source_files():
            for attr in DATA_ATTRS:
                pattern = rf'(?<![\w-])data-{attr}=("[^"]*"|\'[^\']*\')'
                for match in re.finditer(pattern, text):
                    if NOT_BOOTSTRAP.match(match.group(0)):
                        continue
                    if SELECTOR.match(text, max(0, match.start() - 1)):
                        continue
                    twin = f' data-bs-{attr}={match.group(1)}'
                    if text[match.end():match.end() + len(twin)] == twin:
                        continue
                    missing.append(
                        f'{rel_path}:{_line_of(text, match.start())}: '
                        f'data-{attr} without data-bs-{attr} directly after it'
                    )
        self.assertEqual(missing, [], 'Bootstrap 5 data attribute missing:\n'
                                      + '\n'.join(missing))

    def test_no_data_bs_attribute_stands_alone(self):
        """The direction that fails silently on a Bootstrap 4 page."""
        missing = []
        for rel_path, text in _source_files():
            for attr in DATA_ATTRS:
                for match in re.finditer(rf'(?<![\w-])data-bs-{attr}=("[^"]*"|\'[^\']*\')', text):
                    if SELECTOR.match(text, max(0, match.start() - 1)):
                        continue
                    twin = f'data-{attr}={match.group(1)} '
                    if text[max(0, match.start() - len(twin)):match.start()] == twin:
                        continue
                    missing.append(
                        f'{rel_path}:{_line_of(text, match.start())}: '
                        f'data-bs-{attr} without data-{attr} directly before it'
                    )
        self.assertEqual(missing, [], 'Bootstrap 4 data attribute missing:\n'
                                      + '\n'.join(missing))


class TestNoFrameworkOwnedCloseButton(SimpleTestCase):
    """`.close` and `.btn-close` are the pair that cannot be carried together.

    Bootstrap 4's `.close` styles a `&times;` the markup supplies; Bootstrap 5's `.btn-close`
    must be empty and draws its own, so an element with both shows two crosses. Nothing in
    django-menus uses either today, and this keeps it that way rather than leaving the next
    person to discover the collision.
    """

    def test_close_classes_are_not_used(self):
        found = []
        for rel_path, text in _source_files():
            for match in re.finditer(r'''class=("[^"]*"|'[^']*')''', text):
                classes = match.group(1)[1:-1].split()
                if 'close' in classes or 'btn-close' in classes:
                    found.append(f'{rel_path}:{_line_of(text, match.start())}')
        self.assertEqual(found, [],
                         'Neither Bootstrap 4 .close nor Bootstrap 5 .btn-close can be '
                         'carried beside the other:\n' + '\n'.join(found))


class TestDualledNamesTheScannerCannotSee(SimpleTestCase):
    """The two places the textual checks above walk straight past.

    The badge's colour classes are built by an f-string from a caller-supplied `css_class`, and
    the tooltip's placement attribute exists only as a dict key. Neither is a literal the
    regexes can match, so they are rendered and asserted on directly.
    """

    def test_badge_carries_both_spellings(self):
        html = MenuItemBadge(text='4', css_class='primary').badge_html()
        for token in ('badge-pill', 'rounded-pill', 'badge-primary', 'text-bg-primary'):
            self.assertIn(token, html, f'{token!r} missing from the badge markup: {html}')

    def test_tooltip_placement_carries_both_spellings(self):
        attributes = MenuItem.attr({}, 'a tooltip')
        self.assertEqual(attributes.get('data-placement'), 'bottom')
        self.assertEqual(attributes.get('data-bs-placement'), 'bottom')
