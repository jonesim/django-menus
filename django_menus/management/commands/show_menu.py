"""Print the resolved menu so ordering and visibility are inspectable without running the site."""
import json
from importlib import import_module

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.management.base import BaseCommand, CommandError
from django.test import RequestFactory
from django.urls import NoReverseMatch, Resolver404, resolve, reverse

from django_menus.menu import DividerItem, HeaderItem, MenuItem
from django_menus.menu import registry

GLYPHS = {
    'ascii': {'branch': '+-- ', 'last': '`-- ', 'pipe': '|   ', 'gap': '    ', 'rule': '-' * 15},
    'unicode': {'branch': '├── ', 'last': '└── ', 'pipe': '│   ', 'gap': '    ', 'rule': '─' * 15},
}

LINK_TYPES = {
    MenuItem.HREF: 'href',
    MenuItem.AJAX_GET_URL_NAME: 'ajax_get',
    MenuItem.URL_NAME: 'url',
    MenuItem.AJAX_BUTTON: 'ajax_button',
    MenuItem.JAVASCRIPT: 'javascript',
    MenuItem.AJAX_COMMAND: 'ajax_command',
}


def item_url_name(item):
    resolved = getattr(item, 'resolved_url', None)
    if resolved is not None and resolved != 'invalid':
        if resolved.namespace:
            return f'{resolved.namespace}:{resolved.url_name}'
        return resolved.url_name
    name = getattr(item, 'permission_name', None)
    link_type = LINK_TYPES.get(getattr(item, 'link_type', None), '?')
    return f'{link_type}:{name}' if name else link_type


def describe(item):
    if isinstance(item, DividerItem):
        return {'type': 'divider'}
    if isinstance(item, HeaderItem):
        return {'type': 'header', 'label': item.text}
    display = getattr(item, 'menu_display', None)
    if display is None:
        return {'type': 'html', 'label': str(getattr(item, 'html', ''))[:60]}
    if getattr(item, 'permission_name', None) is None:
        # A dropdown parent with no link of its own.
        return {'type': 'item', 'label': display.text or '', 'name': None, 'href': None}
    return {
        'type': 'item',
        'label': display.text or '',
        'name': item_url_name(item),
        'href': str(item.href()),
    }


class Command(BaseCommand):
    help = ('Print the menu registry, or the menus a view actually builds. '
            'With no arguments, prints every section in DJANGO_MENUS_SECTIONS.')

    def add_arguments(self, parser):
        parser.add_argument('sections', nargs='*',
                            help='Registry sections to print (default: all configured).')
        parser.add_argument('--view', help='Url name of a view whose menus should be built, with '
                                           'any url arguments after commas.')
        parser.add_argument('--path', help='Url path of a view whose menus should be built.')
        parser.add_argument('--menu', help='Only show this menu from the view.')
        parser.add_argument('--user', help='Build the request as this user (default: anonymous).')
        parser.add_argument('--show-hidden', action='store_true',
                            help='Include items hidden by permissions.')
        parser.add_argument('--format', choices=('tree', 'flat', 'json'), default='tree')
        parser.add_argument('--unicode', action='store_true',
                            help='Draw the tree with box characters instead of ASCII.')

    def handle(self, *args, **options):
        self.glyphs = GLYPHS['unicode' if options['unicode'] else 'ascii']
        self.show_hidden = options['show_hidden']

        path = self.target_path(options)
        request = self.build_request(path or '/', options['user'])

        if path:
            data = self.view_menus(path, request, options['menu'])
        else:
            data = self.registry_sections(options['sections'], request)

        if options['format'] == 'json':
            self.stdout.write(json.dumps(data, indent=2))
        elif path:
            self.write_menus(data, options['format'])
        else:
            self.write_sections(data, options['format'])

    # ------------------------------------------------------------------------------- the request

    def target_path(self, options):
        if options['path']:
            return options['path']
        if not options['view']:
            return None
        name, *url_args = options['view'].split(',')
        try:
            return reverse(name, args=url_args)
        except NoReverseMatch as error:
            raise CommandError(str(error))

    def build_request(self, path, username):
        request = RequestFactory().get(path)
        if username:
            model = get_user_model()
            try:
                request.user = model.objects.get(**{model.USERNAME_FIELD: username})
            except model.DoesNotExist:
                raise CommandError(f'No user named {username!r}.')
        else:
            request.user = AnonymousUser()
        try:
            # RequestFactory does not set this, and MenuItem.test_visible reads it.
            request.resolver_match = resolve(path)
        except Resolver404:
            request.resolver_match = None
        if apps.is_installed('django.contrib.sessions'):
            request.session = import_module(settings.SESSION_ENGINE).SessionStore()
        if apps.is_installed('django.contrib.messages'):
            from django.contrib.messages.storage.fallback import FallbackStorage
            request._messages = FallbackStorage(request)
        return request

    # ---------------------------------------------------------------------------------- view mode

    def view_menus(self, path, request, only):
        try:
            match = resolve(path)
        except Resolver404:
            raise CommandError(f'{path} does not resolve.')
        view_class = getattr(match.func, 'view_class', None)
        if view_class is None:
            raise CommandError(f'{path} is not a class based view.')
        if not hasattr(view_class, 'setup_menu'):
            raise CommandError(f'{view_class.__name__} does not use MenuMixin.')

        view = view_class()
        view.setup(request, *match.args, **match.kwargs)
        view.setup_menu()

        menus = []
        for name, menu in view.menus.items():
            if only and name != only:
                continue
            menu.request = request
            menus.append({'menu': name, 'template': menu.template,
                          'items': self.walk(menu, request)})
        if only and not menus:
            raise CommandError(f'{view_class.__name__} has no menu named {only!r}.')
        return {'path': path, 'view': f'{view_class.__module__}.{view_class.__name__}',
                'user': str(request.user), 'menus': menus}

    def walk(self, menu, request):
        nodes = []
        for item in menu.menu_items:
            visible = bool(item.test_visible(request))
            if not visible and not self.show_hidden:
                continue
            node = describe(item)
            node['visible'] = visible
            dropdown = getattr(item, 'dropdown', None)
            if dropdown is not None:
                dropdown.request = request
                node['items'] = self.walk(dropdown, request)
            nodes.append(node)
        return nodes

    # ------------------------------------------------------------------------------ registry mode

    def registry_sections(self, names, request):
        configured = registry.sections()
        for name in names:
            if name not in configured:
                raise CommandError(f'Unknown section {name!r}. Configured: '
                                   f'{", ".join(configured) or "none"}.')
        sections = []
        for name in names or configured:
            config = registry.section_config(name)
            group_names = registry.section_groups(config)[0]
            items = []
            # --show-hidden has to suppress the registry's own filtering, otherwise the items it
            # is meant to reveal never reach the command.
            for item in registry.dropdown(name, request, filter_visible=not self.show_hidden):
                node = describe(item)
                node['visible'] = bool(item.test_visible(request))
                items.append(node)
            sections.append({
                'section': name,
                'sort': config.get('sort', registry.ALPHA),
                'groups': group_names,
                'items': items,
                'specs': [{'url_name': spec.url_name, 'group': spec.group,
                           'order': spec.entry.order, 'view': spec.view_path}
                          for spec in registry.specs(name)],
            })
        return {'user': str(request.user), 'sections': sections}

    # ------------------------------------------------------------------------------------ output

    def write_menus(self, data, style):
        self.stdout.write(f"{data['view']}  {data['path']}  (as {data['user']})")
        for menu in data['menus']:
            self.stdout.write('')
            self.stdout.write(self.style.MIGRATE_HEADING(f"{menu['menu']}  ({menu['template']})"))
            if style == 'flat':
                self.write_flat(menu['items'])
            else:
                self.write_tree(menu['items'])

    def write_tree(self, nodes, prefix=''):
        for index, node in enumerate(nodes):
            last = index == len(nodes) - 1
            self.stdout.write(prefix + self.glyphs['last' if last else 'branch'] + self.label(node))
            if node.get('items'):
                self.write_tree(node['items'],
                                prefix + self.glyphs['gap' if last else 'pipe'])

    def write_flat(self, nodes, depth=0):
        for node in nodes:
            self.stdout.write('  ' * depth + self.label(node))
            self.write_flat(node.get('items') or (), depth + 1)

    def label(self, node):
        if node['type'] == 'divider':
            return self.glyphs['rule']
        if node['type'] == 'header':
            return f"# {node['label']}"
        if node['type'] == 'html':
            return f"html: {node['label']}"
        text = node['label']
        if node.get('name'):
            text = f"{text:<28} [{node['name']}]"
            if node.get('href'):
                text = f"{text:<62} {node['href']}"
        if node.get('items') is not None:
            text += f"  ({len(node['items'])} items)"
        if not node.get('visible', True):
            return self.style.WARNING(f'{text}  (hidden)')
        return text

    def write_sections(self, data, style):
        self.stdout.write(f"registry (as {data['user']})")
        for section in data['sections']:
            self.stdout.write('')
            heading = f"section '{section['section']}'  sort={section['sort']}"
            if section['groups']:
                heading += f"  groups={', '.join(section['groups'])}"
            self.stdout.write(self.style.MIGRATE_HEADING(heading))
            if not section['items']:
                self.stdout.write('  (nothing visible)')
            elif style == 'flat':
                self.write_flat(section['items'], depth=1)
            else:
                self.write_tree(section['items'], prefix='  ')
            self.stdout.write(f"  registered ({len(section['specs'])}):")
            for spec in section['specs']:
                group = f" group={spec['group']}" if spec['group'] else ''
                order = f" order={spec['order']}" if spec['order'] is not None else ''
                self.stdout.write(f"    {spec['url_name']}{group}{order}  {spec['view']}")
