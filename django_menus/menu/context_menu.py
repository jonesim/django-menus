from django_menus.menu import HtmlMenu


# noinspection PyUnresolvedReferences
class ContextMenuMixin:
    context_menu_selector = '.context_menu'

    def get_context_data(self, **kwargs):
        self.add_page_command('enable_context_menu', selector=self.context_menu_selector)
        return super().get_context_data(**kwargs)

    def add_context_menu(self, *args, template='context'):
        menu = HtmlMenu(self.request, template=template).add_items(*args)
        return self.command_response('context_menu', menu=menu.render())
