import json

from ajax_helpers.mixins import AjaxHelpers
from ajax_helpers.utils import random_string
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView, View

from django_menus.menu import MenuItem, BaseMenuItem


class HtmlMenu:

    key_press_template = 'django_menus/menu_key_press.html'

    templates = {
        'base': 'django_menus/main_menu.html',
        'tabs': 'django_menus/tab_menu.html',
        'button_group': 'django_menus/button_group.html',
        'breadcrumb': 'django_menus/breadcrumb.html',
        'dropdown': 'django_menus/dropdown.html',
        'buttons': 'django_menus/button_menu.html',
        'context': 'django_menus/context_menu.html',
    }

    def __init__(self, request=None, template='base', menu_id=None, default_link_type=MenuItem.URL_NAME,
                 placement=None, no_hover=False, button_defaults=None, alignment=None, compare_full_path=False):
        self.menu_items = []
        self.button_defaults = getattr(settings, 'DJANGO_MENUS_BUTTON_DEFAULTS', {})
        if button_defaults is not None:
            self.button_defaults.update(button_defaults)

        self.template = self.templates.get(template, template)
        self.request = request
        self.active = None
        self.no_hover = no_hover
        self.placement = placement
        self.alignment = alignment
        self.fixed_id = menu_id
        self.id = None
        self.compare_full_path = compare_full_path
        self.default_link_type = default_link_type

    def visible_items(self):
        return [i for i in self.menu_items if i.visible]

    def add_item(self, url_name=None, text=None,  link_type=None, **kwargs):
        link_type = link_type if link_type is not None else self.default_link_type
        self.menu_items.append(MenuItem(url=url_name, menu_display=text, menu=self, link_type=link_type, **kwargs))

    def add_items(self, *args):
        for a in args:
            if isinstance(a, BaseMenuItem):
                a.menu = self
                self.menu_items.append(a)
            elif isinstance(a, View):
                self.add_item(a.request.path, getattr(a, 'menu_display', None), MenuItem.HREF)
            elif type(a) == tuple:
                if type(a[-1]) == dict:
                    self.add_item(*a[:-1], **a[-1])
                else:
                    self.add_item(*a)
            else:
                self.add_item(a)
        return self

    def badge_ajax(self):
        return [{'function': 'html', 'selector': '#' + i.badge.id, 'html': i.badge.badge_html()}
                for i in self.menu_items if i.has_badge]

    def render(self):
        if self.fixed_id:
            self.id = self.fixed_id
        else:
            self.id = random_string()
        extra_menus = ''
        key_dict = {}
        no_items = True
        for i in self.menu_items:
            if not i.test_visible(self.request):
                continue
            if hasattr(i, 'dropdown') and i.dropdown:
                # noinspection PyUnresolvedReferences
                i.dropdown.request = self.request
                extra_menu = i.dropdown.render()
                if not extra_menu:
                    i.visible = False
                extra_menus += extra_menu
            if getattr(i, 'key', None):
                key_list = [i.key] if isinstance(i.key, str) else i.key
                for key in key_list:
                    key_data = {'shift': False, 'alt': False, 'href': i.href()}
                    for k in key.split('-'):
                        if k.lower() == 'shift':
                            key_data['shift'] = True
                        elif k.lower() == 'alt':
                            key_data['alt'] = True
                        else:
                            key_data['key'] = k
                    key_dict[key_data['key']] = key_data
            no_items = False
        if no_items:
            return ''
        keyboard = render_to_string(self.key_press_template,
                                    context={'key_dict': json.dumps(key_dict)}) if key_dict else ''
        return mark_safe(render_to_string(self.template, context={'menu': self}) + extra_menus + keyboard)


class MenuMixin:

    def add_menu(self, menu_name, menu_type=None, **kwargs):
        request = getattr(self, 'request', None)
        if menu_type:
            self.menus[menu_name] = HtmlMenu(request, menu_type, **kwargs)
        else:
            self.menus[menu_name] = HtmlMenu(request, **kwargs)
        return self.menus[menu_name]

    def get_context_data(self, **kwargs):
        self.setup_menu()
        super_context = getattr(super(), 'get_context_data')
        if super_context and callable(super_context):
            context = super_context(**kwargs)
        else:
            context = {}
        context['menus'] = self.menus
        return context

    def setup_menu(self):
        return

    def add_ajax_dropdown_menu(self, *args,  pos, template='context'):
        menu = HtmlMenu(self.request, template=template).add_items(*args)
        return self.command_response('context_menu', menu=menu.render(), pos=pos)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.menus = {}


class MenuTemplateView(MenuMixin, TemplateView):
    pass


class AjaxMenuTemplateView(AjaxHelpers, MenuTemplateView):

    def timer_menu(self, **_kwargs):
        self.setup_menu()
        for m in self.menus.values():
            self.response_commands += m.badge_ajax()
        return self.command_response()
