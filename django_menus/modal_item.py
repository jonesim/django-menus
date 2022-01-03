from django_modals.helper import show_modal

from django_menus.menu import MenuItem


class ModalMenuItem(MenuItem):

    def __init__(self, modal_name, menu_display=None, modal_slug_args=None, **kwargs):
        if not modal_slug_args:
            modal_slug_args = []
        elif not isinstance(modal_slug_args, list):
            modal_slug_args = [modal_slug_args]
        super().__init__(show_modal(modal_name, *modal_slug_args),
                         menu_display,
                         link_type=MenuItem.JAVASCRIPT,
                         **kwargs)
