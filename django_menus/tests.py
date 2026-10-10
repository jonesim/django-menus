"""What a menu item renders into its tag.

The first tests in this package. They cover ``MenuItem.attributes`` -- and specifically the
accessible name of an item shown as an icon with no words, which is the only thing a screen
reader has to go on and used to be the icon font's private use codepoint.
"""

from django.test import SimpleTestCase
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django_menus.menu import HtmlMenu, MenuItem, MenuItemDisplay


def attributes_of(**kwargs) -> str:
    """The attribute string an item renders into its ``<a>``.

    ``link_type=MenuItem.HREF`` throughout: these tests are about the attributes, and a url name
    would send the item looking for a urlconf that has nothing to do with what is being asked.
    """
    return str(MenuItem(url='#', link_type=MenuItem.HREF, **kwargs).attributes())


class AnIconOnlyItemIsNamedForAssistiveTechnology(SimpleTestCase):
    """An item with an icon and no words: the tooltip is the only wording it has, so it is also
    the accessible name. Without this the name is whatever the font renders in ``::before`` --
    for Font Awesome a private use codepoint, announced as nothing a reader can act on."""

    def test_an_icon_with_a_tooltip_and_no_text_is_labelled(self):
        rendered = attributes_of(menu_display=MenuItemDisplay('', font_awesome='fa fa-plus', tooltip='Add'))

        self.assertIn('aria-label="Add"', rendered)

    def test_the_label_is_the_tooltip_the_sighted_reader_sees(self):
        """Not a second wording to keep in step -- the same string reaches both."""
        rendered = attributes_of(menu_display=MenuItemDisplay('', font_awesome='fa fa-pencil', tooltip='Edit'))

        self.assertIn('title="Edit"', rendered)
        self.assertIn('aria-label="Edit"', rendered)

    def test_a_tooltip_on_the_item_rather_than_the_display_counts_too(self):
        """``MenuItem(tooltip=…)`` and ``MenuItemDisplay(tooltip=…)`` both end up as ``title``."""
        rendered = attributes_of(menu_display=MenuItemDisplay('', font_awesome='fa fa-trash'), tooltip='Remove')

        self.assertIn('aria-label="Remove"', rendered)


class AnItemThatShowsWordsIsLeftAlone(SimpleTestCase):
    """``aria-label`` overrides the visible label, so putting one on an item that already shows
    words makes what is announced differ from what is on screen wherever the tooltip says
    something else -- which is what a tooltip is usually for."""

    def test_words_and_a_tooltip_get_no_label(self):
        rendered = attributes_of(
            menu_display=MenuItemDisplay('Add', font_awesome='fa fa-plus', tooltip='Add a new one')
        )

        self.assertIn('title="Add a new one"', rendered)
        self.assertNotIn('aria-label', rendered)

    def test_words_alone_get_no_label(self):
        self.assertNotIn('aria-label', attributes_of(menu_display=MenuItemDisplay('Add')))


class NothingIsInvented(SimpleTestCase):
    def test_an_icon_with_no_tooltip_is_not_given_a_name(self):
        """There is no wording to use. Naming it after the icon class would be worse than silence."""
        self.assertNotIn('aria-label', attributes_of(menu_display=MenuItemDisplay('', font_awesome='fa fa-plus')))

    def test_a_label_the_caller_passed_is_not_overwritten(self):
        rendered = attributes_of(
            menu_display=MenuItemDisplay('', font_awesome='fa fa-plus', tooltip='Add'),
            attributes={'aria-label': 'Add a door blank size'},
        )

        self.assertIn('aria-label="Add a door blank size"', rendered)
        self.assertNotIn('aria-label="Add"', rendered)


class TheRenderedNameIsUnchanged(SimpleTestCase):
    """The icon is deliberately not marked ``aria-hidden``: that would drop the glyph from every
    labelled item's accessible name too, which is a breaking change for callers selecting on the
    name rather than a fix for anyone reading the page."""

    def test_an_icon_and_words_still_render_both(self):
        display = MenuItemDisplay('Add', font_awesome='fa fa-plus')

        self.assertEqual(display.display(), '<i class="fa fa-plus"></i> Add')

    def test_the_icon_carries_no_aria_hidden(self):
        self.assertNotIn('aria-hidden', MenuItemDisplay('', font_awesome='fa fa-plus').display())


class ALabelIsTextUnlessItSaysOtherwise(SimpleTestCase):
    """``display()`` escapes a label that is not marked safe.

    It used to ``mark_safe`` whatever it was given, so an item whose label came from a value --
    a project name, a file name, a report's name -- wrote that value into the page as markup.
    A label that is markup on purpose says so where it is made, and keeps working.
    """

    PAYLOAD = '<img src=x onerror=alert(1)>'

    def test_a_label_holding_markup_is_escaped(self):
        self.assertEqual(MenuItemDisplay(self.PAYLOAD).display(), '&lt;img src=x onerror=alert(1)&gt;')

    def test_a_label_holding_markup_is_escaped_beside_an_icon_too(self):
        """The icon branch is a second renderer, and the one a menu item usually takes."""
        rendered = MenuItemDisplay(self.PAYLOAD, font_awesome='fa fa-plus').display()

        self.assertNotIn('<img', rendered)
        self.assertIn('<i class="fa fa-plus"></i>', rendered)

    def test_a_label_marked_safe_is_still_markup(self):
        """``mark_safe``/``format_html``/a rendered template: the caller's own markup goes through."""
        display = MenuItemDisplay(mark_safe('<i class="fa fa-lock"></i> Disable'))

        self.assertEqual(display.display(), '<i class="fa fa-lock"></i> Disable')

    def test_a_label_already_escaped_is_not_escaped_twice(self):
        """Callers escaped their own labels while this marked everything safe. They still work."""
        self.assertEqual(MenuItemDisplay(escape(self.PAYLOAD)).display(), '&lt;img src=x onerror=alert(1)&gt;')

    def test_the_icon_class_cannot_end_its_attribute(self):
        rendered = MenuItemDisplay('Add', font_awesome='fa" onmouseover="alert(1)').display()

        self.assertNotIn('onmouseover="', rendered)

    def test_a_label_of_none_still_reads_as_none(self):
        """Unchanged: a display with no text showed ``None`` before and shows it now."""
        self.assertEqual(MenuItemDisplay(None).display(), 'None')


class AnAttributeValueIsTextToo(SimpleTestCase):
    """``attributes()`` writes each value inside double quotes, and marked them all safe.

    A tooltip is the one that holds text somebody typed, so a quote in it closed ``title=""`` and
    whatever followed was read as further attributes.
    """

    def test_a_quote_in_a_tooltip_cannot_start_another_attribute(self):
        rendered = attributes_of(menu_display=MenuItemDisplay('Edit', tooltip='Bo" onmouseover="alert(1)'))

        self.assertNotIn('onmouseover="', rendered)
        self.assertIn('&quot;', rendered)

    def test_an_ordinary_tooltip_is_unchanged(self):
        self.assertIn('title="Edit"', attributes_of(menu_display=MenuItemDisplay('Edit', tooltip='Edit')))

    def test_a_tooltip_already_escaped_is_not_escaped_twice(self):
        rendered = attributes_of(menu_display=MenuItemDisplay('Edit', tooltip=escape('Bo"b')))

        self.assertIn('title="Bo&quot;b"', rendered)
        self.assertNotIn('&amp;quot;', rendered)


class ADefaultIsKeyedOnTheLabelNotOnItsRendering(SimpleTestCase):
    """``button_defaults`` is looked up on the label the caller gave, not on the rendered one.

    `MenuItem.menu`'s setter matched `self.name`, which is `MenuItemDisplay.display()` -- the
    label as it reaches the page. Once that escapes, a default keyed `R&D` stops matching an item
    labelled `R&D`, silently, because the key it is compared against has become `R&amp;D`. A key
    is not a rendering, so the lookup has its own.
    """

    @staticmethod
    def displayed(label, defaults, **kwargs):
        menu = HtmlMenu(button_defaults=defaults).add_items(
            MenuItem(url='#', link_type=MenuItem.HREF, menu_display=label, **kwargs)
        )
        return menu.menu_items[0].menu_display

    def test_a_default_keyed_with_an_ampersand_still_applies(self):
        display = self.displayed('R&D', {'R&D': MenuItemDisplay('Research', 'fa fa-flask')})

        self.assertEqual('Research', display.text)

    def test_an_ordinary_default_still_applies(self):
        display = self.displayed('edit', {'edit': MenuItemDisplay('Edit-default', 'fas fa-pen')})

        self.assertEqual('Edit-default', display.text)

    def test_an_item_with_its_own_icon_matches_exactly_what_it_matched_before(self):
        """Unchanged on purpose.

        ``display()`` put the icon's ``<i>`` in front of the words, so an item carrying its own
        ``font_awesome`` never matched a plain key and does not start to now. Keying on the text
        alone would read better and would change which items pick up a default, which is a
        separate question from escaping.
        """
        display = self.displayed('edit', {'edit': MenuItemDisplay('Edit-default')}, font_awesome='fa fa-star')

        self.assertEqual('edit', display.text)

    def test_the_rendered_label_is_still_escaped(self):
        """The key is unescaped; what reaches the page is not."""
        menu = HtmlMenu(button_defaults={}).add_items(
            MenuItem(url='#', link_type=MenuItem.HREF, menu_display='R&D')
        )

        self.assertEqual('R&amp;D', menu.menu_items[0].name)


class ADefaultKeyIsAStringWhateverTheLabelWas(SimpleTestCase):
    """A label that is not a string still keys the same default it used to.

    The lookup used to go through ``mark_safe(self.text)``, and ``SafeString`` is a ``str``
    subclass: ``SafeString(None)`` is ``'None'`` and ``SafeString(1)`` is ``'1'``. So a default has
    always been keyed by the **string**, even when the label was not one. Handing back the raw
    value instead would stop a default keyed ``'None'`` matching and start one keyed ``None``
    matching -- a silent swap, in the one property whose whole job is to not move the key.
    """

    @staticmethod
    def key_for(label, **kwargs):
        return MenuItem(url='#', link_type=MenuItem.HREF, menu_display=label, **kwargs).default_key

    def test_a_label_of_none_keys_the_string(self):
        self.assertEqual('None', self.key_for(None))

    def test_a_number_label_keys_the_string(self):
        self.assertEqual('1', self.key_for(1))
        self.assertEqual('0', self.key_for(0))

    def test_a_default_keyed_by_the_string_still_applies_to_a_number_label(self):
        """The end of the path, not just the property: a menu, a default, and the item picking it up."""
        menu = HtmlMenu(button_defaults={'1': MenuItemDisplay('Numbered')}).add_items(
            MenuItem(url='#', link_type=MenuItem.HREF, menu_display=1)
        )

        self.assertEqual('Numbered', menu.menu_items[0].menu_display.text)

    def test_an_ordinary_label_is_unchanged(self):
        self.assertEqual('edit', self.key_for('edit'))

    def test_an_icon_label_still_carries_its_icon_into_the_key(self):
        """Documented in the README as the sharp edge of keeping the old behaviour."""
        self.assertEqual('<i class="fa fa-pen"></i> edit', self.key_for('edit', font_awesome='fa fa-pen'))


class AnAttributeNameIsCheckedNotEscaped(SimpleTestCase):
    """A key cannot introduce a second attribute.

    Escaping the value and not the name is false assurance: a name is not quoted, so the
    characters that do the damage are the ones that end it. A key of ``x onmouseover`` renders
    ``x onmouseover="..."``, which the browser reads as an event handler however carefully the
    value beside it was escaped. Both the public ``attributes=`` mapping and the
    ``menu_config['attributes']`` callable let a caller supply a key.
    """

    def test_a_key_cannot_open_an_event_handler(self):
        rendered = attributes_of(attributes={'x onmouseover': 'alert(1)'})

        self.assertNotIn('onmouseover', rendered)

    def test_an_event_handler_name_is_refused_outright(self):
        """Not only the smuggled kind: a key alone never becomes an ``on*``."""
        self.assertNotIn('onclick', attributes_of(attributes={'onclick': 'alert(1)'}))
        self.assertNotIn('onClick', attributes_of(attributes={'onClick': 'alert(1)'}))

    def test_a_key_cannot_close_the_tag(self):
        for key in ('x>', 'x"', "x'", 'x=y', 'x/'):
            with self.subTest(key=key):
                rendered = attributes_of(attributes={key: 'v'})

                self.assertNotIn(key, rendered)

    def test_whitespace_cannot_hide_at_the_end_of_a_key(self):
        """``$`` matches before a trailing newline, so ``match`` let ``data-id\\n`` through.

        Not an injection by itself -- a parser reads the newline as the whitespace it already
        allows before the ``=`` -- but a check has to mean what its docstring says, or the next
        person reads the policy and not the gap in it. ``fullmatch`` closes it.
        """
        for key in ('data-id\n', 'data-id\r', 'data-id\t', 'data-id '):
            with self.subTest(key=repr(key)):
                self.assertNotIn('data-id', attributes_of(attributes={key: 'v'}))

    def test_the_names_a_menu_actually_uses_still_render(self):
        """Including `x-on:click`, which is kept on purpose.

        It is an executable directive wherever Alpine is loaded, so the check is not a promise
        that a name is inert -- only that it cannot become markup, and cannot be a native `on*`.
        Refusing framework directives would break the callers using them deliberately and the
        list has no end (`@click`, `v-on:`, `hx-on:`, `data-action`, and whatever is next), and a
        `data-*` allowlist would not help anyone whose attribute *names* come from user input,
        which is the only way this arises.
        """
        rendered = attributes_of(
            attributes={'data-id': '7', 'aria-hidden': 'true', 'hx-get': '/x', 'x-on:click': 'go'},
            menu_display=MenuItemDisplay('Edit', tooltip='Edit'),
        )

        for expected in ('data-id="7"', 'aria-hidden="true"', 'hx-get="/x"', 'x-on:click="go"', 'title="Edit"'):
            self.assertIn(expected, rendered)

    def test_a_refused_name_does_not_take_the_others_with_it(self):
        rendered = attributes_of(attributes={'data-id': '7', 'x onmouseover': 'alert(1)'})

        self.assertIn('data-id="7"', rendered)
        self.assertNotIn('onmouseover', rendered)


class _HtmlLabel:
    """A hashable object carrying Django's html protocol, usable as a label and as a key."""

    def __init__(self, markup):
        self.markup = markup

    def __html__(self):
        return self.markup

    def __hash__(self):
        return hash(self.markup)

    def __eq__(self, other):
        return isinstance(other, _HtmlLabel) and other.markup == self.markup


class AnHtmlObjectLabelKeysTheSameDefault(SimpleTestCase):
    """``mark_safe`` hands back an object with ``__html__`` unchanged, and ``str()`` would not.

    So an HTML-safe object used as both the label and the `button_defaults` key matched before the
    escaping change, and has to go on matching. This is why `default_key` is the old expression
    rather than something that merely looks equivalent.
    """

    def test_the_object_itself_is_the_key(self):
        label = _HtmlLabel('<b>Edit</b>')

        self.assertEqual(label, MenuItem(url='#', link_type=MenuItem.HREF, menu_display=label).default_key)

    def test_a_default_keyed_by_that_object_still_applies(self):
        label = _HtmlLabel('<b>Edit</b>')
        menu = HtmlMenu(button_defaults={label: MenuItemDisplay('Resolved')}).add_items(
            MenuItem(url='#', link_type=MenuItem.HREF, menu_display=label)
        )

        self.assertEqual('Resolved', menu.menu_items[0].menu_display.text)

    def test_its_markup_still_reaches_the_page(self):
        """It says it is html, so it is html -- the escaping change does not touch it."""
        label = _HtmlLabel('<b>Edit</b>')

        self.assertEqual('<b>Edit</b>', MenuItemDisplay(label).display())
class _TwoFacedName:
    """A key whose `__format__` says something other than its `__str__`.

    Contrived on purpose. The point is not that a caller would write this, it is that the check
    and the render have to agree about what the name *is*, and an f-string calls `__format__`.
    """

    def __str__(self):
        return 'data-id'

    def __format__(self, spec):
        return 'x onmouseover'

    def __hash__(self):
        return hash('data-id')

    def __eq__(self, other):
        return isinstance(other, _TwoFacedName)


class TheCheckedNameIsTheRenderedName(SimpleTestCase):
    def test_a_key_cannot_say_one_thing_to_the_check_and_another_to_the_render(self):
        rendered = attributes_of(attributes={_TwoFacedName(): 'alert(1)'})

        self.assertNotIn('onmouseover', rendered)


class _ShoutingDisplay(MenuItemDisplay):
    """A display with its own renderer, of the kind the old lookup let choose its own key."""

    def display(self):
        return mark_safe(f'<em>{escape(self.text)}</em>')

    def default_key(self):
        return f'shouted:{self.text}'


class ADisplaySubclassSaysWhatItsKeyIs(SimpleTestCase):
    """The lookup used to go through `display()`, so an override chose the key for free.

    Splitting the key off from the rendering is what stops escaping moving it -- but it would
    also have taken that from a subclass, silently, so the key is the display's to answer and a
    subclass overrides it there.
    """

    def test_the_subclass_decides_the_key(self):
        item = MenuItem(url='#', link_type=MenuItem.HREF, menu_display=_ShoutingDisplay('Edit'))

        self.assertEqual('shouted:Edit', item.default_key)

    def test_and_that_key_is_what_a_default_is_matched_on(self):
        menu = HtmlMenu(button_defaults={'shouted:Edit': MenuItemDisplay('Resolved')}).add_items(
            MenuItem(url='#', link_type=MenuItem.HREF, menu_display=_ShoutingDisplay('Edit'))
        )

        self.assertEqual('Resolved', menu.menu_items[0].menu_display.text)

    def test_a_display_that_overrides_nothing_is_unaffected(self):
        item = MenuItem(url='#', link_type=MenuItem.HREF, menu_display=MenuItemDisplay('Edit'))

        self.assertEqual('Edit', item.default_key)
class _RendererOnlyDisplay(MenuItemDisplay):
    """A subclass of the kind that existed before `default_key` did: a renderer, nothing else."""

    def display(self):
        return mark_safe(f'<em>{escape(self.text)}</em>')


class ADisplayOnlySubclassKeepsTheKeyItHad(SimpleTestCase):
    """The common case, and the one a patch release must not move.

    The lookup went through `display()`, so a subclass with its own renderer has always keyed its
    defaults on that renderer's output -- without knowing anything about keys. Giving the key its
    own method must not quietly re-key those: a custom `display()` is the subclass's own code and
    the escaping added here does not touch it, so it still answers for the key unless the subclass
    says otherwise.
    """

    def test_its_renderer_still_decides_the_key(self):
        item = MenuItem(url='#', link_type=MenuItem.HREF, menu_display=_RendererOnlyDisplay('Edit'))

        self.assertEqual('<em>Edit</em>', item.default_key)

    def test_and_a_default_keyed_that_way_still_applies(self):
        menu = HtmlMenu(button_defaults={'<em>Edit</em>': MenuItemDisplay('Resolved')}).add_items(
            MenuItem(url='#', link_type=MenuItem.HREF, menu_display=_RendererOnlyDisplay('Edit'))
        )

        self.assertEqual('Resolved', menu.menu_items[0].menu_display.text)

    def test_overriding_default_key_as_well_still_wins(self):
        """Opting in is for choosing a *different* key, and still does."""
        item = MenuItem(url='#', link_type=MenuItem.HREF, menu_display=_ShoutingDisplay('Edit'))

        self.assertEqual('shouted:Edit', item.default_key)

    def test_the_stock_display_is_not_dragged_through_its_renderer(self):
        """The base class keeps the reconstruction, which is what stops escaping moving the key."""
        item = MenuItem(url='#', link_type=MenuItem.HREF, menu_display=MenuItemDisplay('R&D'))

        self.assertEqual('R&D', item.default_key)
        self.assertEqual('R&amp;D', item.name)


class SafeTrueLetsALabelBeMarkup(SimpleTestCase):
    """``safe=True`` says a label is markup, without wrapping it in ``mark_safe`` first.

    Off by default, so a label is still text unless it says otherwise -- this is just the nicer
    way of saying so.
    """

    MARKUP = '<span class="btn-info">HTML</span>'

    def test_a_safe_label_is_not_escaped(self):
        self.assertEqual(self.MARKUP, MenuItemDisplay(self.MARKUP, safe=True).display())

    def test_a_safe_label_is_not_escaped_beside_an_icon_either(self):
        rendered = MenuItemDisplay(self.MARKUP, font_awesome='fa fa-plus', safe=True).display()

        self.assertEqual(f'<i class="fa fa-plus"></i> {self.MARKUP}', rendered)

    def test_the_icon_class_is_still_escaped_when_the_label_is_safe(self):
        """``safe`` is about the label. ``font_awesome`` goes in a class attribute, and stays text."""
        rendered = MenuItemDisplay('Add', font_awesome='fa" onmouseover="alert(1)', safe=True).display()

        self.assertNotIn('onmouseover="', rendered)

    def test_a_label_is_still_escaped_by_default(self):
        self.assertEqual('&lt;b&gt;Edit&lt;/b&gt;', MenuItemDisplay('<b>Edit</b>').display())

    def test_a_tooltip_is_still_escaped_when_the_label_is_safe(self):
        rendered = attributes_of(menu_display=MenuItemDisplay('Edit', tooltip='Bo"b', safe=True))

        self.assertIn('title="Bo&quot;b"', rendered)

    def test_a_menu_item_passes_it_to_the_display_it_builds(self):
        item = MenuItem(url='#', link_type=MenuItem.HREF, menu_display=self.MARKUP, safe=True)

        self.assertEqual(self.MARKUP, item.name)

    def test_the_tuple_shorthand_takes_it_in_its_options(self):
        menu = HtmlMenu(default_link_type=MenuItem.HREF).add_items(('#', self.MARKUP, {'safe': True}))

        self.assertEqual(self.MARKUP, menu.menu_items[0].name)

    def test_it_does_not_move_the_default_key(self):
        """Which default an item picks up does not depend on whether its label is markup."""
        plain = MenuItem(url='#', link_type=MenuItem.HREF, menu_display='R&D')
        safe = MenuItem(url='#', link_type=MenuItem.HREF, menu_display='R&D', safe=True)

        self.assertEqual(plain.default_key, safe.default_key)

    def test_a_display_passed_in_keeps_its_own_flag(self):
        """Like its ``font_awesome`` and ``css_classes``: the item's ``safe`` does not override it."""
        unsafe = MenuItem(url='#', link_type=MenuItem.HREF, menu_display=MenuItemDisplay(self.MARKUP), safe=True)
        safe = MenuItem(url='#', link_type=MenuItem.HREF, menu_display=MenuItemDisplay(self.MARKUP, safe=True))

        self.assertNotIn('<span', unsafe.name)
        self.assertEqual(self.MARKUP, safe.name)

    def test_a_subclass_that_skips_init_still_renders(self):
        class Bare(MenuItemDisplay):
            def __init__(self, text):
                self.text = text
                self.font_awesome = None

        self.assertEqual('&lt;b&gt;', Bare('<b>').display())
