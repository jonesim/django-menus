import json
from collections import namedtuple

from ajax_helpers.utils import ajax_command, is_ajax
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from django_menus.menu import AjaxMenuTemplateView


class AjaxMenuTabs(AjaxMenuTemplateView):

    TEMPLATE_CONTENT = 0
    MENU_CONTENT = 1
    AjaxCommand = namedtuple('AjaxCommand', ['name', 'type'])

    _ajax_commands = [
        AjaxCommand('tab_template', TEMPLATE_CONTENT),
        AjaxCommand('tab_menu', MENU_CONTENT),
    ]

    additional_content = []

    def create_ajax_commands(self, context):
        self.add_command('clear_timers', store='tab')
        for c in self.ajax_response_commands:
            if c.type == self.TEMPLATE_CONTENT:
                html = context[c.name]
            else:
                html = self.menus[c.name].render()
            self.add_command('html', selector='#' + c.name, html=html)

    def __init__(self, *args, **kwargs):
        self.ajax_response_commands = None
        super().__init__(*args, **kwargs)

    def set_response_commands(self):
        if not self.ajax_response_commands:
            self.ajax_response_commands = self._ajax_commands + [self.AjaxCommand(*a) for a in self.additional_content]

    def tab_response(self):
        self.set_response_commands()
        context = self.get_context_data(**self.kwargs)
        self.create_ajax_commands(context)
        response = self.command_response()
        response['Cache-Control'] = 'No-Cache,No-Store'
        return response

    def get(self, request, *args, **kwargs):
        self.set_response_commands()
        if is_ajax(request):
            return self.tab_response()
        return super().get(request, *args, **kwargs)

    def main_context(self, **kwargs):
        return {}

    def get_tab_commands(self):
        pass

    def tab_context(self, **kwargs):
        tab_commands = self.get_tab_commands()
        context = {}
        if tab_commands:
            command = ajax_command('onload', commands=tab_commands)
            context['tabs_script'] = mark_safe(
                f'<script>ajax_helpers.process_commands([{json.dumps(command)}])</script>'
            )
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not is_ajax(self.request):
            context.update(self.main_context())
        context.update(self.tab_context())
        for c in self.ajax_response_commands:
            if c.type == self.TEMPLATE_CONTENT:
                context[c.name] = mark_safe(render_to_string(getattr(self, c.name), context=context))
        return context
